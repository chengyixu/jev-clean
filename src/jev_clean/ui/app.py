"""Two modes. The model drives discovery and decisions; the person owns execution."""

from __future__ import annotations

import threading
from pathlib import Path

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, ProgressBar, RichLog, Static

from jev_clean.application.service import audit, reassess_selection, save_plan
from jev_clean.domain.models import AuditReport, Candidate, human_bytes
from jev_clean.infrastructure import native
from jev_clean.infrastructure.trash import TrashStore
from jev_clean.infrastructure.update import check_update
from jev_clean.ui.screens import ConfirmScreen, DepthScreen, InfoScreen

HELP = """jev-clean · Nexora — model-driven Clean and Status

1 Clean mysterious System Data     2 Status (disk breakdown)
B           In Clean: switch file review / System Data investigation
↑/↓ or j/k  Navigate evidence / decisions
Space       Toggle a model-approved, safety-checked file
A / N       Select all visible approved / select none
/           Filter paths   Escape  Leave search / cancel scan
Enter       Final review; type TRASH to stage selected files
E           Export private JSON report   R  Re-run model investigation
U           Check updates   H  Transaction history / undo instructions
?           Help   Q  Quit

No model = no operation. There is no rules-only fallback.
Folder classifications and removal decisions come from real local Laya.
Evidence/safety vetoes are separate. Probabilities are not safety guarantees.
The demo uses synthetic metadata but REAL model inference.
Trash staging is reversible; it does NOT free space. No root cleanup.
"""


