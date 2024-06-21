from pathlib import Path
from sys import stderr
from typing import Annotated, Optional

import typer
from loguru import logger
from rich.console import Console
from rich.traceback import install

from cytobank_uploader import __version__
from cytobank_uploader.experiments import Experiment
from cytobank_uploader.interface import (
    _get_auth_token,
    _list_experiment_fcs_files,
    _list_experiments,
    _upload_files,
    get_upload_token,
)

install(show_locals=True)

logger.remove()

console = Console()


def version_callback(value: bool) -> None:
    """Prints the version of the package."""
    if value:
        console.print(f"[yellow]cellranger_scripts[/] version: [bold blue]{__version__}[/]")
        raise typer.Exit()


app = typer.Typer(
    name="cytobank_uploader",
    help=("Utility to upload FCS files to Cytobank"),
    add_completion=False,
    rich_markup_mode="markdown",
)


@app.command(no_args_is_help=True)
def get_auth_token(
    username: Annotated[
        str,
        typer.Option(
            None,
            "-u",
            "--username",
            help="Cytobank username. You will need to provide this if the existing token is invalid",
        ),
    ],
    password: Annotated[
        str,
        typer.Option(
            None,
            "-p",
            "--password",
            help="Account password. You will need to provide this if the existing token is invalid",
        ),
    ],
    base_url: Annotated[
        str,
        typer.Option(
            None,
            "-b",
            "--baseurl",
            help="Change the API base url if necessary for some reason.",
        ),
    ],
    auth_endpoint: Annotated[
        str,
        typer.Option(
            None,
            "-e",
            "--endpoint",
            help="Change the default authorization endpoint, if necessary for some reason",
        ),
    ],
    cytobank_domain: Annotated[
        str,
        typer.Option(
            "premium",
            "-d",
            "--domain",
            help="Change the Cytobank domain. Required if you are using Cytobank Enterprise.",
        ),
    ],
    verbose: Annotated[
        bool,
        typer.Option("-v", "--verbose"),
    ] = False,
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
        verbose=verbose,
    )
    return token


@app.command(no_args_is_help=False)
def list_experiments(
    auth_token: Annotated[str, typer.Argument("-t", "--token", help="Manually provide the authorization token")],
    cytobank_domain: Annotated[
        Optional[str],
        typer.Option(
            "premium",
            "-d",
            "--domain",
            help="Change the Cytobank domain. Required if you are using Cytobank Enterprise.",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("-v", "--verbose"),
    ] = False,
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

    experiments_list = _list_experiments(auth_token, cytobank_domain, verbose=verbose)

    for _ in experiments_list:
        pass

    return experiments_list


@app.command(no_args_is_help=True)
def upload_files(
    files: Annotated[list[Path], typer.Option("-f", "--files")],
    username: Annotated[str, typer.Option("-u", "--username")],
    exp_id: Annotated[int, typer.Option("-i", "--id")],
    cytobank_domain: Annotated[
        str,
        typer.Option(
            "premium",
            "-d",
            "--domain",
            help="Change the Cytobank domain. Required if you are using Cytobank Enterprise.",
        ),
    ],
    auth_token: Annotated[Optional[str], typer.Option("-t", "--token")] = None,
    verbose: Annotated[bool, typer.Option("-v", "--verbose")] = False,
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

    _upload_files(
        files=files,
        username=username,
        exp_id=exp_id,
        cytobank_domain=cytobank_domain,
        auth_token=auth_token,
        verbose=verbose,
    )


@app.command(no_args_is_help=True)
def show_experiment_files(
    expid: Annotated[
        int,
        typer.Argument(
            help="Id for the experiment in question. Can be found using list_experiments()",
        ),
    ],
    cytobank_domain: Annotated[
        str,
        typer.Option(
            "premium",
            "-d",
            "--domain",
            help="Change the Cytobank domain. Required if you are using Cytobank Enterprise.",
        ),
    ],
    auth_token: Annotated[
        Optional[str], typer.Option("-t", "--token", help="Manually provide the authorization token")
    ] = None,
    verbose: Annotated[bool, typer.Option("-v", "--verbose")] = False,
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

    _list_experiment_fcs_files(experimentId=expid, cytobank_domain=cytobank_domain, auth_token=auth_token)
