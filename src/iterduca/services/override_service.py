from __future__ import annotations

from pathlib import Path

import yaml


def deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        current = result.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            result[key] = deep_merge(current, value)
        else:
            result[key] = value
    return result


class OverrideService:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict:
        if not self.path.exists():
            return {}
        data = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise ValueError("Override YAML root must be a mapping")
        return data

    def load_text(self) -> str:
        if not self.path.exists():
            return "# Iterduca runtime overrides\n"
        return self.path.read_text(encoding="utf-8")

    def save_text(self, text: str) -> dict:
        data = yaml.safe_load(text) if text.strip() else {}
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise ValueError("Override YAML root must be a mapping")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        temporary.replace(self.path)
        return data
