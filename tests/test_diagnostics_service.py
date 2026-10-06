import json
import zipfile
from pathlib import Path

from iterduca.models.settings import AppSettings
from iterduca.paths import AppPaths
from iterduca.services.diagnostics_service import DiagnosticsService


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
    )


def test_diagnostics_excludes_sensitive_files_and_raw_logs(tmp_path: Path) -> None:
    paths = make_paths(tmp_path / "app")
    paths.ensure()

    secret = "VERY-SECRET-TOKEN"
    paths.subscriptions_file.write_text(
        f'{{"profile.yaml": {{"url": "https://example.com/?token={secret}"}}}}',
        encoding="utf-8",
    )
    (paths.profiles / "profile.yaml").write_text(
        f"proxies:\n  - name: A\n    password: {secret}\n",
        encoding="utf-8",
    )
    (paths.runtime / "config.yaml").write_text(
        f"secret: {secret}\n",
        encoding="utf-8",
    )
    (paths.logs / "iterduca.log").write_text(
        f"raw log could contain {secret}\n",
        encoding="utf-8",
    )

    destination = tmp_path / "diagnostics.zip"
    settings = AppSettings(
        core_path="C:/private/path/mihomo.exe",
        active_profile="profile.yaml",
    )
    DiagnosticsService(paths).export(destination, settings)

    with zipfile.ZipFile(destination, "r") as archive:
        assert archive.namelist() == ["diagnostics.json"]
        raw = archive.read("diagnostics.json").decode("utf-8")
        payload = json.loads(raw)

    assert secret not in raw
    assert "C:/private/path/mihomo.exe" not in raw
    assert "profile.yaml" not in raw
    assert payload["settings"]["core_path_set"] is True
    assert payload["settings"]["active_profile_set"] is True
    assert payload["log_inventory"][0]["name"] == "iterduca.log"
