from __future__ import annotations

import re

from .base import CommandError, Package, Source, format_fields, run, which

HEADER = re.compile(r"^(\S+) v(\S+?)(?: \((.+)\))?:$")


class CargoSource(Source):
    key = "cargo"
    title = "cargo"
    note_label = "Binaries"

    def __init__(self) -> None:
        self._origins: dict[str, str] = {}

    def available(self) -> bool:
        return which("cargo") is not None

    def list_packages(self) -> list[Package]:
        packages: list[Package] = []
        binaries: dict[str, list[str]] = {}
        for line in run([which("cargo") or "cargo", "install", "--list"]).splitlines():
            match = HEADER.match(line)
            if match:
                name, version, origin = match.groups()
                packages.append(Package(name, version))
                binaries[name] = []
                self._origins[name] = origin or "crates.io"
            elif line.startswith((" ", "\t")) and packages:
                binaries[packages[-1].name].append(line.strip())
        for package in packages:
            package.note = ", ".join(binaries[package.name])
        return packages

    def info(self, package: Package) -> str:
        local = format_fields(
            [
                ("Name", package.name),
                ("Version", package.version),
                ("Source", self._origins.get(package.name)),
                ("Binaries", package.note),
            ]
        )
        try:
            remote = run([which("cargo") or "cargo", "info", package.name], timeout=30)
        except CommandError as exc:
            remote = f"cargo info unavailable: {exc}"
        return f"{local}\n\n{remote}"
