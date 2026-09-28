"""Short questions. No promotional copy or typed confirmation rituals."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from jev_clean.domain.models import Candidate, human_bytes


class QuestionScreen(ModalScreen[bool | None]):
    BINDINGS = [
        ("y", "yes", "Yes"),
        ("n", "no", "No"),
        ("left", "focus_yes", "Yes"),
        ("right", "focus_no", "No"),
        ("escape", "cancel", "Back"),
    ]

    def __init__(self, question: str, detail: str = "", *, id: str):
        super().__init__(id=id)
        self.question = question
        self.detail = detail

    def compose(self) -> ComposeResult:
        with Vertical(classes="question"):
            yield Static(self.question, classes="question-title", markup=False)
            if self.detail:
                yield Static(self.detail, markup=False)
            with Horizontal(classes="answers"):
                yield Button("Yes", id="yes")
                yield Button("No", id="no")

    def on_mount(self) -> None:
        self.query_one("#no", Button).focus()

    def action_focus_yes(self) -> None:
        self.query_one("#yes", Button).focus()

    def action_focus_no(self) -> None:
        self.query_one("#no", Button).focus()

    @on(Button.Pressed, "#yes")
    def action_yes(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#no")
    def action_no(self) -> None:
        self.dismiss(False)

    def action_cancel(self) -> None:
        self.dismiss(None)


class DepthScreen(QuestionScreen):
    def __init__(self):
        super().__init__("Use sudo?", id="sudo-question")


class ConfirmScreen(QuestionScreen):
    def __init__(self, items: list[Candidate]):
        count = len(items)
        size = human_bytes(sum(i.allocated_bytes for i in items))
        super().__init__(
            "Delete selected files?",
            f"{count} {'file' if count == 1 else 'files'} · {size}\nMoves to Trash; recoverable.",
            id="confirm-cleanup",
        )


class InfoScreen(ModalScreen):
    BINDINGS = [("escape", "dismiss", "Back"), ("enter", "dismiss", "Back")]

    def __init__(self, text: str):
        super().__init__()
        self.message = text

    def compose(self) -> ComposeResult:
        with Vertical(classes="question"):
            yield Static(self.message, markup=False)
            yield Button("Back", id="back")

    @on(Button.Pressed, "#back")
    def back(self) -> None:
        self.dismiss()
