import json
from datetime import datetime, timedelta
from pathlib import Path
from sys import stderr
from typing import List, Optional, Union
from warnings import warn

import requests
from boto3 import client
from loguru import logger
from tqdm.auto import tqdm

from .experiments import Experiment


class InvalidTokenError(Exception):
    def __init__(self, token: Optional[str] = None, message: Optional[str] = None):
        self.token = token
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        if self.token is not None:
            return f"Authorization token is invalid! Token passed was {self.token}"
        else:
            return "No valid authorization token!"


def test_token(token: str, domain: str = "premium", verbose: bool = False) -> bool:
    """Check to see if an authorization key is valid"""

    if verbose:
        logger.add(stderr, level="DEBUG")
    else:
        logger.add(stderr, level="ERROR")

    url = f"https://{domain}.cytobank.org/cytobank/api/v1/users"

    payload = {}
    files = {}
    headers = {"Authorization": f"Bearer {token}"}

    response = json.loads(
        requests.get(url, headers=headers, data=payload, files=files).text
    )

    # so, little weird but I cannot find any other calls one can make, other than retreiving
    # the list of experiments that will work without any other information, and that call
    # is slow; asking for the list or users only works with *admin* users, but if the token
    # is invalid, it returns a different error than if it was valid.
    logger.debug(response["errors"][0])
    if response["errors"][0] == "Not Authorized To Access Resource":
        return True
    elif response["errors"][0] == "Not Authenticated -- invalid or missing auth token":
        return False
    else:
        return False


def load_stored_auth_token(
    config_file: Optional[Path] = None, verbose: bool = False
) -> Union[str, bool]:
    """Loads the authorization token from file and test its validity

    Returns
    -------
    str | bool
        Returns the authorization token if present and valid, else False.
    """

    if verbose:
        logger.add(stderr, level="DEBUG")
    else:
        logger.add(stderr, level="ERROR")

    if config_file is None:
        config_file = Path.home() / ".cytobankenvs"
        logger.debug(config_file.exists())

    if config_file.exists():
        config = {
            k.split("=")[0]: k.split("=")[1]
            for k in config_file.read_text().split("\n")
        }

        if "API_TOKEN" in config:
            logger.debug(f"{config['API_TOKEN']}")
            if "RETRIEVE_TIME" in config:
                logger.debug(f"{config['RETRIEVE_TIME']}")
                try:
                    if (
                        datetime.now() - datetime.fromisoformat(config["RETRIEVE_TIME"])
                    ) < timedelta(hours=8):
                        if test_token(config["API_TOKEN"]):
                            logger.debug("stored token is valid")
                            return config["API_TOKEN"]
                        else:
                            return False
                    else:
                        return False
                except ValueError:
                    print(
                        "The value for the token retrieval time is unable to be parsed, assuming it needs to requested again"
                    )
                    return False
        else:
            print("No stored authorization token was found")
            return False

    else:
        print(f"a valid configuration file at {config_file} was not found.")
        return False


def set_auth_token(
    auth_token: str, config_file: Optional[Path] = None, verbose: bool = False
) -> None:
    """Save the authorization token to a file in the user's home directory

    Parameters
    ----------
    auth_token : str
        Authorization token from `get_auth_token()`
    config_file : Path
        Path to config file in which to store the token.  Defaults to .cytobankenvs in the user's home directory.
    """
    if verbose:
        logger.add(stderr, level="DEBUG")
    else:
        logger.add(stderr, level="ERROR")

    if config_file is None:
        config_file = Path.home() / ".cytobankenvs"

    logger.debug(f"storing token in {config_file.resolve()}")

    if not config_file.exists():
        config_file.touch()
    config_file.write_text(f"API_TOKEN={auth_token}\nRETRIEVE_TIME={datetime.now()}")


