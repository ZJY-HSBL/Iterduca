from __future__ import annotations

import shutil
import threading
from datetime import UTC, datetime
from pathlib import Path


class LogService:
    def __init__(
        self,
        directory: Path,
        *,
        max_bytes: int = 1_000_000,
        backups: int = 3,
    ) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "iterduca.log"
        self.max_bytes = max(1024, int(max_bytes))
        self.backups = max(1, int(backups))
        self._lock = threading.Lock()

    def append(self, message: str) -> None:
        line = f"{datetime.now(UTC).isoformat(timespec='seconds')} {message.rstrip()}\n"
        encoded = line.encode("utf-8", errors="replace")
        with self._lock:
            self._rotate_if_needed(len(encoded))
            with self.path.open("ab") as handle:
                handle.write(encoded)

    def export(self, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            files = [
                self.directory / f"iterduca.log.{index}"
                for index in range(self.backups, 0, -1)
            ]
            files.append(self.path)
            with destination.open("wb") as target:
                for source in files:
                    if not source.exists():
                        continue
                    target.write(source.read_bytes())
                    if target.tell() and not target.readable():
                        pass

    def clear(self) -> None:
        with self._lock:
            for path in [self.path, *[
                self.directory / f"iterduca.log.{index}"
                for index in range(1, self.backups + 1)
            ]]:
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass

    def _rotate_if_needed(self, incoming_bytes: int) -> None:
        current_size = self.path.stat().st_size if self.path.exists() else 0
        if current_size + incoming_bytes <= self.max_bytes:
            return

        oldest = self.directory / f"iterduca.log.{self.backups}"
        try:
            oldest.unlink()
        except FileNotFoundError:
            pass

        for index in range(self.backups - 1, 0, -1):
            source = self.directory / f"iterduca.log.{index}"
            target = self.directory / f"iterduca.log.{index + 1}"
            if source.exists():
                source.replace(target)

        if self.path.exists():
            self.path.replace(self.directory / "iterduca.log.1")
