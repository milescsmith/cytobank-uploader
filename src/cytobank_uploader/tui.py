from textual.app import App, ComposeResult
from textual import layout
from textual.widgets import Button


class Uploader(App):
    CSS_PATH = "tui.css"

    def compose(self) -> ComposeResult:
        yield layout.Container(
            
            Button("Get Token", id="get-token"),
            Button("List Experiments", id="list-experiments"),
            id="main_panel"
        )


if __name__ == "__main__":
    Uploader().run()