from __future__ import annotations

import json
from pathlib import Path

from .base import CommandError, Package, Source, format_fields, run, which


class NpmSource(Source):
    def __init__(self, scope: str, directory: Path | None = None) -> None:
        self.scope = scope
        self.directory = directory
        self.key = f"npm-{scope}"
        self.title = "npm (global)" if scope == "global" else "npm (local)"

    @property
    def is_global(self) -> bool:
        return self.scope == "global"

    def _npm(self, *args: str) -> list[str]:
        command = [which("npm") or "npm", *args]
        if self.is_global:
            command.append("--global")
        return command

    def available(self) -> bool:
        if not which("npm"):
            return False
        if self.is_global:
            return True
        assert self.directory is not None
        return (self.directory / "package.json").is_file() or (
            self.directory / "node_modules"
        ).is_dir()

    def list_packages(self) -> list[Package]:
        output = run(self._npm("ls", "--depth=0", "--json"), cwd=self.directory, check=False)
        try:
            data = json.loads(output or "{}")
        except json.JSONDecodeError as exc:
            raise CommandError(f"Could not parse npm output: {exc}") from exc
        packages = []
        for name, details in (data.get("dependencies") or {}).items():
            flags = [flag for flag in ("missing", "extraneous", "invalid") if details.get(flag)]
            packages.append(Package(name, details.get("version", ""), ", ".join(flags)))
        return packages

    def _root(self) -> Path:
        if self.is_global:
            return Path(run(self._npm("root"), cwd=self.directory).strip())
        assert self.directory is not None
        return self.directory / "node_modules"

    def info(self, package: Package) -> str:
        location = self._root() / package.name
        manifest_path = location / "package.json"
        if not manifest_path.is_file():
            return run([which("npm") or "npm", "view", package.name], cwd=self.directory)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        repository = manifest.get("repository")
        if isinstance(repository, dict):
            repository = repository.get("url")
        author = manifest.get("author")
        if isinstance(author, dict):
            author = author.get("name")
        dependencies = manifest.get("dependencies") or {}
        fields = format_fields(
            [
                ("Name", manifest.get("name")),
                ("Version", manifest.get("version")),
                ("Description", manifest.get("description")),
                ("License", manifest.get("license")),
                ("Author", author),
                ("Homepage", manifest.get("homepage")),
                ("Repository", repository),
                ("Location", location),
                ("Binaries", ", ".join(_binaries(manifest))),
            ]
        )
        if dependencies:
            listing = "\n".join(f"  {name} {spec}" for name, spec in sorted(dependencies.items()))
            fields += f"\n\nDependencies ({len(dependencies)}):\n{listing}"
        return fields


def _binaries(manifest: dict) -> list[str]:
    binaries = manifest.get("bin")
    if isinstance(binaries, dict):
        return sorted(binaries)
    if isinstance(binaries, str):
        return [manifest.get("name", "").split("/")[-1]]
    return []
