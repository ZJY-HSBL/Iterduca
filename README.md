# Iterduca

**Modern Network Routing Client**

Iterduca is a Windows-first desktop proxy and network routing client built with Python and PyQt6. It uses Mihomo as an external routing core and keeps the desktop application, profile management, runtime configuration, system integration, and core process lifecycle clearly separated.

> Current version: **v1.0.0**

[中文说明](README.zh-CN.md)

## Why Iterduca

Iterduca is not a fork or a reskin of another desktop client. The application layer is implemented independently around a small core-adapter boundary. The current adapter targets Mihomo, while the UI and profile model are intentionally kept separate from the core process.

The name **Iterduca** comes from the Latin idea of guiding a journey: each connection is guided through the appropriate route to its destination.

## v1.0.0 features

- PyQt6 desktop interface with a compact dark UI
- Imported YAML profile management
- Immutable source profiles and disposable runtime configuration
- Mihomo process start/stop lifecycle
- Local Controller API with an automatically generated secret
- Rule / Global / Direct mode switching
- Proxy group discovery and node switching\n- Selected-node and full proxy-group latency testing\n- Live connection inspection with per-connection and close-all controls\n- Rule table with client-side filtering\n- Subscription URL import, in-place refresh, and bulk update\n- Runtime YAML override editor with nested deep-merge semantics\n- Automatic Connections refresh while the page is visible
- Windows TUN management page with elevation status and UAC relaunch
- Managed TUN stacks: mips, system, gvisor, and mixed
- TUN auto-route, outbound-interface detection, DNS hijack, and strict-route controls
- Optional private/link-local network exclusions for LAN access
- Mihomo `-t` preflight validation before every core start
- Safe TUN recovery path that disables TUN and returns to standard proxy mode
- WinINet system proxy is not layered on top of TUN mode
- Single-instance desktop process with local activation IPC
- Windows startup integration with background tray launch
- Mihomo core auto-discovery from the app directory, working directory, and PATH
- Mihomo core version inspection from Settings
- Versioned Windows executable metadata for packaged builds
- Release artifacts include standalone EXE, portable ZIP, and SHA256SUMS
- Rule Providers page with refresh, single update, and bulk update
- Live Mihomo core memory metric on Overview
- Safe local Profile deletion with active-core shutdown when required
- Subscription metadata cleanup when a profile is deleted
- Subscription HTTP User-Agent automatically follows the Iterduca version
- Proxy Providers page with refresh, selected update, bulk update, and healthcheck
- Provider table shows proxy count and currently alive nodes
- Runtime Tools page for DNS cache and Fake-IP cache maintenance
- Rules table shows rule index, enabled/disabled state, and hit count
- Temporary per-rule enable/disable control for the current Mihomo session
- DNS Query diagnostics for A / AAAA / CNAME / MX / TXT records
- Structured DNS response viewer in Tools
- Persistent rotating application/core logs stored under the Iterduca data directory
- Recent persistent logs restored into the Logs page after restart
- Log export and persistent-log clearing controls
- Full raw Controller payload inspector for selected connections
- Full raw Controller payload inspector for selected rules
- Read-only GitHub Releases update check with semantic version comparison
- Crash-safe Windows system-proxy recovery with persisted ownership state
- Configuration/Profile backup export and guarded restore
- Privacy-conscious diagnostics bundle without Profiles, subscription URLs, runtime configuration, controller secrets, or raw logs
- Local Mixed/Controller port conflict detection before Mihomo startup
- User-facing minimize-to-tray preference
- UI version display derived from the application version constant
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

## 1.0 baseline and future direction

v1.0.0 establishes the stable Windows-first baseline: profile/subscription management, proxy and provider control, connections, rules, TUN, runtime overrides, diagnostics, persistent logs, recovery safeguards, packaging, and release automation are integrated into one desktop client.

Post-1.0 work can focus on deeper traffic history/analytics, installer and code-signing improvements, localization, and additional core lifecycle tooling without changing the existing configuration model.

## Security design

Iterduca defaults the Mihomo Controller to loopback only and uses a generated bearer secret. Imported profiles are preserved as source material and are not overwritten. The application does not upload profiles, subscription contents, traffic data, or logs to an Iterduca service.

Profiles can contain sensitive server credentials. Do not commit personal profiles to Git repositories.

## License

Iterduca is released under the MIT License. Mihomo is an independent project and is distributed under its own license.
