from __future__ import annotations

import subprocess
import threading
from collections.abc import Callable
from pathlib import Path


LogCallback = Callable[[str], None]


class CoreManager:
    def __init__(self, log_callback: LogCallback | None = None) -> None:
        self._process: subprocess.Popen[str] | None = None
        self._reader: threading.Thread | None = None
        self._log_callback = log_callback or (lambda _: None)

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def start(self, executable: Path, config: Path, home: Path) -> None:
        if self.running:
            raise RuntimeError("Mihomo core is already running")
        executable = executable.expanduser().resolve()
        if not executable.is_file():
            raise FileNotFoundError(executable)
        if not config.is_file():
            raise FileNotFoundError(config)
        home.mkdir(parents=True, exist_ok=True)

        command = self.build_command(executable, config, home)
        self._process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=self._creation_flags(),
        )
        self._reader = threading.Thread(target=self._read_output, daemon=True)
        self._reader.start()

    def stop(self, timeout: float = 3.0) -> None:
        process = self._process
        if process is None:
            return
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        self._process = None

    @staticmethod
    def build_command(executable: Path, config: Path, home: Path) -> list[str]:
        return [str(executable), "-d", str(home), "-f", str(config)]

    @staticmethod
    def _creation_flags() -> int:
        return int(getattr(subprocess, "CREATE_NO_WINDOW", 0))

    def _read_output(self) -> None:
        process = self._process
        if process is None or process.stdout is None:
            return
        for line in process.stdout:
            self._log_callback(line.rstrip())
