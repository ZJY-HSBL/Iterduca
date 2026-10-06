from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

import httpx


@dataclass(frozen=True, slots=True)
class ProxyGroup:
    name: str
    kind: str
    now: str
    all: tuple[str, ...]


class MihomoApi:
    def __init__(self, base_url: str, secret: str = "", timeout: float = 3.0) -> None:
        headers = {"Authorization": f"Bearer {secret}"} if secret else {}
        self._client = httpx.Client(base_url=base_url.rstrip("/"), headers=headers, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def version(self) -> dict:
        return self._json("GET", "/version")

    def configs(self) -> dict:
        return self._json("GET", "/configs")

    def set_mode(self, mode: str) -> None:
        self._request("PATCH", "/configs", json={"mode": mode.lower()})

    def proxy_groups(self) -> list[ProxyGroup]:
        payload = self._json("GET", "/proxies")
        proxies = payload.get("proxies", {})
        groups: list[ProxyGroup] = []
        if not isinstance(proxies, dict):
            return groups
        for name, item in proxies.items():
            if not isinstance(item, dict) or "all" not in item:
                continue
            candidates = item.get("all")
            groups.append(
                ProxyGroup(
                    name=name,
                    kind=str(item.get("type", "")),
                    now=str(item.get("now", "")),
                    all=(
                        tuple(str(value) for value in candidates)
                        if isinstance(candidates, list)
                        else ()
                    ),
                )
            )
        return groups

    def select_proxy(self, group: str, proxy: str) -> None:
        path = f"/proxies/{quote(group, safe='')}"
        self._request("PUT", path, json={"name": proxy})

    def delay(
        self,
        proxy: str,
        url: str = "https://www.gstatic.com/generate_204",
        timeout_ms: int = 5000,
    ) -> int:
        path = f"/proxies/{quote(proxy, safe='')}/delay"
        response = self._json("GET", path, params={"url": url, "timeout": timeout_ms})
        return int(response["delay"])

    def connections(self) -> dict:
        return self._json("GET", "/connections")

    def close_connection(self, connection_id: str) -> None:
        self._request("DELETE", f"/connections/{quote(connection_id, safe='')}")

    def close_all_connections(self) -> None:
        self._request("DELETE", "/connections")

    def rules(self) -> list[dict]:
        payload = self._json("GET", "/rules")
        rules = payload.get("rules", [])
        if not isinstance(rules, list):
            return []
        return [item for item in rules if isinstance(item, dict)]

    def set_rule_disabled(self, index: int, disabled: bool) -> None:
        self._request(
            "PATCH",
            "/rules/disable",
            json={str(int(index)): bool(disabled)},
        )

    def dns_query(self, name: str, record_type: str = "A") -> dict:
        return self._json(
            "GET",
            "/dns/query",
            params={"name": name, "type": record_type},
        )

    def proxy_providers(self) -> dict[str, dict]:
        payload = self._json("GET", "/providers/proxies")
        providers = payload.get("providers", {})
        if not isinstance(providers, dict):
            return {}
        return {
            str(name): item
            for name, item in providers.items()
            if isinstance(item, dict)
        }

    def update_proxy_provider(self, name: str) -> None:
        self._request("PUT", f"/providers/proxies/{quote(name, safe='')}")

    def healthcheck_proxy_provider(self, name: str) -> None:
        self._request(
            "GET",
            f"/providers/proxies/{quote(name, safe='')}/healthcheck",
        )

    def flush_dns_cache(self) -> None:
        self._request("POST", "/cache/dns/flush")

    def flush_fakeip_cache(self) -> None:
        self._request("POST", "/cache/fakeip/flush")

    def rule_providers(self) -> dict[str, dict]:
        payload = self._json("GET", "/providers/rules")
        providers = payload.get("providers", {})
        if not isinstance(providers, dict):
            return {}
        return {
            str(name): item
            for name, item in providers.items()
            if isinstance(item, dict)
        }

    def update_rule_provider(self, name: str) -> None:
        self._request("PUT", f"/providers/rules/{quote(name, safe='')}")

    def memory(self) -> int:
        payload = self._json("GET", "/memory")
        return int(payload.get("inuse", 0))

    def _json(self, method: str, path: str, **kwargs) -> dict:
        response = self._request(method, path, **kwargs)
        payload = response.json()
        return payload if isinstance(payload, dict) else {}

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        response = self._client.request(method, path, **kwargs)
        response.raise_for_status()
        return response
