from pathlib import Path

from iterduca.services.log_service import LogService


def test_log_service_rotates_and_exports(tmp_path: Path) -> None:
    service = LogService(tmp_path / "logs", max_bytes=1024, backups=2)
    service.append("A" * 900)
    service.append("B" * 900)

    assert (tmp_path / "logs" / "iterduca.log.1").exists()
    assert (tmp_path / "logs" / "iterduca.log").exists()

    destination = tmp_path / "exported.log"
    service.export(destination)
    text = destination.read_text(encoding="utf-8")

    assert "A" * 100 in text
    assert "B" * 100 in text


def test_log_service_clear_removes_rotated_files(tmp_path: Path) -> None:
    service = LogService(tmp_path / "logs", max_bytes=1024, backups=2)
    service.append("A" * 900)
    service.append("B" * 900)

    service.clear()

    assert not any((tmp_path / "logs").glob("iterduca.log*"))
