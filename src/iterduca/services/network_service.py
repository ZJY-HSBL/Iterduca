from __future__ import annotations

import socket


def tcp_port_in_use(host: str, port: int, timeout: float = 0.15) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def find_port_conflicts(host: str, ports: list[int]) -> list[int]:
    seen: set[int] = set()
    conflicts: list[int] = []
    for port in ports:
        value = int(port)
        if value in seen:
            continue
        seen.add(value)
        if tcp_port_in_use(host, value):
            conflicts.append(value)
    return conflicts
