from __future__ import annotations

import re

from .base import CommandError, Package, Source, run, which

COLUMN = re.compile(r"\S+")
ELLIPSIS = "…"


def _clean(line: str) -> str:
    return line.rstrip().rsplit("\r", 1)[-1]


def parse_table(output: str) -> list[Package]:
    lines = [_clean(line) for line in output.split("\n")]
    for index in range(len(lines) - 1):
        separator = lines[index + 1]
        if lines[index].strip() and len(separator) >= 10 and set(separator) == {"-"}:
            header = lines[index]
            break
    else:
        return []
    starts = [match.start() for match in COLUMN.finditer(header)]
    if len(starts) < 3:
        return []
    packages = []
    for line in lines[index + 2 :]:
        if not line.strip():
            continue
        cells = [
            line[start : starts[position + 1] if position + 1 < len(starts) else None].strip()
            for position, start in enumerate(starts)
        ]
        name, identifier, version = cells[0], cells[1], cells[2]
        source = cells[-1] if len(cells) > 3 else ""
        if name:
            packages.append(Package(name, version, " / ".join(filter(None, [identifier, source]))))
    return packages


class WingetSource(Source):
    key = "winget"
    title = "winget"
    note_label = "Id / Source"

    def available(self) -> bool:
        return which("winget") is not None

    def list_packages(self) -> list[Package]:
        output = run(
            [
                which("winget") or "winget",
                "list",
                "--accept-source-agreements",
                "--disable-interactivity",
            ]
        )
        return parse_table(output)

    def info(self, package: Package) -> str:
        winget = which("winget") or "winget"
        identifier = package.note.split(" / ")[0]
        if identifier and not identifier.endswith(ELLIPSIS):
            try:
                return run([winget, "show", "--id", identifier, "--exact", "--accept-source-agreements", "--disable-interactivity"])
            except CommandError:
                pass
        return run([winget, "show", package.name.rstrip(ELLIPSIS), "--accept-source-agreements", "--disable-interactivity"])
