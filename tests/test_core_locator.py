from pathlib import Path

from iterduca.services.core_locator import CoreLocator


def test_core_locator_prefers_local_mihomo(tmp_path: Path, monkeypatch) -> None:
    core = tmp_path / "mihomo-windows-amd64.exe"
    core.write_text("", encoding="utf-8")
    locator = CoreLocator()
    monkeypatch.setattr(locator, "search_directories", lambda: [tmp_path])

    discovered = locator.discover()

    assert discovered == core
