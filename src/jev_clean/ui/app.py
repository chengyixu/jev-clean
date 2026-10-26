"""Minimal sequential terminal: choose → logs → model judgments → human selection."""

from __future__ import annotations

import threading
import warnings
from pathlib import Path

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Input, OptionList, RichLog, Static

from jev_clean.application.service import audit, execute_selection, merge_status, prepare_selection, save_plan
from jev_clean.domain.models import AuditReport, Candidate, human_bytes, ordered_candidates
from jev_clean.domain.storage_map import recommended_ids, storage_map, toggle_selection
from jev_clean.infrastructure import native
from jev_clean.infrastructure.trash import TrashStore
from jev_clean.infrastructure.update import check_update
from jev_clean.ui.screens import ConfirmScreen, DepthScreen, InfoScreen
from jev_clean.ui.storage_map import StorageMap

HELP = """1 Clean    2 Status
↑↓ / j k   Move    Space select    A all    N none
Enter      Delete / open directory    Esc back
Status     Click/Enter drill down · A recommendations · D review selection
/ filter   I file details   S number source   R rescan
E export   H history   U update
Q quit

Select items with Space, then Enter to confirm moving them to Trash.
Technical details are available in the JSON export."""


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
            ("a,A", "all", "All"),
            ("n", "none", "None"),
            ("enter", "review", "Review"),
            ("d", "delete_selection", "Review selection"),
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
        self.expanding: str | None = None
        self.busy = False
        self.cancel_event = threading.Event()
        self.scope: list[Path] | None = None
        self.deep = False

    def compose(self) -> ComposeResult:
        yield Static("jev-clean", id="title", markup=False)
        yield OptionList("1. Clean", "2. Status", id="menu")
        yield Static("", id="summary", markup=False)
        yield RichLog(id="trace", markup=False, wrap=True, auto_scroll=True, max_lines=500)
        yield Input(placeholder="Filter", id="search")
        yield DataTable(id="results", show_header=False, cursor_type="row")
        yield StorageMap()
        yield Static("↑↓ Enter · q quit", id="hint", markup=False)

    def on_mount(self) -> None:
        self.show_stage("menu")
        if self.initial:
            self.choose(self.initial)

    def show_stage(self, stage: str) -> None:
        self.stage = stage
        self.query_one("#menu").display = stage == "menu"
        self.query_one("#trace").display = stage in ("running", "preparing", "deleting", "error")
        self.query_one("#results").display = stage == "review"
        self.query_one(StorageMap).display = stage == "status"
        self.query_one("#search").display = False
        self.query_one("#summary").display = stage not in ("menu", "running", "preparing", "deleting")
        self.query_one("#title", Static).update(
            "jev-clean" if stage == "menu" else self.mode.title() + (" (demo)" if self.demo else "")
        )
        hints = {
            "menu": "↑↓ Enter · q quit",
            "running": "Esc cancel",
            "preparing": "Checking selected resource contents…",
            "deleting": "Finishing…",
            "review": "Space select · a all · Enter delete · Esc back",
            "status": "Click/Enter open · Space select · a recommended · d review · Esc back",
            "error": "Esc back",
            "done": "Esc back",
        }
        self.query_one("#hint", Static).update(hints.get(stage, "Esc back"))
        if stage == "menu":
            self.query_one("#menu", OptionList).focus()
        elif stage == "status":
            self.query_one("#map-list", OptionList).focus()
        elif stage == "review":
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
        self.expanding = None
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
        expanded = self.expanding
        if expanded and self.report:
            report = merge_status(self.report, report, expanded)
            self.expanding = None
        else:
            self.query_one(StorageMap).stack = []
            self.query_one(StorageMap).current = self.query_one(StorageMap).root
        self.report = report
        self.candidate_by_id = {c.id: c for c in report.scan.candidates}
        self.selected.intersection_update(
            c.id for c in report.scan.candidates if c.selectable and c.operation == "trash"
        )
        self.render_report()
        if expanded:
            view = self.query_one(StorageMap)
            view.open_path(expanded)
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
            approved = [
                c
                for c in ordered_candidates(report.scan.candidates)
                if c.selectable and c.operation == "trash"
            ]
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
            if approved:
                proposed_bytes = sum(c.allocated_bytes for c in approved)
                summary = f"{len(self.selected)}/{len(approved)} selected · {human_bytes(size)} · {human_bytes(proposed_bytes)} proposed"
            else:
                summary = "No items to select."
            self.query_one("#summary").styles.max_height = 3
            if report.categories:
                recorded = report.categories.timestamp.split(" ")[1].split(".")[0]
                label = "demo" if report.demo else "macOS log " + recorded
                summary += f" | System Data {human_bytes(report.categories.other_bytes)} ({label})"

        else:
            view = self.query_one(StorageMap)
            view.set_root(storage_map(report), self.selected, query)
            summary = self.status_summary()
        self.query_one("#summary", Static).update(summary)

    def status_summary(self) -> str:
        view = self.query_one(StorageMap)
        size = sum(
            self.candidate_by_id[i].allocated_bytes for i in self.selected if i in self.candidate_by_id
        )
        basis = (
            "Observed allocations · estimated category paths"
            if view.current.id != "disk"
            else (
                "Synthetic category totals · not your Mac"
                if self.report and self.report.demo
                else f"macOS log {self.report.categories.timestamp.split('.')[0]} · paths are estimates"
                if self.report and self.report.categories
                else "Observed allocations · estimated categories"
            )
        )
        return f"{view.breadcrumb}\n{basis} · {len(self.selected)} selected · {human_bytes(size)}"

    @on(StorageMap.Navigated)
    def map_navigated(self) -> None:
        if self.report and self.is_running and self.query("#summary"):
            self.query_one("#summary", Static).update(self.status_summary())

    @on(StorageMap.InspectPath)
    def map_inspect(self, event: StorageMap.InspectPath) -> None:
        entry = event.entry
        if self.busy or not self.report:
            return
        item = self.candidate_by_id.get(entry.candidate_id)
        if not entry.is_dir and item and item.selectable and item.operation == "trash":
            self.selected = toggle_selection(self.selected, item, list(self.candidate_by_id.values()))
            self.render_report()
        elif entry.is_dir and not self.demo:
            self.expanding = entry.path
            self.scope = [Path(entry.path)]
            self.start_scan(False)
        else:
            item = self.candidate_by_id.get(entry.candidate_id)
            text = f"{entry.path}\n{human_bytes(entry.allocated_bytes)}\n{entry.basis}"
            if item:
                text += f"\nLaya: {item.decision.choice if item.decision else 'unknown'} · {item.reason}"
            self.push_screen(InfoScreen(text))

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
        if self.busy:
            return
        if self.stage == "status":
            entry = self.query_one(StorageMap).focused_entry
            item = self.candidate_by_id.get(entry.candidate_id) if entry else None
            if item:
                self.selected = toggle_selection(self.selected, item, list(self.candidate_by_id.values()))
                self.render_report()
            return
        if self.stage != "review":
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
        if self.stage == "status" and not self.busy:
            self.selected = recommended_ids(list(self.candidate_by_id.values()))
            self.render_report()
        elif self.stage == "review" and not self.busy:
            query = self.query_one("#search", Input).value.casefold()
            self.selected.update(
                c.id
                for c in self.candidate_by_id.values()
                if c.selectable and c.operation == "trash" and query in c.path.casefold()
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
            if not self.demo and any(i.unit == "directory" for i in items):
                self.busy = True
                self.show_stage("preparing")
                self.prepare_worker(items)
            else:
                self.present_confirmation(items)
        elif self.stage == "status" and self.report:
            view = self.query_one(StorageMap)
            if view.focused_entry:
                view.open_entry(view.focused_entry)

    def action_delete_selection(self) -> None:
        if self.stage != "status" or self.busy or not self.selected:
            return
        items = [self.candidate_by_id[i] for i in self.selected]
        if not self.demo and any(i.unit == "directory" for i in items):
            self.busy = True
            self.show_stage("preparing")
            self.prepare_worker(items)
        else:
            self.present_confirmation(items)

    @work(thread=True)
    def prepare_worker(self, items: list[Candidate]) -> None:
        try:
            sealed = prepare_selection(items, home=self.home)
            self.call_from_thread(self.present_confirmation, sealed)
        except Exception as error:
            self.call_from_thread(self.scan_failed, str(error))

    def present_confirmation(self, items: list[Candidate]) -> None:
        self.busy = False
        if self.cancel_event.is_set():
            self.selected.clear()
            self.show_stage("menu")
            return
        for item in items:
            self.candidate_by_id[item.id] = item
        self.show_stage("review" if self.mode == "clean" else "status")
        self.push_screen(ConfirmScreen(items), lambda yes: self.move_selected(items) if yes else None)

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
            result = execute_selection(items, home=self.home)
            text = f"{result.completed} items cleaned."
            if result.failed:
                text += f" {len(result.failed)} skipped."
            if result.batch_id:
                self.call_from_thread(self.trace, f"Undo Trash items: jev-clean restore {result.batch_id}")
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
            self.query_one("#map-list", OptionList).focus() if self.stage == "status" else self.query_one(
                "#results", DataTable
            ).focus()
        elif self.stage == "status" and self.query_one(StorageMap).back():
            self.query_one("#search", Input).value = ""
        else:
            self.report = None
            self.selected.clear()
            self.show_stage("menu")

    def action_search(self) -> None:
        if self.stage in ("review", "status"):
            self.query_one("#search").display = True
            self.query_one("#search", Input).focus()

    def action_details(self) -> None:
        if self.stage == "status":
            entry = self.query_one(StorageMap).focused_entry
            if entry:
                text = f"{entry.path or entry.label}\n{human_bytes(entry.allocated_bytes)}\n{entry.basis}\nEstimated namespace group, not proven Apple per-file membership."
                item = self.candidate_by_id.get(entry.candidate_id)
                if item:
                    text += f"\nLaya: {item.decision.choice if item.decision else 'unknown'} · {item.reason}"
                self.push_screen(InfoScreen(text))
            return
        table = self.query_one("#results", DataTable)
        if self.stage != "review" or not table.row_count:
            return
        key = str(table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value)
        item = self.candidate_by_id[key]
        self.push_screen(InfoScreen(f"{item.path}\n{human_bytes(item.allocated_bytes)}\n{item.reason}"))

    def action_source(self) -> None:
        if not self.report:
            return
        category = self.report.categories
        if category:
            text = (
                f"System Data: {category.other_bytes} bytes\n"
                f"Source: {category.source}\n"
                f"Recorded: {category.timestamp}\n"
                f"Review created: {self.report.created_at}\n"
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
        elif self.stage == "status":
            self.query_one("#map-list", OptionList).action_cursor_down()
        elif self.stage == "review":
            self.query_one("#results", DataTable).action_cursor_down()

    def action_up(self) -> None:
        if self.stage == "menu":
            self.query_one("#menu", OptionList).action_cursor_up()
        elif self.stage == "status":
            self.query_one("#map-list", OptionList).action_cursor_up()
        elif self.stage == "review":
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
