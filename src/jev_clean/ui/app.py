"""Minimal sequential terminal: choose → logs → result. Model/safety engine unchanged."""

from __future__ import annotations

import threading
import warnings
from pathlib import Path

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Input, OptionList, RichLog, Static

from jev_clean.application.service import audit, reassess_selection, save_plan
from jev_clean.domain.models import AuditReport, Candidate, human_bytes
from jev_clean.domain.usage import UsageRow, bar, usage_rows
from jev_clean.infrastructure import native
from jev_clean.infrastructure.trash import TrashStore
from jev_clean.infrastructure.update import check_update
from jev_clean.ui.screens import ConfirmScreen, DepthScreen, InfoScreen

HELP = """1 Clean    2 Status
↑↓ / j k   Move    Space select    A all    N none
Enter      Delete / open directory    Esc back
/ filter   I file details   S number source   R rescan
E export   H history   U update
Q quit

Deletion moves files to Trash. Model approval and safety checks still apply."""


class JevCleanApp(App):
    TITLE = "jev-clean"
    ENABLE_COMMAND_PALETTE = False
    CSS = """
    Screen { background: #171717; color: #dedede; padding: 1 2; }
    #title { height: 2; text-style: bold; }
    #menu { height: 2; border: none; padding: 0; background: #171717; }
    #menu > .option-list--option-highlighted { background: #303030; color: #ffffff; }
    #summary { height: auto; max-height: 3; margin-bottom: 1; }
    #trace { height: 1fr; border: none; background: #171717; }
    #results { height: 1fr; border: none; background: #171717; }
    DataTable > .datatable--cursor { background: #383838; color: #ffffff; text-style: bold; }
    #search { height: 3; border: none; background: #252525; }
    #hint { height: 1; margin-top: 1; color: #999999; }
    .question { width: 60; max-width: 95%; height: auto; padding: 1 2; background: #202020; border: solid #666666; }
    .question-title { text-style: bold; margin-bottom: 1; }
    ModalScreen { align: center middle; background: #000000 60%; }
    .answers { height: 3; margin-top: 1; }
    Button { width: 12; min-width: 8; border: none; background: #303030; margin-right: 2; }
    Button:focus { background: #555555; text-style: bold; }
    """
    BINDINGS = [
        Binding(key, action, label, show=False)
        for key, action, label in [
            ("1", "clean", "Clean"),
            ("2", "status", "Status"),
            ("space", "toggle_item", "Select"),
            ("a", "all", "All"),
            ("n", "none", "None"),
            ("enter", "review", "Review"),
            ("/", "search", "Filter"),
            ("?", "help", "Help"),
            ("r", "rescan", "Rescan"),
            ("u", "update", "Update"),
            ("e", "export", "Export"),
            ("h", "history", "History"),
            ("i", "details", "Details"),
            ("s", "source", "Source"),
            ("j", "down", "Down"),
            ("k", "up", "Up"),
            ("escape", "cancel", "Back"),
            ("q", "quit", "Quit"),
        ]
    ]

    def __init__(self, *, home: Path | None = None, demo: bool = False, initial: str | None = None):
        super().__init__()
        self.home = home or Path.home()
        self.demo = demo
        self.initial = initial
        self.mode = "welcome"
        self.stage = "menu"
        self.report: AuditReport | None = None
        self.selected: set[str] = set()
        self.candidate_by_id: dict[str, Candidate] = {}
        self.usage_by_id: dict[str, UsageRow] = {}
        self.usage_parent: str | None = None
        self.busy = False
        self.cancel_event = threading.Event()
        self.scope: list[Path] | None = None
        self.deep = False

    def compose(self) -> ComposeResult:
        yield Static("jev-clean", id="title", markup=False)
        yield OptionList("1. Clean", "2. Status", id="menu")
        yield Static("", id="summary", markup=False)
        yield RichLog(id="trace", markup=False, wrap=True, auto_scroll=True)
        yield Input(placeholder="Filter", id="search")
        yield DataTable(id="results", show_header=False, cursor_type="row")
        yield Static("↑↓ Enter · q quit", id="hint", markup=False)

    def on_mount(self) -> None:
        self.show_stage("menu")
        if self.initial:
            self.choose(self.initial)

    def show_stage(self, stage: str) -> None:
        self.stage = stage
        self.query_one("#menu").display = stage == "menu"
        self.query_one("#trace").display = stage in ("running", "deleting", "error")
        self.query_one("#results").display = stage in ("review", "status")
        self.query_one("#search").display = False
        self.query_one("#summary").display = stage not in ("menu", "running", "deleting")
        self.query_one("#title", Static).update(
            "jev-clean" if stage == "menu" else self.mode.title() + (" (demo)" if self.demo else "")
        )
        hints = {
            "menu": "↑↓ Enter · q quit",
            "running": "Esc cancel",
            "deleting": "Finishing…",
            "review": "Space select · a all · Enter delete · Esc back",
            "status": "Enter open · Esc back",
            "error": "Esc back",
            "done": "Esc back",
        }
        self.query_one("#hint", Static).update(hints.get(stage, "Esc back"))
        if stage == "menu":
            self.query_one("#menu", OptionList).focus()
        elif stage in ("review", "status"):
            self.query_one("#results", DataTable).focus()
        else:
            self.query_one("#trace", RichLog).focus()

    @on(OptionList.OptionSelected, "#menu")
    def menu_selected(self, event: OptionList.OptionSelected) -> None:
        self.choose("clean" if event.option_index == 0 else "status")

    def choose(self, mode: str) -> None:
        if self.busy:
            return
        self.mode = mode
        self.scope = None
        self.usage_parent = None
        self.report = None
        self.selected.clear()
        self.candidate_by_id.clear()
        self.query_one("#search", Input).value = ""
        if mode == "clean" and not self.demo:
            self.push_screen(DepthScreen(), self.depth_selected)
        else:
            self.start_scan(False)

    def depth_selected(self, deep: bool | None) -> None:
        if deep is None:
            self.show_stage("menu")
            return
        if deep:
            try:
                with self.suspend():
                    authorized = native.authorize()
            except (Exception, KeyboardInterrupt):
                authorized = False
            if not authorized:
                self.query_one("#summary", Static).update("Sudo cancelled.")
                self.show_stage("done")
                return
        self.start_scan(deep)

    def start_scan(self, deep: bool) -> None:
        self.deep = deep
        self.busy = True
        self.cancel_event = threading.Event()
        self.query_one("#trace", RichLog).clear()
        self.show_stage("running")
        self.scan_worker(deep)

    @work(thread=True)
    def scan_worker(self, deep: bool) -> None:
        try:
            # Preserve upstream diagnostics in exports without splashing them over the terminal.
            with warnings.catch_warnings(record=True) as captured:
                report = audit(
                    self.home,
                    self.mode,
                    deep=deep,
                    demo=self.demo,
                    roots=self.scope,
                    progress=lambda line: self.call_from_thread(self.trace, line),
                    cancelled=self.cancel_event.is_set,
                )
            if captured:
                report.diagnostics["model_warnings"] = [str(w.message) for w in captured]
            self.call_from_thread(self.accept_report, report)
        except Exception as error:
            self.call_from_thread(self.scan_failed, str(error))

    def trace(self, line: str) -> None:
        self.query_one("#trace", RichLog).write(Text(line))

    def scan_failed(self, message: str) -> None:
        self.busy = False
        self.report = None
        self.selected.clear()
        self.candidate_by_id.clear()
        self.query_one("#summary", Static).update("Stopped: " + message)
        self.trace(message)
        self.show_stage("error")

    def accept_report(self, report: AuditReport) -> None:
        self.busy = False
        if self.cancel_event.is_set():
            self.report = None
            self.selected.clear()
            self.show_stage("menu")
            return
        self.report = report
        self.candidate_by_id = {c.id: c for c in report.scan.candidates}
        for warning in report.exploration.get("warnings", []):
            self.trace(warning)
        self.render_report()
        self.show_stage("review" if self.mode == "clean" else "status")

    def render_report(self) -> None:
        if not self.report:
            return
        report = self.report
        table = self.query_one("#results", DataTable)
        table.clear(columns=True)
        query = self.query_one("#search", Input).value.casefold()
        if self.mode == "clean":
            table.add_column("Pick", width=3)
            table.add_column("Files", width=max(15, self.size.width - 25))
            table.add_column("Size", width=10)
            approved = [c for c in report.scan.candidates if c.selectable]
            for c in approved:
                if query not in c.path.casefold():
                    continue
                table.add_row(
                    Text("[x]" if c.id in self.selected else "[ ]"),
                    Text(c.path.replace(str(self.home), "~", 1)),
                    human_bytes(c.allocated_bytes),
                    key=c.id,
                )
            size = sum(self.candidate_by_id[i].allocated_bytes for i in self.selected)
            stats = report.exploration.get("stats", {})
            assessed = stats.get(
                "model_assessed", sum(c.decision is not None for c in report.scan.candidates)
            )
            if approved:
                summary = f"{len(self.selected)}/{len(approved)} selected · {human_bytes(size)}"
            elif stats.get("open_file_check_available") is False:
                summary = "No cleanup authorized: open-file check unavailable"
            elif assessed:
                summary = f"0 approved · {assessed} assessed by model"
            elif report.scan.files_seen:
                summary = f"0 approved · {report.scan.files_seen} observed · protected by safety checks"
            else:
                summary = "No files assessed"
            if report.categories:
                recorded = report.categories.timestamp.split(" ")[1].split(".")[0]
                label = "demo" if report.demo else "macOS log " + recorded
                summary += f" | System Data {human_bytes(report.categories.other_bytes)} ({label})"
            if not report.exploration.get("complete", True):
                summary += " | Scan incomplete"
            if stats.get("model_assessed") and stats.get("protected_files"):
                summary += f"\n{stats['model_assessed']} model decisions · {stats['protected_files']} protected files"
        else:
            table.add_column("Location", width=max(12, self.size.width - 44))
            table.add_column("Usage", width=14)
            table.add_column("Share", width=5)
            table.add_column("Size", width=10)
            rows = usage_rows(report.exploration.get("nodes", []), self.usage_parent)
            self.usage_by_id = {str(i): row for i, row in enumerate(rows)}
            for key, row in self.usage_by_id.items():
                if query not in row.path.casefold():
                    continue
                label = row.path.replace(str(self.home), "~", 1)
                table.add_row(
                    Text(label),
                    bar(row.percent),
                    f"{row.percent:.0f}%" if row.percent is not None else "?",
                    human_bytes(row.allocated_bytes)
                    + ("+" if row.allocated_bytes is not None and not row.complete else ""),
                    key=key,
                )
            summary = "% of measured rows"
            if self.usage_parent:
                summary = self.usage_parent.replace(str(self.home), "~", 1) + " · " + summary
            if any(r.percent is None for r in rows) or not report.exploration.get("complete", True):
                summary += " · partial"
            if not rows:
                summary = "No usage measured."
        self.query_one("#summary", Static).update(summary)

    def on_resize(self) -> None:
        if self.report and self.stage in ("review", "status"):
            self.render_report()

    @on(DataTable.RowSelected, "#results")
    def row_selected(self) -> None:
        self.action_review()

    @on(Input.Changed, "#search")
    def filter_changed(self) -> None:
        self.render_report()

    def action_toggle_item(self) -> None:
        if self.stage != "review" or self.busy:
            return
        table = self.query_one("#results", DataTable)
        if table.row_count:
            key = str(table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value)
            item = self.candidate_by_id.get(key)
            if item and item.selectable:
                self.selected.symmetric_difference_update({key})
                row = table.cursor_row
                self.render_report()
                table.move_cursor(row=row)

    def action_all(self) -> None:
        if self.stage == "review" and not self.busy:
            query = self.query_one("#search", Input).value.casefold()
            self.selected.update(
                c.id for c in self.candidate_by_id.values() if c.selectable and query in c.path.casefold()
            )
            self.render_report()

    def action_none(self) -> None:
        if not self.busy:
            self.selected.clear()
            self.render_report()

    def action_review(self) -> None:
        if self.busy:
            return
        if self.stage == "review" and self.selected:
            items = [self.candidate_by_id[i] for i in self.selected]
            self.push_screen(ConfirmScreen(items), lambda yes: self.move_selected(items) if yes else None)
        elif self.stage == "status" and self.report:
            table = self.query_one("#results", DataTable)
            if not table.row_count:
                return
            key = str(table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value)
            row = self.usage_by_id[key]
            if not row.is_dir:
                return
            children = usage_rows(self.report.exploration.get("nodes", []), row.path)
            if children:
                self.usage_parent = row.path
                self.render_report()
            elif not self.demo:
                self.scope = [Path(row.path)]
                self.usage_parent = None
                self.start_scan(False)

    def move_selected(self, items: list[Candidate]) -> None:
        if self.demo:
            self.query_one("#summary", Static).update("Demo. No files deleted.")
            self.show_stage("done")
            return
        self.busy = True
        self.show_stage("deleting")
        self.move_worker(items)

    @work(thread=True)
    def move_worker(self, items: list[Candidate]) -> None:
        try:
            assessed = reassess_selection(items)
            result = TrashStore(self.home).move(assessed, open_paths=native.open_files())
            text = f"{result.moved} files moved to Trash."
            if result.failed:
                text += f" {len(result.failed)} skipped."
            self.call_from_thread(self.trace, f"Undo: jev-clean restore {result.batch_id}")
            for error in result.failed:
                self.call_from_thread(self.trace, error)
            self.call_from_thread(self.finish_move, text)
        except Exception as error:
            self.call_from_thread(self.scan_failed, str(error))

    def finish_move(self, text: str) -> None:
        self.busy = False
        self.selected.clear()
        self.report = None
        self.candidate_by_id.clear()
        self.query_one("#summary", Static).update(text)
        self.show_stage("done")

    def action_cancel(self) -> None:
        if len(self.screen_stack) > 1:
            return
        if self.busy:
            if self.stage != "deleting":
                self.cancel_event.set()
                self.query_one("#hint", Static).update("Cancelling…")
            return
        search = self.query_one("#search", Input)
        if search.display:
            search.display = False
            self.query_one("#results", DataTable).focus()
        elif self.stage == "status" and self.usage_parent:
            self.usage_parent = None
            self.render_report()
        else:
            self.report = None
            self.selected.clear()
            self.show_stage("menu")

    def action_search(self) -> None:
        if self.stage in ("review", "status"):
            self.query_one("#search").display = True
            self.query_one("#search", Input).focus()

    def action_details(self) -> None:
        table = self.query_one("#results", DataTable)
        if self.stage not in ("review", "status") or not table.row_count:
            return
        key = str(table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value)
        if self.stage == "review":
            item = self.candidate_by_id[key]
            text = f"{item.path}\n{human_bytes(item.allocated_bytes)}\n{item.reason}"
        else:
            row = self.usage_by_id[key]
            text = f"{row.path}\n{human_bytes(row.allocated_bytes)}"
        self.push_screen(InfoScreen(text))

    def action_source(self) -> None:
        if not self.report:
            return
        category = self.report.categories
        if category:
            text = (
                f"System Data: {category.other_bytes} bytes\n"
                f"Source: {category.source}\n"
                f"Recorded: {category.timestamp}\n"
                f"Report started: {self.report.created_at}\n"
                f"Field: StorageLogInvestigation - Other\n"
                f"Recomputed residual: {category.residual_bytes} bytes\n"
                "A recorded native value, not instantaneous free space."
            )
        else:
            text = "Native System Data value unavailable. No substitute is invented."
        self.push_screen(InfoScreen(text))

    def action_help(self) -> None:
        self.push_screen(InfoScreen(HELP))

    def action_down(self) -> None:
        if self.stage == "menu":
            self.query_one("#menu", OptionList).action_cursor_down()
        elif self.stage in ("review", "status"):
            self.query_one("#results", DataTable).action_cursor_down()

    def action_up(self) -> None:
        if self.stage == "menu":
            self.query_one("#menu", OptionList).action_cursor_up()
        elif self.stage in ("review", "status"):
            self.query_one("#results", DataTable).action_cursor_up()

    def action_rescan(self) -> None:
        if self.mode in ("clean", "status"):
            self.choose(self.mode)

    def action_clean(self) -> None:
        self.choose("clean")

    def action_status(self) -> None:
        self.choose("status")

    async def action_quit(self) -> None:
        if self.stage == "deleting":
            return
        self.cancel_event.set()
        self.exit()

    def action_export(self) -> None:
        if self.report and not self.busy:
            try:
                path = self.home / ".local/state/jev-clean/latest-plan.json"
                save_plan(path, self.report)
                self.notify(f"Saved {path}")
            except Exception as error:
                self.notify(str(error), severity="error")

    def action_history(self) -> None:
        try:
            rows = TrashStore(self.home).history() if not self.demo else []
            text = (
                "\n".join(f"{r['id']} · {len(r['entries'])} files" for r in rows[:8]) or "No cleanup history."
            )
            self.push_screen(InfoScreen(text + "\n\njev-clean restore <id>"))
        except Exception as error:
            self.notify(str(error), severity="error")

    @work(thread=True)
    def action_update(self) -> None:
        try:
            result = check_update()
            text = f"{result['installed']} → {result['latest']}\n\njev-clean update --apply"
        except Exception as error:
            text = f"Update unavailable: {error}"
        self.call_from_thread(self.push_screen, InfoScreen(text))
