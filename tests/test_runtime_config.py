from pathlib import Path

import yaml

from iterduca.core.runtime_config import RuntimeConfigBuilder


def test_runtime_config_overrides_controller_without_mutating_source(tmp_path: Path) -> None:
    source = tmp_path / "source.yaml"
    source.write_text(
        "mixed-port: 9999\nexternal-controller: 0.0.0.0:9090\nmode: global\nproxies: []\n",
        encoding="utf-8",
    )
    before = source.read_text(encoding="utf-8")
    builder = RuntimeConfigBuilder(tmp_path / "runtime")

    result = builder.build(
        source,
        mixed_port=7890,
        controller_host="127.0.0.1",
        controller_port=9091,
        mode="rule",
        secret="known-secret",
    )

    data = yaml.safe_load(result.path.read_text(encoding="utf-8"))
    assert data["mixed-port"] == 7890
    assert data["external-controller"] == "127.0.0.1:9091"
    assert data["secret"] == "known-secret"
    assert data["mode"] == "rule"
    assert data["allow-lan"] is False
    assert source.read_text(encoding="utf-8") == before


def test_runtime_config_generates_secret(tmp_path: Path) -> None:
    source = tmp_path / "source.yaml"
    source.write_text("proxies: []\n", encoding="utf-8")
    result = RuntimeConfigBuilder(tmp_path / "runtime").build(
        source,
        mixed_port=7890,
        controller_host="127.0.0.1",
        controller_port=9090,
        mode="direct",
    )
    assert len(result.secret) >= 24
