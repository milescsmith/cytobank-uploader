from datetime import datetime
import json
from pathlib import Path
from pprint import pprint
from sys import stderr
from typing import Optional

import requests
import typer
from loguru import logger
from rich.console import Console
from rich.traceback import install

from . import __version__
from .experiments import Experiment
from .interface import (
    _get_auth_token,
    _list_experiment_fcs_files,
    _upload_files,
    get_upload_token,
)

install(show_locals=True)

logger.remove()

console = Console()


def version_callback(value: bool) -> None:
    """Prints the version of the package."""
    if value:
        console.print(
            f"[yellow]{__name__.split('.')[0]}[/] version: [bold blue]{__version__}[/]"
        )
        raise typer.Exit()


app = typer.Typer(
    name="cytobank_uploader",
    help=("Utility to upload FCS files to Cytobank"),
    add_completion=False,
    rich_markup_mode="markdown",
)


def unpack(iterable):
    logger.debug(f"{iterable=}")
    for i in iterable:
        logger.debug(f"{i=}")
        if "__iter__" in dir(i):
            for j in i:
                logger.debug(f"{j=}")
                yield j
        else:
            yield i


@app.command(no_args_is_help=True)
def get_auth_token(
    username: Optional[str] = typer.Option(
        None,
        "-u",
        "--username",
        help="Cytobank username. You will need to provide this if the existing token is invalid",
    ),
    password: Optional[str] = typer.Option(
        None,
        "-p",
        "--password",
        help="Account password. You will need to provide this if the existing token is invalid",
    ),
    base_url: Optional[str] = typer.Option(
        None,
        "-b",
        "--baseurl",
        help="Change the API base url if necessary for some reason.",
    ),
    auth_endpoint: Optional[str] = typer.Option(
        None,
        "-e",
        "--endpoint",
        help="Change the default authorization endpoint, if necessary for some reason",
    ),
    cytobank_domain: str = typer.Option(
        "premium",
        "-d",
        "--domain",
        help="Change the Cytobank domain. Required if you are using Cytobank Enterprise.",
    ),
    verbose: bool = typer.Option(False, "-v", "--verbose"),
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback
    ),
) -> str:
    """Get an authorization token from Cytobank. Required for all operations.
    While the token will be stored to a configuration file, the tokens are only valid for 8 hrs.

    ---

    *Parameters*

    * **username** : Optional[str], optional
        Account username. You will need to provide this if the existing token is invalid

    * **password** : Optional[str], optional
        Account password. You will need to provide this if the existing token is invalid

    * **base_url** : Optional[str], optional
        Change the API base url if necessary for some reason.

    * **auth_endpoint** : Optional[str], optional
        Change the default authorization endpoint, if necessary for some reason

    * **cytobank_domain** : str, optional
        Change the Cytobank domain. Required if you are using Cytobank Enterprise

    ---

    *Returns*

    * **auth_token** : str
        An authorization token required for most API functions

    """

    token = _get_auth_token(
        username=username,
        password=password,
        base_url=base_url,
        auth_endpoint=auth_endpoint,
        cytobank_domain=cytobank_domain,
    )
    return token


@app.command(no_args_is_help=False)
def list_experiments(
    auth_token: Optional[str] = typer.Option(
        None, "-t", "--token", help="Manually provide the authorization token"
    ),
    cytobank_domain: str = typer.Option(
        "premium",
        "-d",
        "--domain",
        help="Change the Cytobank domain. Required if you are using Cytobank Enterprise.",
    ),
    print_list: bool = typer.Option(
        True, "-p", "--print", help="print the last of experiments to the console"
    ),
    verbose: bool = typer.Option(False, "-v", "--verbose"),
) -> list[Experiment]:
    """List the experiments associated with the account.  Will print in the form
    of `experimentName`: `experimentId`

    ---

    *Parameters*

    * **auth_token** : Optional[str], optional
        Manually provide the authorization token

    * **cytobank_domain** : str, optional
        Change the Cytobank domain. Required if you are using Cytobank Enterprise

    ---

    *Returns*

    * **experiment_list** : list[Experiment]
        A list of the current experiments, in the form of **experimentTitle**: **experimentId**

    """
    logger.add(
        f"{__name__}_{datetime.now().strftime('%d-%m-%Y--%H-%M-%S')}.log", level="DEBUG"
    )

    if verbose:
        logger.add(stderr, level="DEBUG")
    else:
        logger.add(stderr, level="ERROR")

    if auth_token is None:
        auth_token = get_auth_token()

    payload = {}
    headers = {"Authorization": f"Bearer {auth_token}"}

    response = requests.get(
        url=f"https://{cytobank_domain}.cytobank.org/cytobank/api/v1/experiments",
        headers=headers,
        data=payload,
    )

    if response.status_code == 200:
        experiments_list = [
            Experiment.from_dict(_) for _ in json.loads(response.text)["experiments"]
        ]
    else:
        raise requests.HTTPError(f"HTTP error with code {response.status_code}")

    if print_list:
        for _ in experiments_list:
            pprint(_)

    return experiments_list


