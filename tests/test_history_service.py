from pathlib import Path

from iterduca.services.history_service import HistoryService


def test_history_service_persists_and_caps_traffic(tmp_path: Path) -> None:
    path = tmp_path / "metrics.json"
    service = HistoryService(path, max_traffic_samples=10, max_latency_samples=5)

    for value in range(15):
        service.record_traffic(value, value * 2)
    service.flush()

    restored = HistoryService(path, max_traffic_samples=10, max_latency_samples=5)
    samples = restored.traffic()

    assert len(samples) == 10
    assert samples[0]["up"] == 5
    assert samples[-1]["down"] == 28


def test_latency_history_is_isolated_per_group_and_proxy(tmp_path: Path) -> None:
    service = HistoryService(tmp_path / "metrics.json", max_latency_samples=5)

    for delay in (10, 20, 30, 40, 50, 60):
        service.record_latency("Group A", "Node 1", delay)
    service.record_latency("Group A", "Node 2", 99)
    service.flush()

    first = service.latency("Group A", "Node 1")
    second = service.latency("Group A", "Node 2")

    assert [item["delay"] for item in first] == [20, 30, 40, 50, 60]
    assert [item["delay"] for item in second] == [99]


def test_history_clear_resets_persisted_data(tmp_path: Path) -> None:
    path = tmp_path / "metrics.json"
    service = HistoryService(path)
    service.record_traffic(1, 2)
    service.record_latency("A", "B", 30)
    service.clear()

    restored = HistoryService(path)
    assert restored.traffic() == []
    assert restored.latency("A", "B") == []
