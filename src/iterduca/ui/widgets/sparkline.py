from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtWidgets import QWidget


class Sparkline(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._primary: list[float] = []
        self._secondary: list[float] = []
        self.setMinimumHeight(120)

    def set_series(
        self,
        primary: list[int | float],
        secondary: list[int | float] | None = None,
    ) -> None:
        self._primary = [float(value) for value in primary][-180:]
        self._secondary = (
            [float(value) for value in secondary][-180:]
            if secondary is not None
            else []
        )
        self.update()

    def clear(self) -> None:
        self._primary = []
        self._secondary = []
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(8, 8, -8, -8)

        grid_pen = QPen(self.palette().mid().color())
        grid_pen.setStyle(Qt.PenStyle.DotLine)
        grid_pen.setWidthF(0.7)
        painter.setPen(grid_pen)
        for fraction in (0.25, 0.5, 0.75):
            y = rect.top() + rect.height() * fraction
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))

        all_values = self._primary + self._secondary
        if len(all_values) < 2:
            return

        maximum = max(max(all_values), 1.0)
        self._draw_series(
            painter,
            rect,
            self._primary,
            maximum,
            self.palette().highlight().color(),
        )
        if self._secondary:
            self._draw_series(
                painter,
                rect,
                self._secondary,
                maximum,
                self.palette().link().color(),
            )

    @staticmethod
    def _draw_series(
        painter: QPainter,
        rect: QRectF,
        values: list[float],
        maximum: float,
        color,
    ) -> None:
        if len(values) < 2:
            return
        pen = QPen(color)
        pen.setWidthF(2.0)
        painter.setPen(pen)

        points: list[QPointF] = []
        last_index = max(1, len(values) - 1)
        for index, value in enumerate(values):
            x = rect.left() + rect.width() * index / last_index
            y = rect.bottom() - rect.height() * max(0.0, value) / maximum
            points.append(QPointF(x, y))

        for first, second in zip(points, points[1:]):
            painter.drawLine(first, second)
