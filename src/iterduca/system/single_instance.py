from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket


class SingleInstance(QObject):
    activated = pyqtSignal()

    def __init__(self, name: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.name = name
        self.server = QLocalServer(self)
        self.primary = self._claim()
        if self.primary:
            self.server.newConnection.connect(self._accept_connections)

    def _claim(self) -> bool:
        probe = QLocalSocket()
        probe.connectToServer(self.name)
        if probe.waitForConnected(150):
            probe.write(b"activate")
            probe.flush()
            probe.waitForBytesWritten(150)
            probe.disconnectFromServer()
            return False

        QLocalServer.removeServer(self.name)
        if not self.server.listen(self.name):
            raise RuntimeError(
                f"Unable to create the single-instance endpoint: {self.server.errorString()}"
            )
        return True

    def _accept_connections(self) -> None:
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            if socket is None:
                continue
            if socket.waitForReadyRead(100):
                message = bytes(socket.readAll())
                if message == b"activate":
                    self.activated.emit()
            socket.disconnectFromServer()
