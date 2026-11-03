from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


class CommandError(RuntimeError):
    pass


@dataclass
class Package:
    name: str
    version: str
    note: str = ""


def which(name: str) -> str | None:
    return shutil.which(name)


def run(
    args: Sequence[str],
    cwd: Path | None = None,
    timeout: float = 120,
    check: bool = True,
) -> str:
    try:
        proc = subprocess.run(
            list(args),
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            stdin=subprocess.DEVNULL,
        )
    except FileNotFoundError as exc:
        raise CommandError(f"Command not found: {args[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise CommandError(f"Timed out after {timeout:.0f}s: {' '.join(args)}") from exc
    if check and proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip()
        raise CommandError(message or f"{args[0]} exited with code {proc.returncode}")
    return proc.stdout


def format_fields(fields: Iterable[tuple[str, object]]) -> str:
    rows = [(key, str(value)) for key, value in fields if value not in (None, "", [], {})]
    if not rows:
        return ""
    width = max(len(key) for key, _ in rows)
    return "\n".join(f"{key.ljust(width)}  {value}" for key, value in rows)


class Source:
    key: str = ""
    title: str = ""
    note_label: str = ""

    def available(self) -> bool:
        raise NotImplementedError

    def list_packages(self) -> list[Package]:
        raise NotImplementedError

    def info(self, package: Package) -> str:
        raise NotImplementedError