@app.command(no_args_is_help=True)
def upload_files(
    files: list[Path] = typer.Option(..., "-f", "--files"),
    username: str = typer.Option(..., "-u", "--username"),
    exp_id: int = typer.Option(..., "-i", "--id"),
    cytobank_domain: str = typer.Option(
        "premium",
        "-d",
        "--domain",
        help="Change the Cytobank domain. Required if you are using Cytobank Enterprise.",
    ),
    auth_token: Optional[str] = typer.Option(None, "-t", "--token"),
    verbose: bool = typer.Option(False, "-v", "--verbose"),
) -> None:
    """Upload one or more FCS files to a Cytobank project

    ---

    *Parameters*

    * **files** : list[Path], optional
        _description_, by default typer.Option(..., "-f", "--files")

    * **username** : str, optional
        _description_, by default typer.Option(..., "-u", "--username")

    * **exp_id** : int, optional
        _description_, by default typer.Option(..., "-i", "--id")

    * **cytobank_domain** : str, optional
        _description_, by default typer.Option("premium", "-d", "--domain")

    * **auth_token** : Optional[str], optional
        _description_, by default typer.Option(None, "-t", "--token")
    """
    if verbose:
        logger.add(stderr, level="DEBUG")
    else:
        logger.add(stderr, level="ERROR")

    if auth_token is None:
        auth_token = get_auth_token()

    upload_token = get_upload_token(username, exp_id, cytobank_domain, auth_token)
    logger.debug(upload_token)

    if not isinstance(files, list):
        files = [files]
    for _ in files:
        if _.is_dir():
            logger.debug(f"{_} is a dir")
        elif _.is_file():
            logger.debug(f"{_} is a file")
        else:
            logger.debug(f"I don't know what {_} is")

    filelist = unpack([list(_.glob("*.fcs")) if _.is_dir() else _ for _ in files])

    _upload_files(
        files=filelist,
        username=username,
        exp_id=exp_id,
        cytobank_domain=cytobank_domain,
        auth_token=auth_token,
    )


@app.command(no_args_is_help=True)
def show_experiment_files(
    expid: int = typer.Argument(
        ...,
        help="Id for the experiment in question. Can be found using list_experiments()",
    ),
    cytobank_domain: str = typer.Option(
        "premium",
        "-d",
        "--domain",
        help="Change the Cytobank domain. Required if you are using Cytobank Enterprise.",
    ),
    auth_token: Optional[str] = typer.Option(
        None, "-t", "--token", help="Manually provide the authorization token"
    ),
    verbose: bool = typer.Option(False, "-v", "--verbose"),
) -> None:
    """Prints a list the FCS files associated with the given experiment

    ---

    *Parameters*

    * **expid** : int, optional
        Id for the experiment in question. Can be found using `list_experiments()`

    * **cytobank_domain** : str, optional
        Change the Cytobank domain. Required if you are using Cytobank Enterprise.

    * **auth_token** : Optional[str], optional
        Manually provide the authorization token

    * **verbose** : bool, optional
    """

    if verbose:
        logger.add(stderr, level="DEBUG")
    else:
        logger.add(stderr, level="ERROR")

    if auth_token is None:
        auth_token = get_auth_token()

    fcs_files = _list_experiment_fcs_files(
        experimentId=expid, cytobank_domain=cytobank_domain, auth_token=auth_token
    )

    print("\n".join(fcs_files))
