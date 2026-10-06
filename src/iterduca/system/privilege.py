from __future__ import annotations

import ctypes
import os
import subprocess
import sys


def is_elevated() -> bool:
    if os.name == "nt":
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except OSError:
            return False

    geteuid = getattr(os, "geteuid", None)
    return bool(geteuid and geteuid() == 0)


def relaunch_elevated() -> bool:
    if os.name != "nt":
        return False

    if getattr(sys, "frozen", False):
        executable = sys.executable
        parameters = subprocess.list2cmdline(sys.argv[1:])
    else:
        executable = sys.executable
        parameters = subprocess.list2cmdline(["-m", "iterduca", *sys.argv[1:]])

    result = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        executable,
        parameters,
        None,
        1,
    )
    return int(result) > 32
