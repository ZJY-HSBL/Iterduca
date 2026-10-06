from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from iterduca.models.settings import AppSettings


class TunPage(QWidget):
    save_requested = pyqtSignal(object)
    elevate_requested = pyqtSignal()
    recover_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel("TUN")
        title.setObjectName("Title")
        layout.addWidget(title)

        self.status = QLabel("TUN disabled")
        self.status.setObjectName("Metric")
        layout.addWidget(self.status)

        self.privilege = QLabel("")
        self.privilege.setObjectName("Muted")
        layout.addWidget(self.privilege)

        hint = QLabel(
            "TUN routes system traffic at the network layer. On Windows it requires "
            "administrator privileges. Iterduca uses Mihomo auto-route and never enables "
            "Linux-only auto-redirect on Windows."
        )
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        form = QFormLayout()

        self.enabled = QCheckBox("Enable TUN on next core start")
        form.addRow("TUN mode", self.enabled)

        self.stack = QComboBox()
        self.stack.addItems(["mips", "system", "gvisor", "mixed"])
        self.stack.currentTextChanged.connect(self._update_stack_note)
        form.addRow("Protocol stack", self.stack)

        self.stack_note = QLabel("")
        self.stack_note.setObjectName("Muted")
        self.stack_note.setWordWrap(True)
        form.addRow("", self.stack_note)

        self.auto_route = QCheckBox("Let Mihomo manage system routes")
        form.addRow("Auto route", self.auto_route)

        self.auto_detect = QCheckBox("Automatically detect outbound interface")
        form.addRow("Interface", self.auto_detect)

        self.dns_hijack = QCheckBox("Hijack UDP/TCP DNS on port 53")
        form.addRow("DNS hijack", self.dns_hijack)

        self.strict_route = QCheckBox("Enable strict route / Windows DNS leak protection")
        form.addRow("Strict route", self.strict_route)

        self.bypass_private = QCheckBox("Keep RFC1918/link-local networks outside TUN")
        form.addRow("Local network", self.bypass_private)

        layout.addLayout(form)

        self.save = QPushButton("Save TUN settings")
        self.save.setObjectName("PrimaryButton")
        self.save.clicked.connect(self._save)
        layout.addWidget(self.save)

        self.elevate = QPushButton("Restart Iterduca as administrator")
        self.elevate.clicked.connect(self.elevate_requested.emit)
        layout.addWidget(self.elevate)

        self.recover = QPushButton("Disable TUN and return to standard mode")
        self.recover.setObjectName("DangerButton")
        self.recover.clicked.connect(self.recover_requested.emit)
        layout.addWidget(self.recover)

        warning = QLabel(
            "Strict route can conflict with some virtualization/network software. "
            "Leave it off unless you specifically need Windows multi-homed DNS leak protection."
        )
        warning.setObjectName("Muted")
        warning.setWordWrap(True)
        layout.addWidget(warning)
        layout.addStretch(1)

    def load_settings(self, settings: AppSettings, elevated: bool, running: bool) -> None:
        self.enabled.setChecked(settings.tun_enabled)
        index = self.stack.findText(settings.tun_stack)
        self.stack.setCurrentIndex(max(0, index))
        self.auto_route.setChecked(settings.tun_auto_route)
        self.auto_detect.setChecked(settings.tun_auto_detect_interface)
        self.dns_hijack.setChecked(settings.tun_dns_hijack)
        self.strict_route.setChecked(settings.tun_strict_route)
        self.bypass_private.setChecked(settings.tun_bypass_private_networks)

        self.privilege.setText(
            "Administrator privileges: available"
            if elevated
            else "Administrator privileges: not available"
        )
        if running and settings.tun_enabled:
            self.status.setText("TUN active")
        elif settings.tun_enabled:
            self.status.setText("TUN enabled for next start")
        else:
            self.status.setText("TUN disabled")

        self.elevate.setVisible(not elevated)
        self.recover.setEnabled(settings.tun_enabled or running)
        self._update_stack_note(self.stack.currentText())

    def _update_stack_note(self, stack: str) -> None:
        if stack in {"system", "mixed"}:
            self.stack_note.setText(
                "Windows Defender Firewall must allow the Mihomo core when using "
                f"the {stack} stack."
            )
        elif stack == "mips":
            self.stack_note.setText(
                "MIPS is Mihomo's current default/recommended general-purpose stack."
            )
        else:
            self.stack_note.setText(
                "gVisor runs the network stack in user space for stronger isolation."
            )

    def _save(self) -> None:
        self.save_requested.emit(
            {
                "tun_enabled": self.enabled.isChecked(),
                "tun_stack": self.stack.currentText(),
                "tun_auto_route": self.auto_route.isChecked(),
                "tun_auto_detect_interface": self.auto_detect.isChecked(),
                "tun_dns_hijack": self.dns_hijack.isChecked(),
                "tun_strict_route": self.strict_route.isChecked(),
                "tun_bypass_private_networks": self.bypass_private.isChecked(),
            }
        )
