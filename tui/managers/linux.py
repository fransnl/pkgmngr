from __future__ import annotations

from .base import CommandError, Package, Source, run, which


class AptSource(Source):
    key = "apt"
    title = "apt"
    note_label = "Arch"

    def available(self) -> bool:
        return which("apt") is not None and which("dpkg-query") is not None

    def list_packages(self) -> list[Package]:
        output = run(
            [
                which("dpkg-query") or "dpkg-query",
                "--show",
                "--showformat=${db:Status-Abbrev}\\t${Package}\\t${Version}\\t${Architecture}\\n",
            ]
        )
        packages = []
        for line in output.splitlines():
            parts = line.split("\t")
            if len(parts) == 4 and parts[0].startswith("ii"):
                packages.append(Package(parts[1], parts[2], parts[3]))
        return packages

    def info(self, package: Package) -> str:
        return run([which("dpkg-query") or "dpkg-query", "--status", f"{package.name}:{package.note}"])


class DnfSource(Source):
    key = "dnf"
    title = "dnf"
    note_label = "Arch"

    def available(self) -> bool:
        return which("dnf") is not None and which("rpm") is not None

    def list_packages(self) -> list[Package]:
        output = run(
            [which("rpm") or "rpm", "--query", "--all", "--queryformat", "%{NAME}\\t%{VERSION}-%{RELEASE}\\t%{ARCH}\\n"]
        )
        packages = []
        for line in output.splitlines():
            parts = line.split("\t")
            if len(parts) == 3:
                packages.append(Package(*parts))
        return packages

    def info(self, package: Package) -> str:
        rpm = which("rpm") or "rpm"
        try:
            return run([rpm, "--query", "--info", f"{package.name}-{package.version}.{package.note}"])
        except CommandError:
            return run([rpm, "--query", "--info", package.name])


class YaySource(Source):
    key = "yay"
    title = "yay"
    note_label = "Repo"

    def available(self) -> bool:
        return which("yay") is not None

    def list_packages(self) -> list[Package]:
        yay = which("yay") or "yay"
        foreign = {line.split()[0] for line in run([yay, "-Qm"], check=False).splitlines() if line.strip()}
        packages = []
        for line in run([yay, "-Q"]).splitlines():
            parts = line.split()
            if len(parts) >= 2:
                packages.append(Package(parts[0], parts[1], "aur" if parts[0] in foreign else "repo"))
        return packages

    def info(self, package: Package) -> str:
        return run([which("yay") or "yay", "-Qi", package.name])
