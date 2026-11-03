from __future__ import annotations

from functools import partial
from pathlib import Path

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Header, Input, Static, TabbedContent, TabPane, Tabs

from .fuzzy import filter_items
from .managers import Package, Source

HIGHLIGHT = "bold #ffaf00"


class PackageTable(DataTable):
    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("g", "scroll_top", "Top", show=False),
        Binding("G", "scroll_bottom", "Bottom", show=False),
    ]


class SearchInput(Input):
    BINDINGS = [
        Binding("up", "app.move_cursor(-1)", "Up", show=False),
        Binding("down", "app.move_cursor(1)", "Down", show=False),
        Binding("ctrl+p", "app.move_cursor(-1)", "Up", show=False),
        Binding("ctrl+n", "app.move_cursor(1)", "Down", show=False),
        Binding("pageup", "app.move_cursor(-10)", "Page up", show=False),
        Binding("pagedown", "app.move_cursor(10)", "Page down", show=False),
    ]


class InfoScreen(ModalScreen[None]):
    BINDINGS = [
        Binding("escape,q,enter", "dismiss", "Close"),
        Binding("j", "scroll(1)", "Down", show=False),
        Binding("k", "scroll(-1)", "Up", show=False),
    ]

    DEFAULT_CSS = """
    InfoScreen {
        align: center middle;
    }
    InfoScreen #dialog {
        width: 90%;
        height: 85%;
        border: round $accent;
        background: $surface;
        padding: 0 1;
    }
    InfoScreen #info-title {
        text-style: bold;
        color: $accent;
        padding-bottom: 1;
    }
    InfoScreen #info-body {
        height: 1fr;
    }
    InfoScreen #info-help {
        color: $text-muted;
        padding-top: 1;
    }
    """

    def __init__(self, source: Source, package: Package) -> None:
        super().__init__()
        self.source = source
        self.package = package

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(f"{self.package.name} {self.package.version}  ·  {self.source.title}", id="info-title")
            with VerticalScroll(id="info-body"):
                yield Static("Loading…", id="info-text")
            yield Static("esc / q / enter  close    ↑ ↓ j k  scroll", id="info-help")

    def on_mount(self) -> None:
        self.query_one("#info-body").focus()
        self.run_worker(self._load, thread=True)

    def _load(self) -> None:
        try:
            text = Text(self.source.info(self.package).rstrip() or "No information available.")
        except Exception as exc:
            text = Text(f"Could not load package info:\n\n{exc}", style="red")
        self.app.call_from_thread(self.query_one("#info-text", Static).update, text)

    def action_scroll(self, lines: int) -> None:
        self.query_one("#info-body", VerticalScroll).scroll_relative(y=lines, animate=False)


