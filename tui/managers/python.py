from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

from .base import CommandError, Package, Source, format_fields, run

LIST_SCRIPT = """
import json, importlib.metadata as m
seen = {}
for d in m.distributions():
    name = d.metadata["Name"]
    if name and name.lower() not in seen:
        seen[name.lower()] = [name, d.version]
print(json.dumps(list(seen.values())))
"""

INFO_SCRIPT = """
import json, sys, importlib.metadata as m
d = m.distribution(sys.argv[1])
md = d.metadata
names = ["Name", "Version", "Summary", "Home-page", "Author", "Author-email",
         "License", "Requires-Python"]
print(json.dumps({
    "fields": [[n, md[n]] for n in names if md[n]],
    "urls": md.get_all("Project-URL") or [],
    "requires": d.requires or [],
    "location": str(d.locate_file("")),
}))
"""


def _in_venv(executable: Path) -> bool:
    return (executable.parent.parent / "pyvenv.cfg").is_file()


def find_global_python() -> str | None:
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if not directory or "WindowsApps" in directory:
            continue
        for name in ("python3", "python"):
            candidate = shutil.which(name, path=directory)
            if candidate and not _in_venv(Path(candidate)):
                return candidate
    base = getattr(sys, "_base_executable", None)
    if base and Path(base).is_file() and not _in_venv(Path(base)):
        return base
    return None


def find_venv_python(directory: Path) -> str | None:
    venv = directory / ".venv"
    for candidate in (venv / "bin" / "python", venv / "Scripts" / "python.exe"):
        if candidate.is_file():
            return str(candidate)
    return None


class PythonSource(Source):
    def __init__(self, scope: str, directory: Path | None = None) -> None:
        self.scope = scope
        self.directory = directory
        self.key = f"python-{scope}"
        self.title = "Python (global)" if scope == "global" else "Python (.venv)"
        self._interpreter: str | None = None
        self._resolved = False

    @property
    def interpreter(self) -> str | None:
        if not self._resolved:
            if self.scope == "global":
                self._interpreter = find_global_python()
            elif self.directory is not None:
                self._interpreter = find_venv_python(self.directory)
            self._resolved = True
        return self._interpreter

    def available(self) -> bool:
        return self.interpreter is not None

    def _python(self, script: str, *args: str) -> object:
        assert self.interpreter is not None
        output = run([self.interpreter, "-c", script, *args])
        try:
            return json.loads(output)
        except json.JSONDecodeError as exc:
            raise CommandError(f"Could not parse output of {self.interpreter}: {exc}") from exc

    def list_packages(self) -> list[Package]:
        rows = self._python(LIST_SCRIPT)
        assert isinstance(rows, list)
        return [Package(name, version) for name, version in rows]

    def info(self, package: Package) -> str:
        data = self._python(INFO_SCRIPT, package.name)
        assert isinstance(data, dict)
        text = format_fields(
            [*map(tuple, data["fields"]), ("Location", data["location"]), ("Interpreter", self.interpreter)]
        )
        if data["urls"]:
            text += "\n\nProject URLs:\n" + "\n".join(f"  {url}" for url in data["urls"])
        if data["requires"]:
            text += f"\n\nRequires ({len(data['requires'])}):\n" + "\n".join(
                f"  {requirement}" for requirement in data["requires"]
            )
        return text
