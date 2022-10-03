# Cytobank Uploader

Upload FCS files to Cytobank without needing a web browser.

---

`cytobank-uploader` provides an easy way to use the [developer API](https://developer.cytobank.org/) to upload files
to Cytobank.  Useful in the even that you need to upload files from, say, an institutional compute cluster or a 
cloud-based service where a web browser is unavailable but a command line prompt is.

# Installation

For the moment, `cytobank-uploader` must be installed from Github via pip:

```
pip -U install git+https://github.com/milescsmith/cytobank-uploader
```

Or you can clone this repository and install via [Poetry](https://python-poetry.org)

```
git clone https://github.com/milescsmith/cytobank-uploader
cd cytobank-uploader
poetry install
```

## Requirements

`cytobank-uploader` requires:

* [python](https://www.python.org/) (>=3.8, <3.11>)
* [boto3](https://aws.amazon.com/sdk-for-python/)
* [requests](https://requests.readthedocs.io/en/latest/)
* [typer](https://typer.tiangolo.com/)
* [tqdm](https://tqdm.github.io/)
* [rich](https://rich.readthedocs.io/en/stable/introduction.html)
* [loguru](https://loguru.readthedocs.io/en/stable/)


# Usage

There are (currently) four subcommands:

* get-auth-token - Get an authorization token from Cytobank. Required for all operations. While the token will be
    stored to a configuration file, the tokens are only valid for 8 hrs.
* list-experiments - List the experiments associated with the account.  Will print in the form of 
    experimentName: experimentId
* show-experiment-files - Prints a list the FCS files associated with the given experiment
* upload-files -Upload one or more FCS files to a Cytobank project


## Token

All operations in Cytobank require an authorization token, which is then valid for 8 hours.  This token can either be
generated on the website, under account settings, or by:

```
cytobank-uploader get-auth-token --username USERNAME --password PASSWORD
```

> If you are a Cytobank Enterpise customer and have a custom domain, you can also pass `--domain DOMAIN`

This token will be stored in the user's home directory in a file named `.cytobankenvs`


## Uploading files

To upload files, you will (at the moment) need an existing Experiment and its `experimentId`.  A list of experiments and
their ids can be retreived using:

```
cytobank-uploader list-experiments
```

These will be displayed as `name: id`.  Once you have the id, you can upload files using:

```
cytobank-uploader upload-files --files FILE1 (FILE2 FILE3 ...) --username USERNAME --id EXPERIMENTID
```

Multiple files can be uploaded to one experiment at a time.

# License

This project is licensed under the terms of the [Mozilla Public License 2.0](https://choosealicense.com/licenses/mpl-2.0/)

![Alt](https://repobeats.axiom.co/api/embed/ff795c2553f0ebc51a53b7340ce2d43baa74472a.svg "Repobeats analytics image")
