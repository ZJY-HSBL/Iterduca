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
