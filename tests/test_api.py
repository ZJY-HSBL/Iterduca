from __future__ import annotations

from urllib.parse import unquote

import httpx

from iterduca.core.api import MihomoApi


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []

    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        self.calls.append((method, path, kwargs))
        request = httpx.Request(method, f"http://localhost{path}")
        if path == "/rules":
            return httpx.Response(
                200,
                request=request,
                json={"rules": [{"type": "DOMAIN", "payload": "example.com", "proxy": "Proxy"}]},
            )
        return httpx.Response(204, request=request)

    def close(self) -> None:
        return None


def test_rules_and_connection_close_use_controller_endpoints() -> None:
    api = MihomoApi("http://127.0.0.1:9090")
    fake = FakeClient()
    api._client = fake  # type: ignore[assignment]

    rules = api.rules()
    api.close_connection("abc/123")

    assert rules[0]["payload"] == "example.com"
    method, path, _ = fake.calls[-1]
    assert method == "DELETE"
    assert unquote(path) == "/connections/abc/123"


def test_rule_provider_and_memory_endpoints() -> None:
    api = MihomoApi("http://127.0.0.1:9090")
    fake = FakeClient()
    api._client = fake  # type: ignore[assignment]

    original_request = fake.request

    def request(method: str, path: str, **kwargs):
        if path == "/providers/rules":
            req = httpx.Request(method, f"http://localhost{path}")
            fake.calls.append((method, path, kwargs))
            return httpx.Response(
                200,
                request=req,
                json={"providers": {"geosite": {"type": "HTTP", "behavior": "domain"}}},
            )
        if path == "/memory":
            req = httpx.Request(method, f"http://localhost{path}")
            fake.calls.append((method, path, kwargs))
            return httpx.Response(200, request=req, json={"inuse": 123456})
        return original_request(method, path, **kwargs)

    fake.request = request  # type: ignore[method-assign]

    providers = api.rule_providers()
    memory = api.memory()
    api.update_rule_provider("geo/site")

    assert providers["geosite"]["behavior"] == "domain"
    assert memory == 123456
    assert fake.calls[-1][0] == "PUT"
    assert fake.calls[-1][1] == "/providers/rules/geo%2Fsite"
