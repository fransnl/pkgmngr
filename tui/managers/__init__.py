from __future__ import annotations

from pathlib import Path

from .base import CommandError, Package, Source
from .brew import BrewSource
from .cargo import CargoSource
from .flatpak import FlatpakSource
from .linux import AptSource, DnfSource, YaySource
from .npm import NpmSource
from .python import PythonSource
from .winget import WingetSource

__all__ = ["CommandError", "Package", "Source", "all_sources", "discover_sources"]


def all_sources(directory: Path) -> list[Source]:
    return [
        NpmSource("global"),
        NpmSource("local", directory),
        PythonSource("global"),
        PythonSource("local", directory),
        BrewSource(),
        AptSource(),
        DnfSource(),
        YaySource(),
        FlatpakSource(),
        CargoSource(),
        WingetSource(),
    ]


def discover_sources(directory: Path) -> list[Source]:
    return [source for source in all_sources(directory) if source.available()]
