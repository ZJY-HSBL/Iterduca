from __future__ import annotations

import time
from collections import deque


class CoreRestartPolicy:
    def __init__(
        self,
        *,
        max_attempts: int = 3,
        window_seconds: float = 60.0,
    ) -> None:
        self.max_attempts = max(1, int(max_attempts))
        self.window_seconds = max(1.0, float(window_seconds))
        self._attempts: deque[float] = deque()

    def allow(self, now: float | None = None) -> bool:
        moment = time.monotonic() if now is None else float(now)
        threshold = moment - self.window_seconds
        while self._attempts and self._attempts[0] <= threshold:
            self._attempts.popleft()
        if len(self._attempts) >= self.max_attempts:
            return False
        self._attempts.append(moment)
        return True

    def remaining(self, now: float | None = None) -> int:
        moment = time.monotonic() if now is None else float(now)
        threshold = moment - self.window_seconds
        while self._attempts and self._attempts[0] <= threshold:
            self._attempts.popleft()
        return max(0, self.max_attempts - len(self._attempts))
