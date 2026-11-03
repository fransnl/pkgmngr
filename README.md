# pkgmngr

A terminal UI for macOS, Windows and Linux that collects the packages installed by every package manager on your system and shows each manager in its own tab.

## Supported package managers

| Tab | Source |
| --- | --- |
| npm (global) / npm (local) | Global npm packages, and packages in the project folder's `node_modules` |
| Python (global) / Python (.venv) | The Python on your PATH, and the project folder's `.venv` |
| brew | Formulae and casks |
| apt, dnf, yay | Linux system packages (yay marks AUR packages) |
| flatpak | Flatpak apps and runtimes, from both user and system installations |
| cargo | Binaries installed with `cargo install` |
| winget | Windows packages |

A tab only appears if its package manager is found. Each tab loads in the background, so slow managers don't block the UI.

## Install

Requires Python 3.10+ and [pipx](https://pipx.pypa.io). Run this from the repository root to install `pkgmngr` globally. pipx gives it an isolated environment and puts the `pkgmngr` command on your PATH:

```sh
pipx install .
```

To update after pulling changes, run `pipx install --force .`. To uninstall, run `pipx uninstall pkgmngr`.

## Usage

Run `pkgmngr` from any folder:

```sh
pkgmngr                   # use the current folder for local npm / .venv packages
pkgmngr path/to/project   # use another folder for local npm / .venv packages
```

## Keyboard shortcuts

The TUI is keyboard-only. Mouse input is turned off and no scrollbars are drawn.

| Key | Action |
| --- | --- |
| `Tab` / `Shift+Tab` | Next / previous package manager tab |
| `↓` `↑` or `j` `k` | Move through the package list |
| `g` / `G` | Jump to top / bottom |
| `Enter` | Show info about the selected package |
| `/` | Focus the search box |
| `↑` `↓`, `Ctrl+P` `Ctrl+N` (in search) | Move the selection without leaving the search box |
| `Enter` (in search) | Show info about the selected package |
| `Esc` | Leave the search box; press again to clear the search |
| `r` | Reload the current tab |
| `q` | Close the info view, or quit |

## Search

The search is fuzzy, like fzf: typing `txl` matches `textual`, and matched letters are highlighted. Results are ranked by match quality. fzf's extended syntax also works:

| Term | Meaning |
| --- | --- |
| `'abc` | Exact substring |
| `^abc` | Starts with |
| `abc$` | Ends with |
| `!abc` | Exclude |

Separate terms with spaces to combine them. For example, `^py !test` lists packages starting with "py" but not containing "test".

## Documentation

- [docs/architecture.md](docs/architecture.md): code layout, and how to add a package manager
- [docs/package-managers.md](docs/package-managers.md): the commands each tab runs
- [docs/search.md](docs/search.md): search syntax and ranking
