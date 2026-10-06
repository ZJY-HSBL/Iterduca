from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx
import yaml


@dataclass(frozen=True, slots=True)
class SubscriptionInfo:
    profile_name: str
    url: str
    updated_at: str


class SubscriptionService:
    def __init__(self, profiles_dir: Path, metadata_file: Path) -> None:
        self.profiles_dir = profiles_dir
        self.metadata_file = metadata_file
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[SubscriptionInfo]:
        data = self._load_metadata()
        items: list[SubscriptionInfo] = []
        for profile_name, item in data.items():
            if not isinstance(item, dict):
                continue
            url = str(item.get("url", ""))
            updated_at = str(item.get("updated_at", ""))
            if url:
                items.append(
                    SubscriptionInfo(
                        profile_name=profile_name,
                        url=url,
                        updated_at=updated_at,
                    )
                )
        return sorted(items, key=lambda item: item.profile_name.lower())

    def add(self, url: str) -> SubscriptionInfo:
        normalized = self._validate_url(url)
        text = self._download(normalized)
        profile_name = self._profile_name(normalized)
        self._write_profile(profile_name, text)
        info = SubscriptionInfo(
            profile_name=profile_name,
            url=normalized,
            updated_at=self._now(),
        )
        self._save_info(info)
        return info

    def update_all(self) -> list[SubscriptionInfo]:
        return [self.update(item.profile_name) for item in self.list()]

    def forget(self, profile_name: str) -> None:
        data = self._load_metadata()
        if profile_name not in data:
            return
        data.pop(profile_name, None)
        self._save_metadata(data)

    def update(self, profile_name: str) -> SubscriptionInfo:
        data = self._load_metadata()
        item = data.get(profile_name)
        if not isinstance(item, dict) or not item.get("url"):
            raise KeyError(profile_name)
        normalized = self._validate_url(str(item["url"]))
        text = self._download(normalized)
        self._write_profile(profile_name, text)
        info = SubscriptionInfo(
            profile_name=profile_name,
            url=normalized,
            updated_at=self._now(),
        )
        self._save_info(info)
        return info

    def _download(self, url: str) -> str:
        response = httpx.get(
            url,
            follow_redirects=True,
            timeout=15.0,
            headers={"User-Agent": "Iterduca/0.2"},
        )
        response.raise_for_status()
        content = response.content
        if len(content) > 8 * 1024 * 1024:
            raise ValueError("Subscription is larger than 8 MiB")
        text = content.decode("utf-8-sig")
        self._validate_profile(text)
        return text

    def _write_profile(self, profile_name: str, text: str) -> None:
        target = self.profiles_dir / profile_name
        temporary = target.with_suffix(".tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(target)

    def _save_info(self, info: SubscriptionInfo) -> None:
        data = self._load_metadata()
        data[info.profile_name] = asdict(info)
        self._save_metadata(data)

    def _save_metadata(self, data: dict) -> None:
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.metadata_file.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.metadata_file)

    def _load_metadata(self) -> dict:
        if not self.metadata_file.exists():
            return {}
        try:
            data = json.loads(self.metadata_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _validate_url(url: str) -> str:
        normalized = url.strip()
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Subscription URL must use http:// or https://")
        return normalized

    @staticmethod
    def _validate_profile(text: str) -> None:
        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            raise ValueError("Subscription did not return a YAML mapping")
        useful_keys = {"proxies", "proxy-providers", "proxy-groups", "rules"}
        if not useful_keys.intersection(data):
            raise ValueError("Subscription does not look like a Mihomo-compatible profile")

    @staticmethod
    def _profile_name(url: str) -> str:
        parsed = urlparse(url)
        stem = Path(parsed.path).stem or parsed.hostname or "subscription"
        safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "-", stem).strip("-") or "subscription"
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
        return f"{safe_stem}-{digest}.yaml"

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat()
