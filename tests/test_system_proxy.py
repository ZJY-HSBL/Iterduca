from pathlib import Path

from iterduca.system.proxy import ProxyRecoveryState, ProxySnapshot, SystemProxy


def test_proxy_recovery_state_round_trip(tmp_path: Path) -> None:
    service = SystemProxy(tmp_path / "proxy-state.json")
    expected = ProxyRecoveryState(
        previous=ProxySnapshot(enabled=0, server="old.proxy:8080"),
        managed_server="127.0.0.1:7890",
    )

    service._write_state(expected)
    loaded = service._read_state()

    assert loaded is not None
    assert loaded.previous.enabled == 0
    assert loaded.previous.server == "old.proxy:8080"
    assert loaded.managed_server == "127.0.0.1:7890"


def test_proxy_endpoint_parser() -> None:
    assert SystemProxy._parse_endpoint("127.0.0.1:7890") == ("127.0.0.1", 7890)
    assert SystemProxy._parse_endpoint("invalid") is None
    assert SystemProxy._parse_endpoint("127.0.0.1:not-a-port") is None


def test_invalid_proxy_recovery_state_is_discarded(tmp_path: Path) -> None:
    state = tmp_path / "proxy-state.json"
    state.write_text("{invalid", encoding="utf-8")
    service = SystemProxy(state)

    assert service._read_state() is None
    assert not state.exists()


class FakeWinReg:
    HKEY_CURRENT_USER = object()
    KEY_QUERY_VALUE = 1
    KEY_SET_VALUE = 2
    REG_DWORD = 4
    REG_SZ = 1

    def __init__(self, enabled: int, server: str) -> None:
        self.values = {
            "ProxyEnable": enabled,
            "ProxyServer": server,
        }

    def OpenKey(self, *args, **kwargs):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def QueryValueEx(self, key, name: str):
        if name not in self.values:
            raise FileNotFoundError(name)
        return self.values[name], None

    def SetValueEx(self, key, name: str, reserved, kind, value) -> None:
        self.values[name] = value


def test_recover_stale_restores_only_dead_managed_proxy(
    tmp_path: Path, monkeypatch
) -> None:
    service = SystemProxy(tmp_path / "proxy-state.json")
    service._write_state(
        ProxyRecoveryState(
            previous=ProxySnapshot(enabled=1, server="old.proxy:8080"),
            managed_server="127.0.0.1:7890",
        )
    )
    fake = FakeWinReg(enabled=1, server="127.0.0.1:7890")
    monkeypatch.setattr(service, "_winreg", lambda: fake)
    monkeypatch.setattr(service, "_port_open", lambda host, port: False)
    monkeypatch.setattr(SystemProxy, "_refresh", classmethod(lambda cls: None))

    recovered = service.recover_stale()

    assert recovered is True
    assert fake.values["ProxyEnable"] == 1
    assert fake.values["ProxyServer"] == "old.proxy:8080"
    assert not (tmp_path / "proxy-state.json").exists()


def test_recover_stale_keeps_live_managed_proxy(
    tmp_path: Path, monkeypatch
) -> None:
    service = SystemProxy(tmp_path / "proxy-state.json")
    service._write_state(
        ProxyRecoveryState(
            previous=ProxySnapshot(enabled=0, server=""),
            managed_server="127.0.0.1:7890",
        )
    )
    fake = FakeWinReg(enabled=1, server="127.0.0.1:7890")
    monkeypatch.setattr(service, "_winreg", lambda: fake)
    monkeypatch.setattr(service, "_port_open", lambda host, port: True)

    recovered = service.recover_stale()

    assert recovered is False
    assert fake.values["ProxyServer"] == "127.0.0.1:7890"
    assert (tmp_path / "proxy-state.json").exists()
