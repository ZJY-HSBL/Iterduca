from pathlib import Path

from iterduca.core.manager import CoreManager


def test_build_command_uses_home_and_config() -> None:
    command = CoreManager.build_command(
        Path("C:/tools/mihomo.exe"),
        Path("C:/runtime/config.yaml"),
        Path("C:/runtime"),
    )
    assert command == [
        "C:/tools/mihomo.exe",
        "-d",
        "C:/runtime",
        "-f",
        "C:/runtime/config.yaml",
    ]