class JevCleanApp(App):
    TITLE = "jev-clean"
    SUB_TITLE = "NEXORA / CLEAN MYSTERIOUS MACOS SYSTEM DATA"
    CSS = """
    Screen { background: #101820; color: #e1e9ec; }
    Header { background: #172832; color: #6ce5ca; }
    #brand { height: 3; padding: 1 2 0 2; color: #6ce5ca; text-style: bold; }
    #nav { height: 3; margin: 0 2; }
    #nav Button { width: 1fr; min-width: 12; border: none; margin-right: 1; background: #223640; }
    #system-data { height: 4; padding: 0 2; margin: 1 2 0 2; color: #6ce5ca; background: #172832; }
    #summary { height: 3; padding: 1 2; background: #172832; margin: 1 2 0 2; }
    #progress { margin: 0 2; height: 1; }
    #search { margin: 0 2; height: 3; }
    #candidates { height: 1fr; min-height: 5; margin: 0 2; background: #101820; }
    #details { height: 5; margin: 0 2; padding: 1; background: #172832; color: #b7cbd2; }
    #trace { height: 8; margin: 0 2; border-top: solid #2d615e; background: #101820; }
    Footer { background: #172832; }
    .dialog { width: 80%; max-width: 100; height: auto; max-height: 90%; padding: 2; border: thick #6ce5ca; background: #172832; overflow-y: auto; }
    ModalScreen { align: center middle; background: #000000 65%; }
    .dialog Static { margin-bottom: 1; }
    .dialog Button { margin-top: 1; width: 100%; }
    .dialog-title { color: #6ce5ca; text-style: bold; }
    """
    BINDINGS = [
        Binding("1", "clean", "Clean"),
        Binding("2", "status", "Status"),
        Binding("b", "breakdown", "Investigation"),
        Binding("space", "toggle_item", "Select"),
        Binding("a", "all", "All approved"),
        Binding("n", "none", "None"),
        Binding("enter", "review", "Review"),
        Binding("/", "search", "Search"),
        Binding("?", "help", "Help"),
        Binding("r", "rescan", "Rescan"),
        Binding("u", "update", "Update"),
        Binding("e", "export", "Export"),
        Binding("h", "history", "History"),
        Binding("j", "down", "Down", show=False),
        Binding("k", "up", "Up", show=False),
        Binding("escape", "cancel", "Cancel"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, *, home: Path | None = None, demo: bool = False, initial: str | None = None):
        super().__init__()
        self.home = home or Path.home()
        self.demo = demo
        self.initial = initial
        self.mode = "welcome"
        self.clean_breakdown = False
        self.report: AuditReport | None = None
        self.selected: set[str] = set()
        self.candidate_by_id: dict[str, Candidate] = {}
        self.nodes: dict[str, dict] = {}
        self.busy = False
        self.cancel_event = threading.Event()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label(
            "Clean mysterious macOS System Data. The model investigates; you keep control.", id="brand"
        )
        with Horizontal(id="nav"):
            yield Button("1  Clean", id="nav-clean")
            yield Button("2  Status", id="nav-status")
        yield Static(
            "Clean mysterious System Data\nAccounting → model-led investigation → review → cleanup. No model-free fallback.",
            id="system-data",
            markup=False,
        )
        yield Static(
            "Choose Clean or Status. The required local model is prepared automatically.\n"
            + (
                "DEMO: synthetic file metadata, real inference, no removal"
                if self.demo
                else "Local MLX decisions · explicit permission · evidence before action"
            ),
            id="summary",
            markup=False,
        )
        yield ProgressBar(total=100, show_eta=False, id="progress")
        yield Input(placeholder="Filter paths · / focus · Escape return", id="search")
        yield DataTable(id="candidates", cursor_type="row", zebra_stripes=True)
        yield Static(
            "Clean includes System Data accounting, model investigation and file review. B switches investigation/review.",
            id="details",
            markup=False,
        )
        yield RichLog(id="trace", highlight=False, markup=False, wrap=True)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#candidates", DataTable).focus()
        if self.initial:
            self.choose(self.initial)

    @on(Button.Pressed)
    def nav(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("nav-"):
            self.choose(event.button.id[4:])

    def choose(self, mode: str) -> None:
        if self.busy:
            self.notify("Investigation in progress; Escape cancels first")
            return
        self.mode = mode
        self.clean_breakdown = False
        self.query_one("#system-data", Static).update(
            "System Data: awaiting this investigation. Native totals will appear here; unavailable never means zero."
        )
        self.report = None
        self.candidate_by_id.clear()
        self.nodes.clear()
        self.selected.clear()
        self.query_one("#search", Input).value = ""
        self.query_one("#candidates", DataTable).clear(columns=True)
        if self.demo:
            self.start_scan(False)
        else:
            self.push_screen(DepthScreen(), self.depth_selected)

    def depth_selected(self, deep: bool | None) -> None:
        if deep is None:
            return
        if deep:
            try:
                with self.suspend():
                    print("\nRead-only diagnostics. Password stays in sudo; Ctrl-C cancels.")
                    authorized = native.authorize()
            except (Exception, KeyboardInterrupt):
                authorized = False
            if not authorized:
                self.notify("Authorization cancelled/failed; no investigation started.", severity="warning")
                return
        self.start_scan(deep)

    def start_scan(self, deep: bool) -> None:
        self.busy = True
        self.cancel_event = threading.Event()
        self.query_one("#progress", ProgressBar).update(total=None)
        self.query_one("#trace", RichLog).clear()
        self.query_one("#summary", Static).update(
            f"{self.mode.upper()} · loading mandatory model…\nNo inference fallback. Escape cancels."
        )
        self.scan_worker(deep)

    @work(thread=True)
    def scan_worker(self, deep: bool) -> None:
        try:
            report = audit(
                self.home,
                self.mode,
                deep=deep,
                demo=self.demo,
                progress=lambda text: self.call_from_thread(self.trace, text),
                cancelled=self.cancel_event.is_set,
            )
            self.call_from_thread(self.accept_report, report)
        except Exception as error:
            self.call_from_thread(self.scan_failed, str(error))

    def trace(self, text: str) -> None:
        self.query_one("#trace", RichLog).write(Text(text))

    def scan_failed(self, message: str) -> None:
        self.busy = False
        self.report = None
        self.selected.clear()
        self.candidate_by_id.clear()
        self.query_one("#candidates", DataTable).clear(columns=True)
        self.query_one("#progress", ProgressBar).update(total=100, progress=0)
        self.query_one("#summary", Static).update(
            f"Operation stopped: {message}\nAutomatic model preparation did not succeed. Check connection and press R to retry."
        )
        self.trace(message)

    def accept_report(self, report: AuditReport) -> None:
        self.busy = False
        self.report = report
        self.candidate_by_id = {c.id: c for c in report.scan.candidates}
        self.nodes = {str(i): n for i, n in enumerate(report.exploration.get("nodes", []))}
        self.query_one("#progress", ProgressBar).update(total=100, progress=100)
        self.render_report()
        self.trace(report.model_status)
        for warning in report.exploration.get("warnings", []):
            self.trace(warning)
        self.query_one("#candidates", DataTable).focus()

    def render_report(self) -> None:
        if not self.report:
            return
        report = self.report
        table = self.query_one("#candidates", DataTable)
        table.clear(columns=True)
        query = self.query_one("#search", Input).value.casefold()
        prefix = "DEMO DATA / REAL INFERENCE | " if self.demo else ""
        context = report.system_data
        native_total = (
            f"{human_bytes(context['native_other_bytes'])} reported @ {context['timestamp']}"
            if context["native_other_bytes"] is not None
            else "native total unavailable — not zero"
        )
        self.query_one("#system-data", Static).update(
            f"{prefix}System Data · {native_total}\n"
            f"{context['approved_candidate_count']} model-approved potential cleanup files / {human_bytes(context['approved_candidate_bytes'])}. "
            "Category membership not proven; Trash staging frees no space.\n"
            + (
                "CLEAN: B switches investigation ↔ file review. Select then confirm."
                if self.mode == "clean"
                else "STATUS: model-directed breakdown; nested directory sizes overlap."
            )
        )
        if self.mode == "clean" and not self.clean_breakdown:
            table.add_columns("Pick", "Allocated", "Location", "Laya", "Safety veto")
            for c in report.scan.candidates:
                if query not in c.path.casefold():
                    continue
                prediction = (
                    f"{c.decision.choice} {max(c.decision.probabilities.values()):.0%}"
                    if c.decision
                    else "UNASSESSED"
                )
                table.add_row(
                    "●" if c.id in self.selected else "○" if c.selectable else "—",
                    human_bytes(c.allocated_bytes),
                    Text(c.path.replace(str(self.home), "~", 1)),
                    prediction,
                    "pass" if c.eligible else "VETO",
                    key=c.id,
                )
            size = sum(self.candidate_by_id[i].allocated_bytes for i in self.selected)
            summary = f"{prefix}CLEAN · {len(report.exploration.get('steps', []))} exploration decisions · {len(self.selected)} selected / {human_bytes(size)}\n{report.model_status}"
        else:
            table.add_columns("Allocated", "Model-directed breakdown", "Explore", "Model classification")
            for key, node in self.nodes.items():
                if query not in node["path"].casefold():
                    continue
                decision = node.get("decision")
                purpose = node.get("purpose")
                table.add_row(
                    human_bytes(node["allocated_bytes"]),
                    Text("  " * node["depth"] + node["path"].replace(str(self.home), "~", 1)),
                    decision["choice"] if decision else "observed",
                    purpose["choice"] if purpose else "unclassified",
                    key=key,
                )
            category = report.categories
            detail = (
                f"Native Other {human_bytes(category.other_bytes)} · residual {human_bytes(category.residual_bytes)} · delta {category.discrepancy_bytes} B @ {category.timestamp}"
                if category
                else "Native category totals unavailable. Filesystem rows are not proven System Data membership."
            )
            summary = f"{self.mode.upper()} · System Data investigation · model-selected depth; do not sum nested rows\n{detail}"
        self.query_one("#summary", Static).update(summary)

    @on(DataTable.RowSelected, "#candidates")
    def row_selected(self) -> None:
        self.action_review()

    @on(DataTable.RowHighlighted, "#candidates")
    def highlight(self, event: DataTable.RowHighlighted) -> None:
        key = str(event.row_key.value)
        if self.mode == "clean" and not self.clean_breakdown and key in self.candidate_by_id:
            item = self.candidate_by_id[key]
            dist = (
                " · ".join(f"{k} {v:.1%}" for k, v in item.decision.probabilities.items())
                if item.decision
                else "unassessed"
            )
            latency = f"{item.decision.elapsed_ms:.1f} ms" if item.decision else ""
            self.query_one("#details", Static).update(
                f"{item.path}\nMODEL: {dist} · {latency}\nGUARD: {item.reason}"
            )
        elif (self.mode == "status" or self.clean_breakdown) and key in self.nodes:
            node = self.nodes[key]
            decision = node.get("decision")
            self.query_one("#details", Static).update(
                f"{node['path']}\nExploration: {decision or 'Not expanded by model'}\nCategory attribution unresolved; model classification is a hypothesis, not proof."
            )

    @on(Input.Changed, "#search")
    def filter_changed(self) -> None:
        self.render_report()

    def action_toggle_item(self) -> None:
        if self.mode != "clean" or self.clean_breakdown or self.busy:
            return
        table = self.query_one("#candidates", DataTable)
        if table.row_count:
            key = str(table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value)
            item = self.candidate_by_id.get(key)
            if item and item.selectable:
                self.selected.symmetric_difference_update({key})
                row = table.cursor_row
                self.render_report()
                table.move_cursor(row=row)

    def action_all(self) -> None:
        if self.mode == "clean" and not self.clean_breakdown and not self.busy:
            query = self.query_one("#search", Input).value.casefold()
            self.selected.update(
                c.id for c in self.candidate_by_id.values() if c.selectable and query in c.path.casefold()
            )
            self.render_report()

    def action_breakdown(self) -> None:
        if self.mode == "clean" and self.report and not self.busy:
            self.clean_breakdown = not self.clean_breakdown
            self.query_one("#search", Input).value = ""
            self.render_report()

    def action_none(self) -> None:
        self.selected.clear()
        self.render_report()

    def action_review(self) -> None:
        if self.mode == "clean" and not self.clean_breakdown and not self.busy and self.selected:
            items = [self.candidate_by_id[i] for i in self.selected]
            self.push_screen(
                ConfirmScreen(items), lambda accepted: self.move_selected(items) if accepted else None
            )

    def move_selected(self, items: list[Candidate]) -> None:
        if self.demo:
            self.notify("Demo data: no actual files to move")
            return
        self.busy = True
        self.move_worker(items)

    @work(thread=True)
    def move_worker(self, items: list[Candidate]) -> None:
        try:
            assessed = reassess_selection(items)
            result = TrashStore(self.home).move(assessed, open_paths=native.open_files())
            self.call_from_thread(
                self.trace,
                f"Staged {result.moved}; space NOT freed. Restore: jev-clean restore {result.batch_id}",
            )
            for error in result.failed:
                self.call_from_thread(self.trace, error)
        except Exception as error:
            self.call_from_thread(self.trace, f"Refused: {error}")
        finally:
            self.call_from_thread(self.finish_move)

    def finish_move(self) -> None:
        self.busy = False
        self.selected.clear()
        self.report = None
        self.candidate_by_id.clear()
        self.query_one("#candidates", DataTable).clear(columns=True)
        self.query_one("#system-data", Static).update(
            "System Data cleanup review finished. Files staged in Trash do not free space.\nRe-run Clean after any manual Trash emptying to get a new native reading; no reduction is assumed."
        )
        self.query_one("#summary", Static).update(
            "Review finished. History has receipts. R to investigate again; Trash staging does not free space."
        )

    def action_cancel(self) -> None:
        self.cancel_event.set()
        self.query_one("#candidates", DataTable).focus()

    def action_search(self) -> None:
        self.query_one("#search", Input).focus()

    def action_help(self) -> None:
        self.push_screen(InfoScreen(HELP))

    def action_down(self) -> None:
        self.query_one("#candidates", DataTable).action_cursor_down()

    def action_up(self) -> None:
        self.query_one("#candidates", DataTable).action_cursor_up()

    def action_rescan(self) -> None:
        if self.mode != "welcome":
            self.choose(self.mode)

    def action_clean(self) -> None:
        self.choose("clean")

    def action_status(self) -> None:
        self.choose("status")

    def action_export(self) -> None:
        if self.report and not self.busy:
            try:
                path = self.home / ".local/state/jev-clean/latest-plan.json"
                save_plan(path, self.report)
                self.notify(f"Private report: {path}")
            except Exception as error:
                self.notify(str(error), severity="error")

    def action_history(self) -> None:
        try:
            rows = TrashStore(self.home).history() if not self.demo else []
            text = (
                "\n".join(f"{r['id']} · {len(r['entries'])} records" for r in rows[:8]) or "No transactions."
            )
            self.push_screen(
                InfoScreen(
                    text
                    + "\n\nUndo: jev-clean restore <batch-id>\nExisting source files are never overwritten."
                )
            )
        except Exception as error:
            self.notify(str(error), severity="error")

    @work(thread=True)
    def action_update(self) -> None:
        try:
            update = check_update()
            text = f"Installed {update['installed']} · latest {update['latest']}\n{update['url']}\n\njev-clean update --apply prompts before installation."
        except Exception as error:
            text = f"Update check unavailable: {error}"
        self.call_from_thread(self.push_screen, InfoScreen(text))
