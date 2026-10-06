import socket

from iterduca.services import network_service


def test_find_port_conflicts_deduplicates_and_reports_used_ports(monkeypatch) -> None:
    monkeypatch.setattr(
        network_service,
        "tcp_port_in_use",
        lambda host, port, timeout=0.15: port in {7890, 9090},
    )

    conflicts = network_service.find_port_conflicts(
        "127.0.0.1",
        [7890, 9090, 7890, 10000],
    )

    assert conflicts == [7890, 9090]


def test_tcp_port_in_use_detects_listening_socket() -> None:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = listener.getsockname()[1]

    try:
        assert network_service.tcp_port_in_use("127.0.0.1", port) is True
    finally:
        listener.close()
