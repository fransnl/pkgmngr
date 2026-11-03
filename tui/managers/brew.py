from __future__ import annotations

from .base import Package, Source, run, which


class BrewSource(Source):
    key = "brew"
    title = "brew"
    note_label = "Type"

    def available(self) -> bool:
        return which("brew") is not None

    def list_packages(self) -> list[Package]:
        brew = which("brew") or "brew"
        packages = []
        for kind in ("formula", "cask"):
            for line in run([brew, "list", f"--{kind}", "--versions"]).splitlines():
                name, *versions = line.split()
                packages.append(Package(name, versions[-1] if versions else "", kind))
        return packages

    def info(self, package: Package) -> str:
        return run([which("brew") or "brew", "info", f"--{package.note}", package.name])
