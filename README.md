# Iterduca

**Modern Network Routing Client**

Iterduca is a Windows-first desktop proxy and network routing client built with Python and PyQt6. It uses Mihomo as an external routing core and keeps the desktop application, profile management, runtime configuration, system integration, and core process lifecycle clearly separated.

> Current version: **v0.2.0**

[中文说明](README.zh-CN.md)

## Why Iterduca

Iterduca is not a fork or a reskin of another desktop client. The application layer is implemented independently around a small core-adapter boundary. The current adapter targets Mihomo, while the UI and profile model are intentionally kept separate from the core process.

The name **Iterduca** comes from the Latin idea of guiding a journey: each connection is guided through the appropriate route to its destination.

## v0.2.0 features

- PyQt6 desktop interface with a compact dark UI
- Imported YAML profile management
- Immutable source profiles and disposable runtime configuration
- Mihomo process start/stop lifecycle
- Local Controller API with an automatically generated secret
- Rule / Global / Direct mode switching
- Proxy group discovery and node switching\n- Selected-node latency testing\n- Live connection inspection with per-connection and close-all controls\n- Rule table with client-side filtering\n- Subscription URL import and in-place profile refresh
- Real-time upload/download traffic through the Controller WebSocket
- Mihomo stdout log viewer
- Windows WinINet system proxy enable/restore
- System tray with show/start/stop/quit actions
- Persistent local settings
- Unit tests for configuration, profiles, settings, and core command generation
- Windows GitHub Actions CI

## Architecture

```text
┌────────────────────────────────────┐
│            PyQt6 Desktop           │
│ Overview · Proxies · Profiles      │
│ Logs · Settings · System Tray      │
└─────────────────┬──────────────────┘
                  │
          Application Services
                  │
      ┌───────────┴───────────┐
      │                       │
Profile / Settings      Mihomo Adapter
      │                REST + WebSocket
      │                       │
Runtime Config          Core Lifecycle
      │                       │
      └───────────┬───────────┘
                  │
             Mihomo Core
```

The imported profile is never edited in place. Iterduca writes a separate runtime `config.yaml` and injects only application-owned values such as `mixed-port`, `external-controller`, `secret`, and routing mode.

## Requirements

- Windows 10/11
- Python 3.12+
- Mihomo executable

Mihomo is **not bundled** in this repository. Download it from the official MetaCubeX/mihomo project and select the executable in **Settings**.

Official project: https://github.com/MetaCubeX/mihomo

## Run from source

```powershell
git clone https://github.com/ZJY-HSBL/Iterduca.git
cd Iterduca
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m iterduca
```

Alternatively:

```powershell
.\scripts\run.ps1
```

## First run

1. Open **Settings** and select your Mihomo executable.
2. Set the mixed port and Controller port if the defaults conflict with another application.
3. Open **Profiles** and import a valid Mihomo/Clash-compatible YAML profile.
4. Select the profile and click **Use selected**.
5. Return to **Overview** and click **Start core**.
6. Enable Windows system proxy in Settings if you want applications using the system proxy to route through Iterduca.

The Controller is forced to `127.0.0.1` in v0.1.0 and receives a fresh random secret for each runtime configuration.

## Project structure

```text
Iterduca/
├── src/iterduca/
│   ├── core/          # Mihomo API, process and runtime config
│   ├── models/        # Application data models
│   ├── services/      # Profile and settings services
│   ├── system/        # Windows system integration
│   └── ui/            # PyQt6 window, pages and theme
├── tests/
├── scripts/
└── .github/workflows/
```

## Tests

```powershell
python -m pytest
python -m ruff check src tests
```

## Roadmap

The next milestones are connection inspection, rules and rule-provider views, subscription URL updates, latency testing, core update management, configuration overrides, TUN mode, traffic history, and Windows packaging/signing.

TUN support is intentionally not part of the first MVP because it requires a separate privilege, routing, DNS, and recovery design rather than being treated as a simple toggle.

## Security design

Iterduca defaults the Mihomo Controller to loopback only and uses a generated bearer secret. Imported profiles are preserved as source material and are not overwritten. The application does not upload profiles, subscription contents, traffic data, or logs to an Iterduca service.

Profiles can contain sensitive server credentials. Do not commit personal profiles to Git repositories.

## License

Iterduca is released under the MIT License. Mihomo is an independent project and is distributed under its own license.
