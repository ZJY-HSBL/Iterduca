from __future__ import annotations

import ctypes
import json
import os
import socket
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class ProxySnapshot:
    enabled: int
    server: str


@dataclass(slots=True)
class ProxyRecoveryState:
    previous: ProxySnapshot
    managed_server: str


class SystemProxy:
    """Windows WinINet proxy controller with crash-safe state restoration."""

    INTERNET_OPTION_SETTINGS_CHANGED = 39
    INTERNET_OPTION_REFRESH = 37
    KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

    def __init__(self, state_file: Path | None = None) -> None:
        self.state_file = state_file
        self._snapshot: ProxySnapshot | None = None

    @property
    def supported(self) -> bool:
        return os.name == "nt"

    def enable(self, host: str, port: int) -> None:
        winreg = self._winreg()
        managed_server = f"{host}:{int(port)}"
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            self.KEY_PATH,
            0,
            winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE,
        ) as key:
            if self._snapshot is None:
                self._snapshot = ProxySnapshot(
                    enabled=self._query_int(winreg, key, "ProxyEnable", 0),
                    server=self._query_str(winreg, key, "ProxyServer", ""),
                )
                self._write_state(
                    ProxyRecoveryState(
                        previous=self._snapshot,
                        managed_server=managed_server,
                    )
                )
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, managed_server)
        self._refresh()

    def disable(self) -> None:
        if not self.supported:
            return

        recovery = self._read_state()
        snapshot = self._snapshot or (recovery.previous if recovery else None)
        if snapshot is None:
            return

        self._restore(snapshot)
        self._snapshot = None
        self._clear_state()

    def recover_stale(self) -> bool:
        """Restore the previous proxy only when Iterduca still owns a dead local proxy."""
        if not self.supported:
            return False

        recovery = self._read_state()
        if recovery is None:
            return False

        winreg = self._winreg()
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            self.KEY_PATH,
            0,
            winreg.KEY_QUERY_VALUE,
        ) as key:
            enabled = self._query_int(winreg, key, "ProxyEnable", 0)
            server = self._query_str(winreg, key, "ProxyServer", "")

        if enabled != 1 or server != recovery.managed_server:
            self._clear_state()
            return False

        endpoint = self._parse_endpoint(recovery.managed_server)
        if endpoint is not None and self._port_open(*endpoint):
            return False

        self._restore(recovery.previous)
        self._clear_state()
        self._snapshot = None
        return True

    def _restore(self, snapshot: ProxySnapshot) -> None:
        winreg = self._winreg()
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            self.KEY_PATH,
            0,
            winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, snapshot.enabled)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, snapshot.server)
        self._refresh()

    def _write_state(self, state: ProxyRecoveryState) -> None:
        if self.state_file is None:
            return
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_file.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                {
                    "previous": asdict(state.previous),
                    "managed_server": state.managed_server,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        temporary.replace(self.state_file)

    def _read_state(self) -> ProxyRecoveryState | None:
        if self.state_file is None or not self.state_file.exists():
            return None
        try:
            payload = json.loads(self.state_file.read_text(encoding="utf-8"))
            previous = payload["previous"]
            return ProxyRecoveryState(
                previous=ProxySnapshot(
                    enabled=int(previous["enabled"]),
                    server=str(previous.get("server", "")),
                ),
                managed_server=str(payload["managed_server"]),
            )
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            self._clear_state()
            return None

    def _clear_state(self) -> None:
        if self.state_file is None:
            return
        try:
            self.state_file.unlink()
        except FileNotFoundError:
            pass

    @staticmethod
    def _parse_endpoint(server: str) -> tuple[str, int] | None:
        host, separator, port = server.rpartition(":")
        if not separator or not host:
            return None
        try:
            return host, int(port)
        except ValueError:
            return None

    @staticmethod
    def _port_open(host: str, port: int) -> bool:
        try:
            with socket.create_connection((host, port), timeout=0.15):
                return True
        except OSError:
            return False

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
