from __future__ import annotations

import sys
import tomllib
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    with (root / "pyproject.toml").open("rb") as handle:
        version = str(tomllib.load(handle)["project"]["version"])

    parts = [int(part) for part in version.split(".")]
    if len(parts) != 3:
        raise ValueError("Iterduca release version must use MAJOR.MINOR.PATCH")
    version_tuple = (*parts, 0)

    output = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "build" / "version_info.txt"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_tuple},
    prodvers={version_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', 'ZJY-HSBL'),
          StringStruct('FileDescription', 'Iterduca Network Routing Client'),
          StringStruct('FileVersion', '{version}'),
          StringStruct('InternalName', 'Iterduca'),
          StringStruct('OriginalFilename', 'Iterduca.exe'),
          StringStruct('ProductName', 'Iterduca'),
          StringStruct('ProductVersion', '{version}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""",
        encoding="utf-8",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
