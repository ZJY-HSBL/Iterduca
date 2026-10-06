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
