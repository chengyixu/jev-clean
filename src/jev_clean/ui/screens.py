from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static

from jev_clean.domain.models import Candidate, human_bytes


class InfoScreen(ModalScreen):
    BINDINGS = [("escape", "dismiss", "Back")]

    def __init__(self, text: str):
        super().__init__()
        self.message = text

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Static(self.message, markup=False)
            yield Button("Back", id="back")

    @on(Button.Pressed, "#back")
    def back(self) -> None:
        self.dismiss()


class DepthScreen(ModalScreen[bool | None]):
    BINDINGS = [("escape", "cancel", "Cancel"), ("d", "deep", "Deep"), ("l", "limited", "Limited")]

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Static("Deeper evidence, not more deletion power", classes="dialog-title")
            yield Static(
                "Authorize native read-only diagnostics with sudo? Password entry stays in your terminal. "
                "Sudo does not bypass Full Disk Access or SIP. The app and model never run as root.",
                markup=False,
            )
            yield Button("D · Authorize deep scan", id="deep", variant="primary")
            yield Button("L · Continue without sudo", id="limited")
            yield Button("Cancel", id="cancel")

    @on(Button.Pressed)
    def pressed(self, event: Button.Pressed) -> None:
        self.dismiss(True if event.button.id == "deep" else False if event.button.id == "limited" else None)

    def action_deep(self) -> None:
        self.dismiss(True)

    def action_limited(self) -> None:
        self.dismiss(False)

    def action_cancel(self) -> None:
        self.dismiss(None)


class ConfirmScreen(ModalScreen[bool]):
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, items: list[Candidate], *, maintenance: bool = False):
        super().__init__(id="confirm-cleanup")
        self.items = items
        self.maintenance = maintenance

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            if self.maintenance:
                text = "Reset Quick Look thumbnail cache? This rebuilds previews and may temporarily slow them. No speed gain is promised. Type RESET."
            else:
                text = "\n".join(c.path for c in self.items[:12])
                if len(self.items) > 12:
                    text += (
                        f"\n… and {len(self.items) - 12} more selected files (review in table/export first)."
                    )
                text += f"\n\nMove {len(self.items)} files ({human_bytes(sum(c.allocated_bytes for c in self.items))}) to Trash? "
                text += "This does not free space until you empty Trash yourself. Type TRASH. No files are permanently erased."
            yield Static(text, markup=False)
            yield Input(placeholder="RESET" if self.maintenance else "TRASH", id="confirmation")
            yield Button("Confirm", id="confirm", variant="warning")
            yield Button("Cancel", id="cancel")

    @on(Button.Pressed, "#confirm")
    @on(Input.Submitted, "#confirmation")
    def confirm(self) -> None:
        expected = "RESET" if self.maintenance else "TRASH"
        if self.query_one("#confirmation", Input).value == expected:
            self.dismiss(True)
        else:
            self.notify(f"Type {expected} exactly to confirm", severity="warning")

    @on(Button.Pressed, "#cancel")
    def action_cancel(self) -> None:
        self.dismiss(False)
