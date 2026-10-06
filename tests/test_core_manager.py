from pathlib import Path

from iterduca.core.manager import CoreManager


def test_build_command_uses_home_and_config() -> None:
    executable = Path("C:/tools/mihomo.exe")
    config = Path("C:/runtime/config.yaml")
    home = Path("C:/runtime")

    command = CoreManager.build_command(executable, config, home)

    assert command == [str(executable), "-d", str(home), "-f", str(config)]


def test_validate_uses_mihomo_test_flag(tmp_path: Path, monkeypatch) -> None:
    executable = tmp_path / "mihomo.exe"
    config = tmp_path / "config.yaml"
    home = tmp_path / "runtime"
    executable.write_text("", encoding="utf-8")
    config.write_text("proxies: []\n", encoding="utf-8")

    captured = {}

    class Result:
        returncode = 0
        stdout = "configuration test is successful"
        stderr = ""

    def fake_run(command, **kwargs):
        captured["command"] = command
        return Result()

    monkeypatch.setattr("subprocess.run", fake_run)
    CoreManager().validate(executable, config, home)

    assert captured["command"][1] == "-t"
    assert "-f" in captured["command"]
    assert "-d" in captured["command"]


def test_validate_rejects_invalid_config(tmp_path: Path, monkeypatch) -> None:
    executable = tmp_path / "mihomo.exe"
    config = tmp_path / "config.yaml"
    executable.write_text("", encoding="utf-8")
    config.write_text("bad: config\n", encoding="utf-8")

    class Result:
        returncode = 1
        stdout = "configuration test failed"
        stderr = "invalid config"

    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: Result())

    import pytest

    with pytest.raises(RuntimeError, match="configuration test failed"):
        CoreManager().validate(executable, config, tmp_path / "runtime")


def test_version_uses_mihomo_version_flag(tmp_path: Path, monkeypatch) -> None:
    executable = tmp_path / "mihomo.exe"
    executable.write_text("", encoding="utf-8")
    captured = {}

    class Result:
        returncode = 0
        stdout = "Mihomo Meta v1.2.3 windows amd64"
        stderr = ""

    def fake_run(command, **kwargs):
        captured["command"] = command
        return Result()

    monkeypatch.setattr("subprocess.run", fake_run)
    version = CoreManager().version(executable)

    assert captured["command"][1] == "-v"
    assert version.startswith("Mihomo Meta")
