from pathlib import Path

import yaml

from iterduca.core.runtime_config import RuntimeConfigBuilder
from iterduca.models.settings import AppSettings


def test_default_tun_config_uses_safe_windows_defaults() -> None:
    settings = AppSettings()
    tun = settings.tun_config()

    assert tun["enable"] is False
    assert tun["stack"] == "mips"
    assert tun["auto-route"] is True
    assert tun["auto-detect-interface"] is True
    assert tun["dns-hijack"] == ["any:53", "tcp://any:53"]
    assert tun["strict-route"] is False
    assert "192.168.0.0/16" in tun["route-exclude-address"]
    assert "fc00::/7" in tun["route-exclude-address"]
    assert "auto-redirect" not in tun


def test_iterduca_tun_values_override_profile_and_user_overrides(tmp_path: Path) -> None:
    source = tmp_path / "source.yaml"
    source.write_text(
        "proxies: []\n"
        "tun:\n"
        "  enable: false\n"
        "  stack: system\n"
        "  mtu: 1500\n",
        encoding="utf-8",
    )

    settings = AppSettings(
        tun_enabled=True,
        tun_stack="mips",
        tun_auto_route=True,
        tun_auto_detect_interface=True,
        tun_dns_hijack=True,
        tun_strict_route=False,
    )
    runtime = RuntimeConfigBuilder(tmp_path / "runtime").build(
        source,
        mixed_port=7890,
        controller_host="127.0.0.1",
        controller_port=9090,
        mode="rule",
        secret="test-secret",
        overrides={"tun": {"enable": False, "stack": "gvisor", "mtu": 1400}},
        tun=settings.tun_config(),
    )

    data = yaml.safe_load(runtime.path.read_text(encoding="utf-8"))
    assert data["tun"]["enable"] is True
    assert data["tun"]["stack"] == "mips"
    assert data["tun"]["mtu"] == 1400
    assert data["tun"]["auto-route"] is True
    assert data["tun"]["strict-route"] is False


def test_private_network_bypass_can_be_disabled() -> None:
    settings = AppSettings(tun_bypass_private_networks=False)
    tun = settings.tun_config()
    assert "route-exclude-address" not in tun
