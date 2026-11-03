# Package managers

A tab is shown only when its manager is detected. "Directory" means the folder passed on the command line (default: the current folder).

| Tab | Shown when | List command | Info command |
| --- | --- | --- | --- |
| npm (global) | `npm` on PATH | `npm ls --depth=0 --json --global` | Reads `package.json` under `npm root --global`, otherwise `npm view <name>` |
| npm (local) | `npm` on PATH and the directory has `package.json` or `node_modules/` | `npm ls --depth=0 --json` in the directory | Reads `node_modules/<name>/package.json`, otherwise `npm view <name>` |
| Python (global) | A `python3`/`python` on PATH that is not inside a virtual environment | `importlib.metadata` script run by that interpreter | `importlib.metadata` script (summary, URLs, requirements, location) |
| Python (.venv) | `<directory>/.venv/bin/python` or `.venv\Scripts\python.exe` exists | Same script, run by the venv interpreter | Same |
| brew | `brew` on PATH | `brew list --formula --versions` and `brew list --cask --versions` | `brew info --formula\|--cask <name>` |
| apt | `apt` and `dpkg-query` on PATH | `dpkg-query --show` (only packages with status `ii`) | `dpkg-query --status <name>:<arch>` |
| dnf | `dnf` and `rpm` on PATH | `rpm --query --all` | `rpm --query --info <name>-<version>.<arch>` |
| yay | `yay` on PATH | `yay -Q`, with `yay -Qm` marking AUR packages | `yay -Qi <name>` |
| flatpak | `flatpak` on PATH | `flatpak list --app` and `flatpak list --runtime` with `--columns=application,version,branch,installation` | `flatpak info --user\|--system\|--installation=<name> <id> <branch>` |
| cargo | `cargo` on PATH | `cargo install --list` | Local data plus `cargo info <name>` (needs cargo 1.82+ and network access) |
| winget | `winget` on PATH | `winget list` (table output is parsed) | `winget show --id <id> --exact`, falling back to `winget show <name>` |

## Notes

- **Python** packages are read with `importlib.metadata` rather than `pip`, so environments without pip (for example ones created by `uv`) still work. The global interpreter is the first `python3`/`python` on PATH whose parent folder has no `pyvenv.cfg`. Entries under `WindowsApps` (the Microsoft Store alias) are skipped.
- **npm** exits with a non-zero code when the tree has problems (missing peer dependencies and similar) but still prints JSON, so its exit code is ignored. Packages flagged `missing`, `extraneous` or `invalid` are still listed.
- **dnf** listing uses `rpm` directly, because the `dnf list --installed` output format differs between dnf4 and dnf5.
- **flatpak** packages are listed by application id (for example `org.mozilla.firefox`). The third column holds the kind (`app`/`runtime`), installation and branch, which `info()` reads back to target the exact ref.
- **winget** has no machine-readable list output. The parser finds the header row above the `-----` separator line and slices columns at the header word positions. It expects single-word column headers (true for English output). winget may truncate long values with `…`. If the id is truncated, info falls back to a name search.
