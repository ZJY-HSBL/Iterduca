from pathlib import Path

import yaml

from iterduca.core.runtime_config import RuntimeConfigBuilder
from iterduca.services.override_service import OverrideService, deep_merge


def test_deep_merge_preserves_nested_base_values() -> None:
    base = {"dns": {"enable": False, "ipv6": False}, "mode": "global"}
    override = {"dns": {"enable": True}}
    merged = deep_merge(base, override)

    assert merged["dns"] == {"enable": True, "ipv6": False}
    assert merged["mode"] == "global"


def test_override_service_round_trip(tmp_path: Path) -> None:
    service = OverrideService(tmp_path / "override.yaml")
    saved = service.save_text("dns:\n  enable: true\ntcp-concurrent: true\n")

    assert saved["dns"]["enable"] is True
    assert service.load()["tcp-concurrent"] is True


def test_app_owned_runtime_values_win_over_overrides(tmp_path: Path) -> None:
    source = tmp_path / "source.yaml"
    source.write_text("proxies: []\n", encoding="utf-8")

    result = RuntimeConfigBuilder(tmp_path / "runtime").build(
        source,
        mixed_port=7890,
        controller_host="127.0.0.1",
        controller_port=9090,
        mode="rule",
        secret="safe-secret",
        overrides={
            "mixed-port": 9999,
            "external-controller": "0.0.0.0:9999",
            "secret": "unsafe",
            "mode": "global",
            "dns": {"enable": True},
        },
    )

    data = yaml.safe_load(result.path.read_text(encoding="utf-8"))
    assert data["mixed-port"] == 7890
    assert data["external-controller"] == "127.0.0.1:9090"
    assert data["secret"] == "safe-secret"
    assert data["mode"] == "rule"
    assert data["dns"]["enable"] is True
