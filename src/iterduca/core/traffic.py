from __future__ import annotations

import json
import threading
from collections.abc import Callable

import websocket


TrafficCallback = Callable[[int, int], None]
ErrorCallback = Callable[[str], None]


class TrafficMonitor:
    """Consume Mihomo's /traffic WebSocket on a daemon thread."""

    def __init__(self, url: str, secret: str, callback: TrafficCallback, error_callback: ErrorCallback | None = None) -> None:
        self.url = url
        self.secret = secret
        self.callback = callback
        self.error_callback = error_callback or (lambda _: None)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        headers = [f"Authorization: Bearer {self.secret}"] if self.secret else []
        while not self._stop.is_set():
            try:
                ws = websocket.create_connection(self.url, header=headers, timeout=3)
                try:
                    while not self._stop.is_set():
                        payload = json.loads(ws.recv())
                        self.callback(int(payload.get("up", 0)), int(payload.get("down", 0)))
                finally:
                    ws.close()
            except Exception as exc:  # network boundary; reconnect is intentional
                self.error_callback(str(exc))
                self._stop.wait(1.0)
