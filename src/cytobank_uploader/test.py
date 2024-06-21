from typing import ClassVar

from textual.app import App, ComposeResult
from textual.layout import Vertical
from textual.widgets import Header, Static

from cytobank_uploader.widgets import ClickableDataTable

# from textual.app import App


# class Uploader(App):
#     def on_key(self, event):
#         if event.key.isdigit():
#             self.background = f"on color({event.key})"


# Uploader.run(log="Uploader.log")


def on_click(self, event) -> None:
    if event.focused.sender.id == "exp-tbl":
        self.selectedexp = event.sender.focused.contents

    self.selectedfile = event.path


class TableTest(App):
    BINDINGS: ClassVar[list[tuple[str, str, str]]] = [
        ("q", "quit", "Quit"),
    ]

    def on_mount(self):
        tbl = self.query_one("#click-tbl", ClickableDataTable)
        tbl.add_column("One")
        tbl.add_column("Two")
        tbl.add_row("une", "deux")
        tbl.add_row("eins", "zwei")
        tbl.add_row("uno", "dos")

    def on_click(self, event: ClickableDataTable.CellClicked) -> None:
        text_bx = self.query_one("#textbox", Static)
        text_bx.update(event.sender.focused.contents)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(Static("Nothing", id="textbox"), ClickableDataTable(id="click-tbl"), id="widget-vert")


tabletest = TableTest(title="Table Test", watch_css=True)

if __name__ == "__main__":
    tabletest.run()