def _get_auth_token(
    username: Optional[str] = None,
    password: Optional[str] = None,
    base_url: Optional[str] = None,
    auth_endpoint: Optional[str] = None,
    cytobank_domain: str = "premium",
    config_file: Optional[Path] = None,
    verbose: bool = False,
) -> str:
    """Get an authorization token from Cytobank. Required for all operations. Looks for a stored token, and it valid
    returns it, otherwise generates a new one.

    While the token will be stored in a configuration file, the tokens are only valid for 8 hrs.

    Parameters
    ----------
    username : str, optional
        Cytobank username. You will need to provide this if the existing token is invalid
    password : str, optional
        Account password. You will need to provide this if the existing token is invalid
    base_url : str, optional
        Change the API base url if necessary for some reason
    auth_endpoint : str, optional
        Change the default authorization endpoint, if necessary for some reason
    cytobank_domain : str, optional
        Change the Cytobank domain. Required if you are using Cytobank Enterprise.
    config_file: Path, optional
        Path to a config file that is (temporarily) storing the API authorization token.  By default, this is
        stored as '.cytobankenvs' in the current user's home directory

    Returns
    -------
    str
        Loads the stored authorization token if it is found and valid, else generates a new one
    """
    if verbose:
        logger.add(stderr, level="DEBUG")
    else:
        logger.add(stderr, level="ERROR")

    if auth_token := load_stored_auth_token(config_file):
        logger.debug("stored token was valid")
        return auth_token
    else:
        if (username is None) or (password is None):
            warn(
                "A valid authorization token was not found. Please provide the username and password and generate a new one."
            )
            raise InvalidTokenError()
        logger.debug("stored token is invalid, generating new one")
        if base_url is None:
            base_url = f"https://{cytobank_domain}.cytobank.org/cytobank/api/v1"
        if auth_endpoint is None:
            auth_endpoint = f"{base_url}/authenticate"
        logger.debug(f"{auth_endpoint=}")

        payload = {"username": username, "password": password}

        response = requests.post(
            url=auth_endpoint,
            data=payload,
        )

        logger.debug(f"{response.status_code=}")

        if response.status_code == 200:
            response_parsed = json.loads(response.text)
            auth_token: str = response_parsed["user"]["authToken"]
            logger.debug(f"{auth_token=}")
            set_auth_token(auth_token)

            return auth_token
        else:
            raise requests.HTTPError(f"HTTP error with code {response.status_code}")


def get_experiment_id(title: str, exp_list: list[Experiment]) -> Union[int, None]:
    """Given a list of Experiment objects, return the id for the
    Experiment with the matching title

    Parameters
    ----------
    title : str
        _description_
    exp_list : list[Experiment]
        _description_

    Returns
    -------
    int
        _description_
    """

    ident = [_ for _ in exp_list if _.experimentName == title]

    if len(ident) != 1:
        warn(f"More than one experiment was found titled {title}!")
        for _ in ident:
            print(f"{_.experimentName}: {_.experimentId}")
    else:
        return ident[0].id


def get_upload_token(
    username: str,
    exp_id: int,
    cytobank_domain: str = "premium",
    auth_token: Optional[str] = None,
    verbose: bool = False,
) -> dict[str, Union[str, int, bool, float]]:
    """Use the experimentId and auth token to retreive parameters to upload to
    an AWS s3 bucket

    Parameters
    ----------
    username : str
        cytobank username (not email address used to login)
    exp_id : int
        The experiment ID.  Should be a string of numbers and can be retrieved using `get_experiment_id`
    cytobank_domain : str, optional
        The domain from "{domain}.cytobank.org" used to login.  Only needed if you are a Cytobank Enterprise customer
        and use a custom domain.  Defaults to "premium"
    auth_token : Optional[str], optional
        Cytobank API authorization token. If you generated a token on Cytobank's site, it can be supplied here,
        otherwise run `get_auth_token()` if it hasn't already been run. By default `None`

    Returns
    -------
    dict[str, Union[str, int, bool, float]]
        _description_

    Raises
    ------
    requests.HTTPError
        _description_
    """

    if verbose:
        logger.add(stderr, level="DEBUG")
    else:
        logger.add(stderr, level="ERROR")

    if auth_token is None:
        auth_token = _get_auth_token()
    elif not test_token(auth_token):
        raise InvalidTokenError(auth_token)

    logger.debug("auth_token")

    headers = {"Authorization": f"Bearer {auth_token}"}

    upload_token_endpoint = f"https://{cytobank_domain}-api.cytobank.org/api/v1/upload/token?userId={username}&experimentId={exp_id}&acs=false"
    logger.debug(f"{upload_token_endpoint=}")
    upload_token_response = requests.get(url=upload_token_endpoint, headers=headers)

    if upload_token_response.status_code == 200:
        utr_parsed = json.loads(upload_token_response.text)
        logger.debug(f"{utr_parsed['accessKeyId']=}")
    else:
        raise requests.HTTPError(
            f"HTTP error with code {upload_token_response.status_code}"
        )

    return utr_parsed


