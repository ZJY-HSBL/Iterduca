from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass


@dataclass(slots=True)
class ProxySnapshot:
    enabled: int
    server: str


class SystemProxy:
    """Windows WinINet proxy controller with state restoration."""

    INTERNET_OPTION_SETTINGS_CHANGED = 39
    INTERNET_OPTION_REFRESH = 37

    def __init__(self) -> None:
        self._snapshot: ProxySnapshot | None = None

    @property
    def supported(self) -> bool:
        return os.name == "nt"

    def enable(self, host: str, port: int) -> None:
        winreg = self._winreg()
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
            0,
            winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE,
        ) as key:
            if self._snapshot is None:
                self._snapshot = ProxySnapshot(
                    enabled=self._query_int(winreg, key, "ProxyEnable", 0),
                    server=self._query_str(winreg, key, "ProxyServer", ""),
                )
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"{host}:{int(port)}")
        self._refresh()

    def disable(self) -> None:
        if not self.supported:
            return
        winreg = self._winreg()
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
            0,
            winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE,
        ) as key:
            if self._snapshot is None:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            else:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, self._snapshot.enabled)
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, self._snapshot.server)
                self._snapshot = None
        self._refresh()

    @staticmethod
    def _winreg():
        if os.name != "nt":
            raise OSError("System proxy control is currently supported on Windows only")
        import winreg

        return winreg

    @staticmethod
    def _query_int(winreg, key, name: str, default: int) -> int:
        try:
            return int(winreg.QueryValueEx(key, name)[0])
        except FileNotFoundError:
            return default

    @staticmethod
    def _query_str(winreg, key, name: str, default: str) -> str:
        try:
            return str(winreg.QueryValueEx(key, name)[0])
        except FileNotFoundError:
            return default

    @classmethod
    def _refresh(cls) -> None:
        if os.name != "nt":
            return
        wininet = ctypes.windll.Wininet
        wininet.InternetSetOptionW(0, cls.INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
        wininet.InternetSetOptionW(0, cls.INTERNET_OPTION_REFRESH, 0, 0)
