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


def test_proxy_provider_and_cache_endpoints() -> None:
    api = MihomoApi("http://127.0.0.1:9090")
    fake = FakeClient()
    api._client = fake  # type: ignore[assignment]

    original_request = fake.request

    def request(method: str, path: str, **kwargs):
        if path == "/providers/proxies":
            req = httpx.Request(method, f"http://localhost{path}")
            fake.calls.append((method, path, kwargs))
            return httpx.Response(
                200,
                request=req,
                json={
                    "providers": {
                        "airport": {
                            "type": "Proxy",
                            "proxies": [
                                {"name": "A", "alive": True},
                                {"name": "B", "alive": False},
                            ],
                        }
                    }
                },
            )
        return original_request(method, path, **kwargs)

    fake.request = request  # type: ignore[method-assign]

    providers = api.proxy_providers()
    api.update_proxy_provider("a/b")
    api.healthcheck_proxy_provider("a/b")
    api.flush_dns_cache()
    api.flush_fakeip_cache()

    assert len(providers["airport"]["proxies"]) == 2
    paths = [(method, path) for method, path, _ in fake.calls]
    assert ("PUT", "/providers/proxies/a%2Fb") in paths
    assert ("GET", "/providers/proxies/a%2Fb/healthcheck") in paths
    assert ("POST", "/cache/dns/flush") in paths
    assert ("POST", "/cache/fakeip/flush") in paths


def test_rule_toggle_and_dns_query_endpoints() -> None:
    api = MihomoApi("http://127.0.0.1:9090")
    fake = FakeClient()
    api._client = fake  # type: ignore[assignment]

    original_request = fake.request

    def request(method: str, path: str, **kwargs):
        if path == "/dns/query":
            req = httpx.Request(method, f"http://localhost{path}")
            fake.calls.append((method, path, kwargs))
            return httpx.Response(
                200,
                request=req,
                json={
                    "Status": 0,
                    "Answer": [
                        {"name": "example.com.", "type": 1, "TTL": 60, "data": "1.2.3.4"}
                    ],
                },
            )
        return original_request(method, path, **kwargs)

    fake.request = request  # type: ignore[method-assign]

    api.set_rule_disabled(12, True)
    result = api.dns_query("example.com", "A")

    rule_call = next(call for call in fake.calls if call[1] == "/rules/disable")
    dns_call = next(call for call in fake.calls if call[1] == "/dns/query")

    assert rule_call[0] == "PATCH"
    assert rule_call[2]["json"] == {"12": True}
    assert dns_call[2]["params"] == {"name": "example.com", "type": "A"}
    assert result["Answer"][0]["data"] == "1.2.3.4"
