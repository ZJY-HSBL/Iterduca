import sys

from iterduca.system.startup import StartupService


def test_startup_command_uses_background_mode(monkeypatch) -> None:
    monkeypatch.delattr(sys, "frozen", raising=False)
    command = StartupService().command()

    assert "-m" in command
    assert "iterduca" in command
    assert "--background" in command
