from __future__ import annotations

import os
import subprocess
import sys


class StartupService:
    VALUE_NAME = "Iterduca"
    KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

    @property
    def supported(self) -> bool:
        return os.name == "nt"

    def command(self) -> str:
        if getattr(sys, "frozen", False):
            return subprocess.list2cmdline([sys.executable, "--background"])
        return subprocess.list2cmdline(
            [sys.executable, "-m", "iterduca", "--background"]
        )

    def is_enabled(self) -> bool:
        if not self.supported:
            return False
        winreg = self._winreg()
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.KEY_PATH,
                0,
                winreg.KEY_QUERY_VALUE,
            ) as key:
                value, _ = winreg.QueryValueEx(key, self.VALUE_NAME)
        except FileNotFoundError:
            return False
        return str(value) == self.command()

    def set_enabled(self, enabled: bool) -> None:
        if not self.supported:
            raise OSError("Startup integration is currently supported on Windows only")
        winreg = self._winreg()
        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER,
            self.KEY_PATH,
            0,
            winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE,
        ) as key:
            if enabled:
                winreg.SetValueEx(
                    key,
                    self.VALUE_NAME,
                    0,
                    winreg.REG_SZ,
                    self.command(),
                )
            else:
                try:
                    winreg.DeleteValue(key, self.VALUE_NAME)
                except FileNotFoundError:
                    pass

    @staticmethod
    def _winreg():
        import winreg

        return winreg
