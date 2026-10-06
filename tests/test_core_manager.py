from pathlib import Path

from iterduca.core.manager import CoreManager


def test_build_command_uses_home_and_config() -> None:
    executable = Path("C:/tools/mihomo.exe")
    config = Path("C:/runtime/config.yaml")
    home = Path("C:/runtime")

    command = CoreManager.build_command(executable, config, home)

    assert command == [str(executable), "-d", str(home), "-f", str(config)]
