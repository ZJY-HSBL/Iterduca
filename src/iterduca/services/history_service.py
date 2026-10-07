from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


class HistoryService:
    def __init__(
        self,
        path: Path,
        *,
        max_traffic_samples: int = 720,
        max_latency_samples: int = 50,
    ) -> None:
        self.path = path
        self.max_traffic_samples = max(10, int(max_traffic_samples))
        self.max_latency_samples = max(5, int(max_latency_samples))
        self._data = self._load()
        self._dirty = False

    def record_traffic(self, up: int, down: int) -> None:
        traffic = self._data.setdefault("traffic", [])
        if not isinstance(traffic, list):
            traffic = []
            self._data["traffic"] = traffic
        traffic.append(
            {
                "ts": self._now(),
                "up": max(0, int(up)),
                "down": max(0, int(down)),
            }
        )
        del traffic[:-self.max_traffic_samples]
        self._dirty = True

    def traffic(self) -> list[dict]:
        traffic = self._data.get("traffic", [])
        return list(traffic) if isinstance(traffic, list) else []

    def record_latency(self, group: str, proxy: str, delay: int) -> None:
        key = self._latency_key(group, proxy)
        latency = self._data.setdefault("latency", {})
        if not isinstance(latency, dict):
            latency = {}
            self._data["latency"] = latency
        samples = latency.setdefault(key, [])
        if not isinstance(samples, list):
            samples = []
            latency[key] = samples
        samples.append(
            {
                "ts": self._now(),
                "delay": int(delay),
            }
        )
        del samples[:-self.max_latency_samples]
        self._dirty = True

    def latency(self, group: str, proxy: str) -> list[dict]:
        latency = self._data.get("latency", {})
        if not isinstance(latency, dict):
            return []
        samples = latency.get(self._latency_key(group, proxy), [])
        return list(samples) if isinstance(samples, list) else []

    def flush(self) -> None:
        if not self._dirty:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(self._data, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        temporary.replace(self.path)
        self._dirty = False

    def clear(self) -> None:
        self._data = {"traffic": [], "latency": {}}
        self._dirty = True
        self.flush()

    def _load(self) -> dict:
        if not self.path.exists():
            return {"traffic": [], "latency": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"traffic": [], "latency": {}}
        if not isinstance(data, dict):
            return {"traffic": [], "latency": {}}
        data.setdefault("traffic", [])
        data.setdefault("latency", {})
        return data

    @staticmethod
    def _latency_key(group: str, proxy: str) -> str:
        return f"{group}\u0000{proxy}"

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat(timespec="seconds")