class PackageManagerApp(App[None]):
    TITLE = "pkgmngr"

    CSS = """
    * {
        scrollbar-size: 0 0;
    }
    #search {
        margin: 0 1;
    }
    #tabs, #tabs ContentSwitcher, #tabs TabPane {
        height: 1fr;
    }
    #tabs TabPane {
        padding: 0;
    }
    .status {
        color: $text-muted;
        padding: 0 1;
    }
    .status.error {
        color: $error;
    }
    PackageTable {
        height: 1fr;
    }
    #empty {
        padding: 1 2;
    }
    """

    BINDINGS = [
        Binding("tab", "switch_tab(1)", "Next tab", priority=True),
        Binding("shift+tab", "switch_tab(-1)", "Prev tab", priority=True),
        Binding("slash", "focus_search", "Search"),
        Binding("escape", "escape", "Back", show=False),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, sources: list[Source], directory: Path) -> None:
        super().__init__()
        self.sources = {source.key: source for source in sources}
        self.directory = directory
        self.packages: dict[str, list[Package]] = {key: [] for key in self.sources}
        self.rendered_query: dict[str, str | None] = {key: None for key in self.sources}
        self.sub_title = str(directory)

    def compose(self) -> ComposeResult:
        yield Header()
        yield SearchInput(placeholder="Search  ( / to focus · 'exact ^prefix suffix$ !exclude )", id="search")
        if not self.sources:
            yield Static("No supported package managers were found on this system.", id="empty")
        with TabbedContent(id="tabs"):
            for key, source in self.sources.items():
                with TabPane(source.title, id=f"pane-{key}"):
                    yield Static("Loading…", classes="status", id=f"status-{key}")
                    yield PackageTable(id=f"table-{key}", cursor_type="row", zebra_stripes=True)
        yield Footer()

    def on_mount(self) -> None:
        for key, source in self.sources.items():
            table = self._table(key)
            table.add_column("Name", key="name")
            table.add_column("Version", key="version")
            if source.note_label:
                table.add_column(source.note_label, key="note")
            self._load(key)
        self._focus_table()

    def _table(self, key: str) -> PackageTable:
        return self.query_one(f"#table-{key}", PackageTable)

    def _status(self, key: str) -> Static:
        return self.query_one(f"#status-{key}", Static)

    def _active_key(self) -> str | None:
        if not self.sources:
            return None
        active = self.query_one("#tabs", TabbedContent).active
        return active.removeprefix("pane-") if active else None

    def _focus_table(self) -> None:
        key = self._active_key()
        if key:
            self._table(key).focus()

    def _load(self, key: str) -> None:
        status = self._status(key)
        status.remove_class("error")
        status.update("Loading…")
        self.run_worker(partial(self._fetch, key), thread=True, group=f"load-{key}", exclusive=True)

    def _fetch(self, key: str) -> None:
        try:
            packages = self.sources[key].list_packages()
        except Exception as exc:
            self.call_from_thread(self._show_error, key, exc)
        else:
            self.call_from_thread(self._set_packages, key, packages)

    def _show_error(self, key: str, error: Exception) -> None:
        self.packages[key] = []
        self.rendered_query[key] = None
        self._table(key).clear()
        status = self._status(key)
        status.add_class("error")
        status.update(Text(f"Failed to list packages: {error}"))

    def _set_packages(self, key: str, packages: list[Package]) -> None:
        self.packages[key] = packages
        self.rendered_query[key] = None
        self._render(key)

    def _render(self, key: str) -> None:
        query = self.query_one("#search", SearchInput).value
        if self.rendered_query[key] == query:
            return
        self.rendered_query[key] = query
        source = self.sources[key]
        packages = self.packages[key]
        index = {id(package): position for position, package in enumerate(packages)}
        results = filter_items(query, packages, lambda package: package.name)
        table = self._table(key)
        table.clear()
        for package, positions in results:
            name = Text(package.name)
            for position in positions:
                name.stylize(HIGHLIGHT, position, position + 1)
            cells = [name, package.version]
            if source.note_label:
                cells.append(package.note)
            table.add_row(*cells, key=str(index[id(package)]))
        total = len(packages)
        shown = len(results)
        noun = "package" if total == 1 else "packages"
        self._status(key).update(f"{shown} of {total} {noun}" if query.strip() else f"{total} {noun}")
        tab = self.query_one("#tabs", TabbedContent).get_tab(f"pane-{key}")
        tab.label = f"{source.title} ({total})"

    def on_input_changed(self, event: Input.Changed) -> None:
        key = self._active_key()
        if key:
            self._render(key)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._open_selected()

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        key = self._active_key()
        if key:
            self._render(key)
        if not isinstance(self.focused, SearchInput):
            self._focus_table()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self._open_selected()

    def _open_selected(self) -> None:
        key = self._active_key()
        if not key:
            return
        table = self._table(key)
        if table.row_count == 0:
            return
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        package = self.packages[key][int(row_key.value)]
        self.push_screen(InfoScreen(self.sources[key], package))

    def action_switch_tab(self, step: int) -> None:
        if not self.sources or isinstance(self.screen, ModalScreen):
            return
        tabs = self.query_one("#tabs", TabbedContent).query_one(Tabs)
        if step > 0:
            tabs.action_next_tab()
        else:
            tabs.action_previous_tab()

    def action_move_cursor(self, step: int) -> None:
        key = self._active_key()
        if key:
            table = self._table(key)
            if table.row_count:
                row = min(max(table.cursor_row + step, 0), table.row_count - 1)
                table.move_cursor(row=row)

    def action_focus_search(self) -> None:
        self.query_one("#search", SearchInput).focus()

    def action_escape(self) -> None:
        search = self.query_one("#search", SearchInput)
        if self.focused is search:
            self._focus_table()
        elif search.value:
            search.value = ""

    def action_refresh(self) -> None:
        key = self._active_key()
        if key:
            self._load(key)
