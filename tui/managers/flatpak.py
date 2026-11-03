from __future__ import annotations

from .base import Package, Source, run, which

SEPARATOR = " / "


class FlatpakSource(Source):
    key = "flatpak"
    title = "flatpak"
    note_label = "Type / Installation / Branch"

    def available(self) -> bool:
        return which("flatpak") is not None

    def list_packages(self) -> list[Package]:
        flatpak = which("flatpak") or "flatpak"
        packages = []
        for kind in ("app", "runtime"):
            output = run([flatpak, "list", f"--{kind}", "--columns=application,version,branch,installation"])
            for line in output.splitlines():
                parts = line.split("\t")
                if len(parts) == 4 and parts[0]:
                    application, version, branch, installation = (part.strip() for part in parts)
                    packages.append(Package(application, version, SEPARATOR.join([kind, installation, branch])))
        return packages

    def info(self, package: Package) -> str:
        _, installation, branch = package.note.split(SEPARATOR)
        if installation in ("user", "system"):
            scope = f"--{installation}"
        else:
            scope = f"--installation={installation}"
        return run([which("flatpak") or "flatpak", "info", scope, package.name, branch])
