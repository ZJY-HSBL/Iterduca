from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from iterduca.paths import AppPaths


class BackupService:
    FORMAT_VERSION = 1

    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths

    def export(self, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        with zipfile.ZipFile(
            temporary,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            archive.writestr(
                "manifest.json",
                json.dumps(
                    {
                        "format": self.FORMAT_VERSION,
                        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
                    },
                    indent=2,
                ),
            )
            self._write_if_exists(archive, self.paths.settings_file, "settings.json")
            self._write_if_exists(
                archive,
                self.paths.subscriptions_file,
                "subscriptions.json",
            )
            self._write_if_exists(archive, self.paths.override_file, "override.yaml")
            for profile in sorted(self.paths.profiles.glob("*.y*ml")):
                archive.write(profile, f"profiles/{profile.name}")
        temporary.replace(destination)

    def restore(self, source: Path) -> None:
        with zipfile.ZipFile(source, "r") as archive:
            names = archive.namelist()
            self._validate_names(names)
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            if int(manifest.get("format", -1)) != self.FORMAT_VERSION:
                raise ValueError("Unsupported Iterduca backup format")

            for profile in self.paths.profiles.glob("*.y*ml"):
                profile.unlink()

            mapping = {
                "settings.json": self.paths.settings_file,
                "subscriptions.json": self.paths.subscriptions_file,
                "override.yaml": self.paths.override_file,
            }
            for member, target in mapping.items():
                if member in names:
                    self._atomic_write(target, archive.read(member))
                else:
                    try:
                        target.unlink()
                    except FileNotFoundError:
                        pass

            for member in names:
                if not member.startswith("profiles/") or member.endswith("/"):
                    continue
                filename = member.removeprefix("profiles/")
                self._atomic_write(self.paths.profiles / filename, archive.read(member))

    @staticmethod
    def _write_if_exists(
        archive: zipfile.ZipFile,
        source: Path,
        member: str,
    ) -> None:
        if source.exists():
            archive.write(source, member)

    @classmethod
    def _validate_names(cls, names: list[str]) -> None:
        allowed_exact = {
            "manifest.json",
            "settings.json",
            "subscriptions.json",
            "override.yaml",
        }
        if "manifest.json" not in names:
            raise ValueError("Backup manifest is missing")

        for member in names:
            if member in allowed_exact:
                continue
            if member.startswith("profiles/") and not member.endswith("/"):
                relative = member.removeprefix("profiles/")
                path = Path(relative)
                if (
                    len(path.parts) == 1
                    and path.suffix.lower() in {".yaml", ".yml"}
                    and path.name == relative
                ):
                    continue
            raise ValueError(f"Unexpected backup member: {member}")

    @staticmethod
    def _atomic_write(target: Path, content: bytes) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_bytes(content)
        temporary.replace(target)