def _upload_files(
    files: list[Path],
    username: str,
    exp_id: int,
    cytobank_domain: str,
    auth_token: Optional[str],
    verbose: bool,
) -> None:
    """Upload one or more FCS files to a Cytobank project

    Parameters
    ----------
    files : list[Path], optional
        _description_, by default typer.Option(..., "-f", "--files")
    username : str, optional
        _description_, by default typer.Option(..., "-u", "--username")
    exp_id : int, optional
        _description_, by default typer.Option(..., "-i", "--id")
    cytobank_domain : str, optional
        _description_, by default typer.Option("premium", "-d", "--domain")
    auth_token : Optional[str], optional
        _description_, by default typer.Option(None, "-t", "--token")
    """
    if verbose:
        logger.add(stderr, level="DEBUG")
    else:
        logger.add(stderr, level="ERROR")

    if auth_token is None:
        auth_token = _get_auth_token()
    elif not test_token(auth_token):
        raise InvalidTokenError(auth_token)

    upload_token = get_upload_token(username, exp_id, cytobank_domain, auth_token)
    logger.debug(upload_token)

    s3_client = client(
        "s3",
        aws_access_key_id=upload_token["accessKeyId"],
        aws_secret_access_key=upload_token["secretAccessKey"],
        aws_session_token=upload_token["sessionToken"],
    )

    for file in files:
        if file.exists():
            with tqdm(
                total=file.stat().st_size,
                desc=f"uploading {file.name} to s3://{upload_token['uploadBucketName']}",
                bar_format="{percentage:.1f}%|{bar:25} | {rate_fmt} | {desc}",
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:

                s3_client.upload_file(
                    Filename=str(file.resolve()),
                    Bucket=upload_token["uploadBucketName"],
                    Key=f"experiments/{upload_token['experimentId']}/{file.name}",
                    Callback=pbar.update,
                )

        else:
            raise FileNotFoundError(f"{file.resolve} was not found")


def _list_experiment_fcs_files(
    experimentId: int,
    cytobank_domain: str = "premium",
    auth_token: Optional[str] = None,
) -> List[str]:

    if auth_token is None:
        auth_token = _get_auth_token()
    elif not test_token(auth_token):
        raise InvalidTokenError(auth_token)

    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {}

    base_url = f"https://{cytobank_domain}.cytobank.org/cytobank/api/v1"
    fcsfiles_endpoint = f"experiments/{experimentId}/fcs_files"

    fcs_file_response = requests.get(
        url=f"{base_url}/{fcsfiles_endpoint}",
        headers=headers,
        data=payload,
    )

    if fcs_file_response.status_code == 200:
        fcs_files_info = json.loads(fcs_file_response.text)
        fcs_files = [_["filename"] for _ in fcs_files_info["fcsFiles"]]
    else:
        raise requests.HTTPError(
            f"HTTP error with code {fcs_file_response.status_code}"
        )

    return fcs_files
