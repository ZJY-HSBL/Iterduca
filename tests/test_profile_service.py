from pathlib import Path

import pytest

from iterduca.services.profile_service import ProfileService


def test_import_profile_copies_and_counts_proxies(tmp_path: Path) -> None:
    source = tmp_path / "My Profile.yaml"
    source.write_text(
        "proxies:\n"
        "  - {name: A, type: http, server: 127.0.0.1, port: 80}\n"
        "  - {name: B, type: http, server: 127.0.0.1, port: 81}\n",
        encoding="utf-8",
    )
    service = ProfileService(tmp_path / "profiles")
    info = service.import_file(source)
    assert info.proxy_count == 2
    assert info.path.exists()
    assert info.path != source
    assert "My-Profile" in info.name


def test_resolve_rejects_path_escape(tmp_path: Path) -> None:
    service = ProfileService(tmp_path / "profiles")
    outside = tmp_path / "outside.yaml"
    outside.write_text("proxies: []\n", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        service.resolve("../outside.yaml")


def test_delete_profile_is_confined_to_profile_directory(tmp_path: Path) -> None:
    service = ProfileService(tmp_path / "profiles")
    profile = service.directory / "local.yaml"
    profile.write_text("proxies: []\n", encoding="utf-8")

    service.delete("local.yaml")

    assert not profile.exists()

    outside = tmp_path / "outside.yaml"
    outside.write_text("proxies: []\n", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        service.delete("../outside.yaml")
