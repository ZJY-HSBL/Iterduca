# Iterduca

**Modern Network Routing Client**

Iterduca is a Windows-first desktop proxy and network routing client built with Python and PyQt6. It uses Mihomo as an external routing core and keeps the desktop application, profile management, runtime configuration, system integration, and core process lifecycle clearly separated.

> Current version: **v1.7.0**

[中文说明](README.zh-CN.md)

## Why Iterduca

Iterduca is not a fork or a reskin of another desktop client. The application layer is implemented independently around a small core-adapter boundary. The current adapter targets Mihomo, while the UI and profile model are intentionally kept separate from the core process.

The name **Iterduca** comes from the Latin idea of guiding a journey: each connection is guided through the appropriate route to its destination.

## v1.7.0 features

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
- Persistent upload/download traffic history with a lightweight Overview chart
- Persistent per-node latency history with on-demand history charts
- Traffic history sampled in memory and periodically flushed to disk
- Connections search across host/process/network/chain/rule fields
- Stable sortable Connections rows, including numeric upload/download sorting
- Detailed Profile statistics for proxies, groups, rules, Proxy Providers, Rule Providers, and file size
- Subscription-backed Profiles display their latest update timestamp
- Multi-file YAML import and drag-and-drop Profile import
- Per-user Windows Setup installer generated with Inno Setup
- Installer CI performs real PyInstaller + Inno Setup packaging validation
- Subscription usage metadata parsed from the common subscription-userinfo response header
- Profiles display used traffic, total traffic, remaining quota, and expiry time when provided
- Seven-day expiry warning for subscription-backed Profiles
- Optional automatic subscription refresh with a configurable 1–168 hour interval
- Background subscription refresh avoids UI blocking and suppresses modal errors
- Manual and automatic update-all operations share an in-flight guard to prevent duplicate refresh jobs
- Built-in Mihomo Core Manager for Windows x64
- Latest Core discovery through the official MetaCubeX/mihomo GitHub Release API
- Exact generic windows-amd64 asset selection instead of CPU-tuned v1/v2/v3 variants
- Mandatory SHA-256 verification using GitHub Release Asset digest metadata before installation
- Managed Mihomo Core stored under Iterduca application data without overwriting user-selected external binaries
- Installed Core is validated with mihomo -v before being selected
- Invalid/stale configured Core paths automatically fall back to the managed Core, local discovery, or PATH
- Iterduca application update discovery through GitHub Releases
- Exact Windows Setup asset selection for the target Iterduca version
- Update downloads use a temporary file and a 256 MiB safety limit
- Setup installation requires SHA-256 agreement across GitHub Release Asset digest metadata, SHA256SUMS.txt, and the downloaded installer
- Untrusted/non-HTTPS update asset URLs are rejected before download
- Verified updates require explicit user confirmation; Iterduca never performs silent background installation
- Before launching a verified Setup update, Iterduca stops Mihomo and restores owned runtime/network state
- Optional Mihomo Core auto-start when Iterduca launches
- Optional automatic recovery after an unexpected Mihomo exit
- Crash recovery is rate-limited to 3 restart attempts per 60 seconds to prevent restart loops
- Manual Stop cancels a pending crash-recovery restart
- Automatic/background Core startup failures are logged and surfaced through the system tray instead of opening blocking dialogs
- System tray tooltip and Start/Stop actions follow the actual Core running state
- Tray notifications surface unexpected exits, scheduled recovery, successful background starts, and suppressed restart loops
- Privacy-safe diagnostics include Core startup/recovery preferences for troubleshooting
- Proxy nodes can be searched case-insensitively
- Proxy nodes can be displayed in profile order, alphabetical order, or fastest-latency order
- Filtered/sorted proxy actions bind to the real proxy name instead of a fragile list index
- Test all visible nodes without losing the current filter
- Proxy group summaries show visible, tested, and reachable node counts
- Latency history shows min/average/max statistics while ignoring timeout samples
- Creating a validated release/vX.Y.Z branch automatically publishes the matching Git tag and GitHub Release
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
- Python 3.12+ when running from source

Mihomo is not embedded in the Iterduca repository or application package. Iterduca can download the official Windows x64 Mihomo release on demand from MetaCubeX/mihomo, verify its SHA-256 digest, and manage it under the Iterduca application-data directory. You can also select your own external Mihomo executable in **Settings**; Iterduca never overwrites a user-selected external Core.

Official project: https://github.com/MetaCubeX/mihomo

## Windows releases

Each release can provide a standalone executable, a portable ZIP, and a per-user Setup installer. The installer places Iterduca under the current user's local Programs directory, so installation itself does not require administrator privileges. TUN elevation remains an explicit runtime action.

Maintainers: see [Release Process](docs/RELEASING.md). From v1.7.0 onward, creating a validated `release/vX.Y.Z` branch automatically publishes the matching Git tag and GitHub Release.

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

1. Open **Settings**. Use the built-in Core Manager to install the latest verified Windows x64 Mihomo Core, or select an external Mihomo executable.
2. Set the Mixed Port and Controller Port if the defaults conflict with another application.
3. Open **Profiles** and import a valid Mihomo/Clash-compatible YAML profile or add a subscription URL.
4. Select the Profile and click **Use selected**.
5. Return to **Overview** and click **Start core**.
6. Enable Windows System Proxy or TUN according to how you want traffic to enter Iterduca.

The Controller is always bound to `127.0.0.1` and receives a fresh random secret for each generated runtime configuration.

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
