from pathlib import Path

from iterduca.models.settings import AppSettings
from iterduca.services.settings_service import SettingsService


def test_settings_round_trip(tmp_path: Path) -> None:
    service = SettingsService(tmp_path / "settings.json")
    settings = AppSettings(
        core_path="C:/mihomo.exe",
        active_profile="main.yaml",
        mixed_port=7897,
        subscription_auto_update_enabled=True,
        subscription_update_interval_hours=12,
    )
    service.save(settings)
    loaded = service.load()
    assert loaded == settings


def test_invalid_settings_fall_back_to_defaults(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("not-json", encoding="utf-8")
    loaded = SettingsService(path).load()
    assert loaded.mixed_port == 7890


def test_subscription_update_interval_is_coerced_to_int(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        '{"subscription_auto_update_enabled": true, '
        '"subscription_update_interval_hours": "6"}',
        encoding="utf-8",
    )

    loaded = SettingsService(path).load()

    assert loaded.subscription_auto_update_enabled is True
    assert loaded.subscription_update_interval_hours == 6
