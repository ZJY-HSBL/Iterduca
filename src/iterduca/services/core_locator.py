from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


class CoreLocator:
    def search_directories(self) -> list[Path]:
        directories: list[Path] = []
        if getattr(sys, "frozen", False):
            directories.append(Path(sys.executable).resolve().parent)
        else:
            directories.append(Path.cwd())
        executable_dir = Path(sys.executable).resolve().parent
        if executable_dir not in directories:
            directories.append(executable_dir)
        return directories

    def discover(self) -> Path | None:
        names = ("mihomo.exe", "mihomo")
        for directory in self.search_directories():
            for name in names:
                candidate = directory / name
                if candidate.is_file():
                    return candidate
            for candidate in sorted(directory.glob("mihomo*.exe")):
                if candidate.is_file():
                    return candidate

        path_match = shutil.which("mihomo.exe" if os.name == "nt" else "mihomo")
        return Path(path_match).resolve() if path_match else None
