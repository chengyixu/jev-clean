"""Keyboard/list equivalent for every treemap block, including zero/unknown sizes."""

from __future__ import annotations

from rich.cells import cell_len
from rich.segment import Segment
from rich.style import Style
from rich.text import Text
from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import OptionList, Static

from jev_clean.domain.models import human_bytes
from jev_clean.domain.storage_map import MapEntry, Tile, layout_tiles

NORMAL = Style(color="#e7edf2", bgcolor="#273b4b")
RECOMMENDED = Style(color="#ffffff", bgcolor="#1e5949")
SELECTED = Style(color="#ffffff", bgcolor="#735526")
BORDER = Style(color="#8695a0", bgcolor="#1b252d")
FOCUS = Style(color="#ffffff", bgcolor="#1b252d", bold=True)


class TreemapCanvas(Widget):
    DEFAULT_CSS = """
    TreemapCanvas { width: 1fr; height: 1fr; background: #171717; }
    """

    class Opened(Message):
        def __init__(self, entry: MapEntry):
            super().__init__()
            self.entry = entry

    def __init__(self):
        super().__init__(id="treemap")
        self.entries: list[MapEntry] = []
        self.tiles: list[Tile] = []
        self.hit_tiles: list[Tile] = []
        self.selected: set[str] = set()
        self.highlighted = ""
        self._map_lines: list[Strip] = []
        self._map_size = (-1, -1)

    def update_map(self, entries: list[MapEntry], selected: set[str], highlighted: str) -> None:
        self.entries, self.selected, self.highlighted = entries, set(selected), highlighted
        self._map_size = (-1, -1)
        self.refresh()

    def _build(self) -> None:
        width, height = self.size.width, self.size.height
        self._map_size = (width, height)
        self.tiles = layout_tiles(self.entries, width, height)
        self.hit_tiles = []
        chars = [[" " for _ in range(width)] for _ in range(height)]
        styles = [[Style(color="#999999", bgcolor="#171717") for _ in range(width)] for _ in range(height)]

        def label(text: str, x: int, y: int, max_width: int, style: Style):
            if not 0 <= y < height or max_width <= 0:
                return
            t = Text(text)
            t.truncate(max_width, overflow="ellipsis")
            pos = x
            for char in t.plain:
                n = cell_len(char)
                if n == 0:
                    continue
                if pos + n > min(width, x + max_width):
                    break
                chars[y][pos], styles[y][pos] = char, style
                for offset in range(1, n):
                    chars[y][pos + offset], styles[y][pos + offset] = "", style
                pos += n

        def paint(tile: Tile, depth: int):
            e, x, y, w, h = tile.entry, tile.x, tile.y, tile.width, tile.height
            self.hit_tiles.append(tile)
            selected = bool(e.candidate_id and e.candidate_id in self.selected)
            # Organizational categories are not uniformly painted as disposable.
            body = SELECTED if selected else RECOMMENDED if e.recommended and e.candidate_id else NORMAL
            edge = FOCUS if e.id == self.highlighted else BORDER
            for row in range(y, y + h):
                for col in range(x, x + w):
                    styles[row][col] = body
                    if w >= 3 and h >= 3 and (row in (y, y + h - 1) or col in (x, x + w - 1)):
                        chars[row][col] = "─" if row in (y, y + h - 1) else "│"
                        styles[row][col] = edge
            if w >= 3 and h >= 3:
                chars[y][x], chars[y][x + w - 1], chars[y + h - 1][x], chars[y + h - 1][x + w - 1] = (
                    "┌",
                    "┐",
                    "└",
                    "┘",
                )
            pad = 1 if w >= 3 else 0
            title_y = y + (1 if h >= 3 else 0)
            marker = (
                "[x] " if selected else "◆ " if e.recommended else "◇ " if e.contains_recommendations else ""
            )
            label(marker + e.label, x + pad, title_y, w - 2 * pad, body + Style(bold=True))
            if h >= 4:
                label(
                    human_bytes(e.allocated_bytes)
                    + ("+" if not e.complete and e.basis != "recorded macOS total" else ""),
                    x + pad,
                    title_y + 1,
                    w - 2 * pad,
                    body,
                )
            if e.children and e.basis != "recorded macOS total" and depth < 2 and w >= 10 and h >= 7:
                for inner in layout_tiles(e.children, w - 2, h - 4):
                    paint(
                        Tile(inner.entry, inner.x + x + 1, inner.y + y + 3, inner.width, inner.height),
                        depth + 1,
                    )

        for tile in self.tiles:
            paint(tile, 0)
        if not self.tiles:
            label("No measured area. Use the list to explore.", 0, height // 2, width, Style(color="#aaaaaa"))
        self._map_lines = []
        for row, row_styles in zip(chars, styles, strict=True):
            segments: list[Segment] = []
            for char, style in zip(row, row_styles, strict=True):
                if segments and segments[-1].style == style:
                    last = segments.pop()
                    segments.append(Segment(last.text + char, style))
                else:
                    segments.append(Segment(char, style))
            self._map_lines.append(Strip(segments, width))

    def render_line(self, y: int) -> Strip:
        if self._map_size != (self.size.width, self.size.height):
            self._build()
        return self._map_lines[y] if 0 <= y < len(self._map_lines) else Strip.blank(self.size.width)

    def on_click(self, event: events.Click) -> None:
        for tile in reversed(self.hit_tiles):
            if tile.contains(event.x, event.y):
                self.post_message(self.Opened(tile.entry))
                event.stop()
                break


class StorageMap(Widget):
    DEFAULT_CSS = """
    StorageMap { height: 1fr; }
    #map-body { height: 1fr; }
    #map-list { width: 28; max-width: 40%; height: 1fr; border: none; background: #171717; padding: 0; }
    #map-list > .option-list--option-highlighted { background: #303d47; color: #ffffff; }
    #map-legend { height: 1; color: #aaaaaa; }
    """

    class Navigated(Message):
        pass

    class InspectPath(Message):
        def __init__(self, entry: MapEntry):
            super().__init__()
            self.entry = entry

    def __init__(self):
        super().__init__(id="storage-map")
        self.root = MapEntry("disk", "Storage", None)
        self.current = self.root
        self.stack: list[MapEntry] = []
        self.selected: set[str] = set()
        self.visible_entries: list[MapEntry] = []
        self.query_text = ""

    def compose(self) -> ComposeResult:
        with Horizontal(id="map-body"):
            yield OptionList(id="map-list")
            yield TreemapCanvas()
        yield Static(
            Text("◆ recommended   ◇ contains recommendations   [x] selected"),
            id="map-legend",
            markup=False,
            expand=True,
        )

    @property
    def breadcrumb(self) -> str:
        return " › ".join(e.label for e in [*self.stack, self.current])

    @property
    def focused_entry(self) -> MapEntry | None:
        index = self.query_one("#map-list", OptionList).highlighted
        return (
            self.visible_entries[index] if index is not None and index < len(self.visible_entries) else None
        )

    def set_root(self, root: MapEntry, selected: set[str], query: str = "") -> None:
        ids = [e.id for e in [*self.stack, self.current]][1:]
        self.root, self.current, self.stack = root, root, []
        for entry_id in ids:
            child = next((c for c in self.current.children if c.id == entry_id), None)
            if child is None:
                break
            self.stack.append(self.current)
            self.current = child
        self.selected, self.query_text = set(selected), query.casefold()
        self.refresh_view()

    def refresh_view(self) -> None:
        options = self.query_one("#map-list", OptionList)
        old = options.highlighted or 0
        self.visible_entries = [
            e
            for e in self.current.children
            if not self.query_text or self.query_text in (e.label + e.path).casefold()
        ]
        options.clear_options()
        for e in self.visible_entries:
            marker = (
                "[x]"
                if e.candidate_id in self.selected
                else "◆"
                if e.recommended
                else "◇"
                if e.contains_recommendations
                else " "
            )
            amount = human_bytes(e.allocated_bytes) if e.allocated_bytes is not None else "unavailable"
            style = (
                "#ffffff on #735526"
                if e.candidate_id in self.selected
                else "#ffffff on #1e5949"
                if e.recommended
                else "#dedede"
            )
            options.add_option(
                Text(
                    f"{marker} {e.label}\n  {amount}"
                    + ("+" if not e.complete and e.basis != "recorded macOS total" else ""),
                    style=style,
                )
            )
        options.highlighted = min(old, len(self.visible_entries) - 1) if self.visible_entries else None
        self.update_canvas()

    def update_canvas(self) -> None:
        entry = self.focused_entry
        self.query_one(TreemapCanvas).update_map(
            self.visible_entries, self.selected, entry.id if entry else ""
        )

    @on(OptionList.OptionHighlighted, "#map-list")
    def highlighted(self) -> None:
        self.update_canvas()

    @on(OptionList.OptionSelected, "#map-list")
    def selected_option(self, event: OptionList.OptionSelected) -> None:
        if self.focused_entry:
            self.open_entry(self.focused_entry)
        event.stop()

    @on(TreemapCanvas.Opened)
    def clicked(self, event: TreemapCanvas.Opened) -> None:
        self.open_entry(event.entry)
        event.stop()

    def open_path(self, path: str) -> None:
        """Enter a newly inventoried descendant, including nested preview targets."""
        pending = list(self.current.children)
        while pending:
            entry = pending.pop()
            if entry.path == path:
                if entry.children:
                    self.open_entry(entry)
                return
            pending.extend(entry.children)

    def open_entry(self, entry: MapEntry) -> None:
        def route(parent: MapEntry) -> list[MapEntry] | None:
            for child in parent.children:
                if child.id == entry.id:
                    return [child]
                nested = route(child)
                if nested:
                    return [child, *nested]
            return None

        chain = route(self.current)
        if chain and len(chain) > 1:
            for ancestor in chain[:-1]:
                self.stack.append(self.current)
                self.current = ancestor
        if entry.children:
            self.stack.append(self.current)
            self.current = entry
            self.query_text = ""
            self.query_one("#map-list", OptionList).highlighted = 0
            self.refresh_view()
            self.post_message(self.Navigated())
        elif entry.path and entry.is_dir:
            self.post_message(self.InspectPath(entry))
        elif entry.path:
            self.post_message(self.InspectPath(entry))
        else:
            self.notify("No observed paths attributed to this category.")

    def back(self) -> bool:
        if not self.stack:
            return False
        self.current = self.stack.pop()
        self.query_text = ""
        self.refresh_view()
        self.post_message(self.Navigated())
        return True
