from datetime import datetime, timedelta
from pathlib import Path
from typing import ClassVar, Optional
from zoneinfo import ZoneInfo

from textual.app import App, ComposeResult
from textual.layout import Center, Container, Horizontal, Vertical
from textual.reactive import var
from textual.widgets import Button, DataTable, DirectoryTree, Footer, Header, Static, TextInput

from cytobank_uploader.interface import _get_auth_token, _list_experiments
from cytobank_uploader.widgets import ClickableDataTable, UpdateableDirTree


class ExperimentTable(ClickableDataTable):
    def on_mount(self) -> None:
        self.add_column("Experiment", width=50)
        self.add_column("ID", width=12)


class UploadQueueTable(DataTable):
    def on_mount(self) -> None:
        self.add_column("Upload queue:", width=50)
        self.add_column("", width=50)
        self.add_row("Files:", "Project")


class ButtonPanel(Static):
    """put buttons here"""

    def compose(self) -> None:
        yield Button("Load token", id="load-btn")
        yield Button("Request token", id="request-btn")


class InputPanel(Static):
    def compose(self):
        yield TextInput(placeholder="username", id="username-input")
        # TODO: need to subclass and make a ***** variant
        yield TextInput(placeholder="password", id="password-input")


class TokenPanel(Static):
    """widget to display authorization-related info"""

    def compose(self) -> ComposeResult:
        yield ButtonPanel()
        yield InputPanel()
        yield Static("Last retreived:", id="refresh-text")
        yield Static("INVALID", id="valid-token")


class Uploader(App):
    CSS_PATH = "tui.css"
    BINDINGS: ClassVar[list[tuple[str, str, str], tuple[str, str, str], tuple[str, str, str], tuple[str, str, str]]] = [
        ("q", "quit", "Quit"),
        ("l", "load", "Load token"),
        ("r", "request", "Request token"),
        ("g", "get", "Get experiments"),
    ]
    token_retrieve_time = var(None)
    token_validity = var(None)

    username = var(None)
    password = var(None)

    exp_list = var(None)
    dirtreepath = var(None)
    selectedfile = var(None)
    selectedexp = var(None)

    async def on_text_input_changed(self, event: TextInput.Changed) -> None:
        if event.sender.id == "username-input":
            self.username = event.value
        elif event.sender.id == "password-input":
            self.password = event.value
        elif event.sender.id == "path-input":
            self.dirtreepath = event.value
            if Path(event.value).exists:
                self.query_one("#path-tree", UpdateableDirTree).update_path(self.dirtreepath)

    def on_mount(self):
        self.dirtreepath = str(Path().home())

    def on_directory_tree_file_click(self, event: DirectoryTree.FileClick) -> None:
        self.selectedfile = event.path

    def on_click(self, event) -> None:
        if event.sender.focused.id == "exp-tbl":
            self.selectedexp = event.sender.focused.contents

    # def on_click(self, event: ClickableDataTable.CellClicked) -> None:
    #     text_bx = self.query_one("#textbox", Static)
    #     text_bx.update(event.sender.focused.contents)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "load-btn":
            _, token_retreive_time = get_token()
            self.query_one("#refresh-text", Static).update(f"Last retreived:\n{token_retreive_time}")
            if (datetime.now(tz=ZoneInfo("UTC")) - datetime.fromisoformat(token_retreive_time)) < timedelta(hours=8):
                self.token_validity = "VALID"
                self.query_one("#valid-token", Static).update(self.token_validity)
                self.add_class("valid")
            else:
                self.token_validity = "INVALID"
                self.query_one("#valid-token", Static).update(self.token_validity)
                self.add_class("invalid")
        elif event.button.id == "request-btn":
            _get_auth_token(self.username, self.password, verbose=False)
        elif event.button.id == "getexp-btn":
            self.exp_list = _list_experiments()
            exptable = self.query_one("#exp-tbl", ExperimentTable)
            for i in self.exp_list:
                (exptable.add_row(i.experimentName, str(i.id)))
        elif event.button.id == "addfile-btn":
            upload_queue = self.query_one("#queue-tbl", UploadQueueTable)
            upload_queue.add_row(str(self.selectedfile), str(self.selectedexp))

    def compose(self) -> ComposeResult:
        self.dirtreepath = str(Path().home())
        yield Header()
        yield TokenPanel()
        yield Horizontal(
            Vertical(Button("Get Experiments", id="getexp-btn"), ExperimentTable(id="exp-tbl"), id="experiment-panel"),
            Vertical(
                TextInput(placeholder=self.dirtreepath, id="path-input"),
                UpdateableDirTree(path=self.dirtreepath, id="path-tree"),
                id="path-panel",
                # DirectoryTree(path="./", id="path-tree"),
            ),
            Vertical(
                Horizontal(
                    Button(
                        "Add file",
                        id="addfile-btn",
                    ),
                    Button("Remove file", id="removefile-btn"),
                    Button("Upload", id="upload-btn"),
                    id="upload-btns",
                ),
                UploadQueueTable(id="queue-tbl"),
                id="upload-panel",
            ),
            classes="treecontainer",
        )
        yield Footer()


def get_token(config_file: Optional[Path] = None) -> tuple[str, str]:
    if config_file is None:
        config_file = Path.home() / ".cytobankenvs"
    config = {k.split("=")[0]: k.split("=")[1] for k in config_file.read_text().rstrip().split("\n")}
    return (config["API_TOKEN"], config["RETRIEVE_TIME"])


uploader = Uploader(title="Cytobank Uploader", watch_css=True)


if __name__ == "__main__":
    uploader.run()
