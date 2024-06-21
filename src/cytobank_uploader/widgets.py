import contextlib
from dataclasses import dataclass

# from rich.progress import Progress
from rich.tree import Tree
from textual import events
from textual._types import MessageTarget
from textual.message import Message
from textual.widgets import DataTable, DirectoryTree

# from textual.widgets._data_table import Coord
from textual.widgets._tree_control import NodeID, TreeNode


@dataclass
class DirEntry:
    path: str
    is_dir: bool


class ClickableDataTable(DataTable):
    """Variant of the DataTable widget that emits the contents of a cell when that cell is clicked"""

    class CellClicked(Message, bubble=True):
        def __init__(self, sender: MessageTarget, contents: str) -> None:
            self.contents = contents
            super().__init__(sender)

    def on_click(self, event: events.Click) -> None:
        if meta := event.style.meta:
            with contextlib.suppress(KeyError):
                self.contents = self.data[meta["row"]][meta["column"]]
                export = self.CellClicked(self, self.contents)
                self.emit(export)


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
