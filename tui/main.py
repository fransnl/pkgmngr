from __future__ import annotations

import argparse
from pathlib import Path

from .app import PackageManagerApp
from .managers import discover_sources


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pkgmngr",
        description="Browse packages installed by every package manager on this system.",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="project folder used for local npm packages and .venv (default: current folder)",
    )
    args = parser.parse_args(argv)
    directory = Path(args.directory).expanduser().resolve()
    if not directory.is_dir():
        parser.error(f"not a directory: {directory}")
    PackageManagerApp(discover_sources(directory), directory).run(mouse=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
