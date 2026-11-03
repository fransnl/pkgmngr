# Architecture

```
tui/
├── __main__.py        python -m tui entry point
├── main.py            argument parsing, builds the app
├── app.py             Textual UI: tabs, tables, search box, info modal
├── fuzzy.py           fzf-style matcher used by the search box
└── managers/
    ├── __init__.py    all_sources() / discover_sources()
    ├── base.py        Package, Source, run(), CommandError, format_fields()
    ├── npm.py         NpmSource (global and local)
    ├── python.py      PythonSource (global and .venv)
    ├── brew.py        BrewSource
    ├── linux.py       AptSource, DnfSource, YaySource
    ├── flatpak.py     FlatpakSource
    ├── cargo.py       CargoSource
    └── winget.py      WingetSource
```

## Sources

A *source* is one tab in the UI. Every source subclasses `managers.base.Source` and provides:

| Member | Purpose |
| --- | --- |
| `key` | Unique id, used in widget ids (`table-<key>`, `status-<key>`, `pane-<key>`). |
| `title` | Tab label. |
| `note_label` | Optional header for a third table column. If empty, the table only has Name and Version. |
| `available()` | Cheap check (usually `shutil.which`) deciding whether the tab is shown. Must not run slow commands. |
| `list_packages()` | Returns `list[Package]`. Runs in a worker thread. Raise `CommandError` (or any exception) to show an error in the tab. |
| `info(package)` | Returns plain text for the info modal. Runs in a worker thread. |

`Package` has `name`, `version` and `note`. `note` fills the optional third column, and sources can also use it to carry data that `info()` needs later (brew stores `formula`/`cask`, flatpak stores kind/installation/branch, apt/dnf store the architecture, winget stores the package id).

Shell commands go through `managers.base.run()`. It resolves output as UTF-8, closes stdin, applies a timeout and turns failures into `CommandError`.

### Adding a package manager

1. Create a `Source` subclass in `tui/managers/`.
2. Add an instance to `all_sources()` in `tui/managers/__init__.py`.
3. Document it in [package-managers.md](package-managers.md) and the README.

## UI flow

1. `main.main()` resolves the project directory and calls `discover_sources()`, which keeps only sources whose `available()` is true.
2. `PackageManagerApp.compose()` creates a `TabPane` per source containing a status line and a `PackageTable` (a `DataTable` with vim bindings).
3. On mount, each source is loaded in its own thread worker (`group=load-<key>`, exclusive, so a refresh cancels a pending load). The results are handed back with `call_from_thread`.
4. `_render(key)` filters the source's packages with the current search query, rebuilds the table and updates the status line and tab label. It remembers the last query it rendered for each tab, so only the active tab is rebuilt while typing. Other tabs re-render when they are activated.
5. Row keys are indexes into `app.packages[key]`, so the selected row maps back to its `Package`.
6. Enter (on the table, or submitting the search box) pushes `InfoScreen`, which calls `source.info()` in a worker thread.

## Key handling

The UI is keyboard-only. `main.py` runs the app with `mouse=False`, and the app CSS sets `scrollbar-size: 0 0` on every widget, so nothing is drawn for the mouse. Scrollable widgets still scroll with their key bindings.

- `tab` / `shift+tab` are app bindings with `priority=True`, so they switch tabs even while the search box has focus, instead of moving focus.
- `SearchInput` binds up/down, ctrl+p/ctrl+n and page up/down to `app.move_cursor`, so you can move through results without leaving the search box, as in fzf.
- `escape` from the search box focuses the table. From the table it clears the query.
- `q`, `r` and `/` are normal (non-priority) bindings, so they are typed as text while the search box has focus.
