import json
import zipfile
from pathlib import Path

import pytest

from iterduca.paths import AppPaths
from iterduca.services.backup_service import BackupService


def make_paths(root: Path) -> AppPaths:
    return AppPaths(
        root=root,
        profiles=root / "profiles",
        runtime=root / "runtime",
        logs=root / "logs",
        settings_file=root / "settings.json",
        subscriptions_file=root / "subscriptions.json",
        override_file=root / "override.yaml",
        proxy_state_file=root / "proxy-state.json",
        metrics_file=root / "metrics.json",
    )


def test_backup_round_trip_replaces_configuration(tmp_path: Path) -> None:
    paths = make_paths(tmp_path / "app")
    paths.ensure()
    paths.settings_file.write_text('{"mixed_port": 7890}', encoding="utf-8")
    paths.subscriptions_file.write_text(
        '{"profile.yaml": {"url": "https://example.com/sub"}}',
        encoding="utf-8",
    )
    paths.override_file.write_text("dns:\n  enable: true\n", encoding="utf-8")
    profile = paths.profiles / "profile.yaml"
    profile.write_text("proxies: []\n", encoding="utf-8")

    archive = tmp_path / "backup.zip"
    service = BackupService(paths)
    service.export(archive)

    paths.settings_file.write_text('{"mixed_port": 9999}', encoding="utf-8")
    profile.write_text("proxies:\n  - {name: changed}\n", encoding="utf-8")
    extra = paths.profiles / "extra.yaml"
    extra.write_text("proxies: []\n", encoding="utf-8")

    service.restore(archive)

    assert json.loads(paths.settings_file.read_text(encoding="utf-8"))["mixed_port"] == 7890
    assert profile.read_text(encoding="utf-8") == "proxies: []\n"
    assert not extra.exists()


def test_backup_restore_rejects_unexpected_members(tmp_path: Path) -> None:
    paths = make_paths(tmp_path / "app")
    paths.ensure()
    archive = tmp_path / "malicious.zip"

    with zipfile.ZipFile(archive, "w") as payload:
        payload.writestr("manifest.json", '{"format": 1}')
        payload.writestr("../outside.txt", "nope")

    with pytest.raises(ValueError, match="Unexpected backup member"):
        BackupService(paths).restore(archive)

    assert not (tmp_path / "outside.txt").exists()
