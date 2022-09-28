from typing import Optional, Tuple, NewType
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from cytobank_uploader.interface import _get_auth_token, _list_experiments

from textual.app import App, ComposeResult
from textual.layout import Container, Vertical, Horizontal, Center
from textual.widgets import Button, Header, Footer, DirectoryTree, DataTable, Static, TextInput
from textual.reactive import var
from textual.widgets._tree_control import TreeNode, NodeID
from rich.tree import Tree

@dataclass
class DirEntry:
    path: str
    is_dir: bool


class UpdateableDirTree(DirectoryTree):
    """Variant of the DirectoryTree widget that can handle a change in directory"""

    def update_path(self, newpath, label=None):
        if label is None:
            label = str(newpath)
        self.path = newpath
        self.data = DirEntry(newpath, True)
        self._tree = Tree(label)
        self.node_id = NodeID(0)
        self.root = TreeNode(None, 0, self, self._tree, label, self.data)
        self.nodes = {0: self.root}
        self._tree.label = self.root
        # self.load_directory(newpath)


class ExperimentTable(DataTable):
    
    def on_mount(self) -> None:
        self.add_column("Experiment", width=50)
        self.add_column("ID", width=12)


class ButtonPanel(Static):
    """put buttons here"""

    def compose(self) -> None:
        yield Button("Load token", id="load")
        yield Button("Request token", id="request")
    

class InputPanel(Static):

    def compose(self):
        yield TextInput(placeholder="username", id="username")
        # TODO: need to subclass and make a ***** variant
        yield TextInput(placeholder="password", id="password")


class TokenPanel(Static):
    """widget to display authorization-related info"""

    def compose(self) -> ComposeResult:
        yield ButtonPanel()
        yield InputPanel()
        yield Static("Last retreived:", id="refresh-text")
        yield Static("INVALID", id="valid-token")


class Uploader(App):
    CSS_PATH = "tui.css"
    BINDINGS = [
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
    exptable = ExperimentTable(id="experimenttbl")
    dirtreepath = var(None)
    selectedfile = var(None)

    async def on_text_input_changed(self, event: TextInput.Changed) -> None:
        if event.sender.id == "username":
            self.username = event.value
        elif event.sender.id == "password":
            self.password = event.value
        elif event.sender.id == "filepath":
            self.dirtreepath = event.value
            self.query_one("#tree-two", UpdateableDirTree).update_path(self.dirtreepath)
            # self.query_one("#tree-two", DirectoryTree).update(self.dirtreepath)

    def on_mount(self):
        self.dirtreepath = str(Path().home())

    def on_directory_tree_file_click(self, event: DirectoryTree.FileClick) -> None:
        self.selectedfile = event.path
        # self.query_one("#filepath", TextInput).update(self.selectedfile)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "load":
            _, token_retreive_time = get_token()
            self.query_one("#refresh-text", Static).update(f"Last retreived:\n{token_retreive_time}")
            if (datetime.now() - datetime.fromisoformat(token_retreive_time)) < timedelta(hours=8):
                self.token_validity = "VALID"
                self.query_one("#valid-token", Static).update(self.token_validity)
                self.add_class("valid")
            else:
                self.token_validity = "INVALID"
                self.query_one("#valid-token", Static).update(self.token_validity)
                self.add_class("invalid")
        elif event.button.id == "request":
            _get_auth_token(self.username, self.password, verbose=False)
        elif event.button.id == "getexperiments":
            self.exp_list = _list_experiments()
            for i in self.exp_list:
                (
                    self.exptable.add_row(i.experimentName, str(i.id))
                )


    def compose(self) -> ComposeResult:
        yield Header()
        yield TokenPanel()
        yield Container(
            Vertical(
                Button("Get Experiments", id="getexperiments"),
                self.exptable,
                id="experimentvertical"
            ),
            # Static(
                TextInput(id="filepath"),
                UpdateableDirTree(path="./", id="tree-two"),
                # DirectoryTree(path="./", id="tree-two"),
            # ),
            classes = "treecontainer"
        )
        yield Footer()

        # self.exptable.add_column("Experiment", width=50)
        # self.exptable.add_column("ID", width=10)


def get_token(config_file: Optional[Path] = None) -> Tuple[str, str]:
    if config_file is None:
        config_file = Path.home() / ".cytobankenvs"
    config = {
        k.split("=")[0]: k.split("=")[1]
        for k in config_file.read_text().rstrip().split("\n")
    }
    return (config["API_TOKEN"], config["RETRIEVE_TIME"])


uploader = Uploader(title="Cytobank Uploader", watch_css=True)


if __name__ == "__main__":
    uploader.run()