# Changelog

All notable changes to Iterduca are documented here.

The project follows Semantic Versioning.

## [1.7.0] - 2026-10-08

### Added

- Case-insensitive proxy node search.
- Proxy sorting by profile order, name, or measured latency.
- Test-visible action for latency testing the current filtered node set.
- Proxy group coverage summary for visible, tested, and reachable nodes.
- Latency history minimum, average, and maximum statistics.
- Pure, unit-tested proxy filtering, sorting, and latency-statistics services.
- Automatic GitHub Release publishing when a validated release/vX.Y.Z branch is created.
- Bilingual release-process documentation.

### Changed

- Proxy list items now bind directly to their real proxy names, keeping selection, switching, latency testing, and history correct after filtering or sorting.
- Unavailable or untested nodes sort after successful measurements in latency mode.
- Release workflow validates the release branch/tag against the project version before publishing.
- Version metadata and bilingual documentation updated for v1.7.0.

## [1.6.0] - 2026-10-07

### Added

- Optional Mihomo Core auto-start when Iterduca launches.
- Optional automatic restart after an unexpected Mihomo Core exit.
- Dedicated Core restart policy with a maximum of three attempts per 60-second window.
- System tray notifications for unexpected Core exits, scheduled recovery, background start success/failure, and restart-loop suppression.
- Diagnostics metadata for Core auto-start, crash recovery, subscription auto-update, and window-behavior settings.
- Regression coverage for restart rate limiting and startup/recovery setting persistence.

### Changed

- Core startup now has separate interactive and background paths so automatic startup failures never open blocking modal dialogs.
- Manual Stop cancels any pending automatic crash-recovery restart.
- System tray tooltip and Start/Stop action enabled state now follow the actual Core state.
- Unexpected Core exits restore runtime/network state before a recovery attempt is scheduled.
- Version metadata and bilingual documentation updated for v1.6.0.

## [1.5.0] - 2026-10-07

### Added

- Verified Iterduca application update downloads from GitHub Releases.
- Exact Windows Setup asset selection for the latest Iterduca version.
- SHA-256 checksum verification against `SHA256SUMS.txt`.
- Independent cross-check against GitHub Release Asset `digest` metadata.
- 256 MiB installer download safety limit and atomic temporary-file replacement.
- Explicit Download & Install control in Tools.
- Regression coverage for exact asset selection, untrusted URL rejection, verified download, tamper rejection, and digest-manifest disagreement.

### Changed

- Application updates are never installed silently; installation requires explicit user confirmation after verification.
- Iterduca stops the Mihomo Core and restores owned runtime state before launching the verified Setup installer.
- Core setup documentation now reflects the built-in managed Core workflow introduced in v1.4.
- GitHub Release text now explains managed Core installation instead of requiring manual Mihomo setup.
- Version metadata and bilingual documentation updated for v1.5.0.

## [1.4.0] - 2026-10-07

### Added

- Built-in Windows x64 Mihomo Core Manager.
- Latest release discovery through the official MetaCubeX/mihomo GitHub Release API.
- Exact selection of the generic `mihomo-windows-amd64-vX.Y.Z.zip` release asset.
- Mandatory SHA-256 verification using GitHub Release Asset digest metadata.
- Streamed Core downloads with archive and binary size limits.
- Atomic managed-Core installation under the Iterduca application-data directory.
- Post-install `mihomo -v` verification before selecting the managed Core.
- Core update progress and latest-version status in Settings.
- Regression tests for release selection, digest requirements, verified extraction, hash mismatch rejection, and version comparison.

### Changed

- Managed Core installation never overwrites a user-selected external Mihomo binary.
- Iterduca prefers its managed Core when the configured Core path is absent or stale.
- Invalid configured Core paths automatically fall back to managed/local/PATH discovery.
- Core replacement is refused while the current Core is running.
- Version metadata and bilingual documentation updated for v1.4.0.

## [1.3.0] - 2026-10-07

### Added

- Subscription quota metadata parsed from the common `subscription-userinfo` response header.
- Persisted upload, download, total quota, and expiry timestamp metadata.
- Used/total/remaining traffic information in the Profiles page.
- Seven-day subscription expiry warning.
- Optional automatic refresh for all subscriptions.
- Configurable subscription refresh interval from 1 to 168 hours.
- Regression coverage for subscription metadata parsing, persistence, malformed metadata, interval persistence, and interval clamping.

### Changed

- Background subscription updates run off the Qt main thread and log failures instead of opening modal dialogs.
- Manual and automatic update-all tasks share an in-flight guard to prevent duplicate concurrent refreshes.
- Corrupt persisted quota values safely fall back to zero instead of breaking Profile loading.
- Version metadata and bilingual documentation updated for v1.3.0.

## [1.2.0] - 2026-10-07

### Added

- Detailed Profile statistics for proxy nodes, proxy groups, rules, Proxy Providers, Rule Providers, and file size.
- Subscription update timestamps in the Profiles interface.
- Multi-file YAML import.
- Drag-and-drop YAML Profile import.
- Per-user Windows Setup installer built with Inno Setup.
- Dedicated Installer CI that performs a real PyInstaller + Inno Setup build and verifies generated artifacts.
- Installer CI is retriggered whenever project version metadata changes.

### Changed

- Profiles now expose richer configuration structure information instead of only proxy counts.
- Release workflow uploads the Setup installer alongside the standalone EXE, portable ZIP, and checksum manifest.
- Windows installation defaults to the current user's local Programs directory and does not require elevation.
- Version metadata and bilingual documentation updated for v1.2.0.

## [1.1.0] - 2026-10-07

### Added

- Persistent upload/download traffic history.
- Lightweight QPainter-based traffic chart on Overview without an additional charting dependency.
- Persistent per-group/per-node latency history with bounded sample retention.
- Latency-history chart for the currently selected proxy node.
- Connections search across host, process, network, chain, and rule fields.
- Sortable Connections columns with numeric ordering for upload/download values.
- Regression coverage for traffic/latency history persistence and retention limits.

### Changed

- Traffic history is sampled every five seconds and flushed periodically instead of writing on every WebSocket event.
- History data is atomically flushed on core shutdown.
- Connection row payloads are bound to table items so sorting cannot desynchronize the detail panel or close action.
- Version metadata and bilingual documentation updated for v1.1.0.

## [1.0.0] - 2026-10-07

### Added

- Crash-safe Windows system-proxy ownership state persisted to disk.
- Startup recovery that restores the previous system proxy only when Iterduca still owns the configured proxy and its local endpoint is no longer alive.
- Safe configuration/Profile backup export and guarded restore with strict archive-member validation.
- Privacy-conscious diagnostics export that excludes Profiles, subscription URLs, runtime configuration, controller secrets, and raw log contents.
- Local Mixed Port / Controller Port conflict detection before Mihomo startup.
- User-facing minimize-to-tray preference.
- CI validation for `develop/**` branches.
- Regression coverage for system-proxy recovery decisions, backup restore security, diagnostics privacy, and local port preflight.

### Changed

- UI version display now derives from `APP_VERSION` instead of a hard-coded label.
- Backup restore reloads Settings, Profiles, Overrides, TUN state, and Windows startup preference after stopping the core.
- v1.0.0 is the first stable Windows-first baseline release.

## [0.9.0] - 2026-10-07

### Added

- Persistent rotating application and Mihomo runtime logs.
- Restore of recent persisted log lines into the Logs page after restart.
- Log export and persistent-log clearing controls.
- Full raw Controller payload detail panel for Connections.
- Full raw Controller payload detail panel for Rules.
- Read-only GitHub Releases update checker with semantic-version comparison.
- Regression coverage for log rotation/export/tail and release-version checks.

### Changed

- All internal Iterduca log events now flow through one UI + persistent-log sink.
- Update checking does not download or execute release assets.
- Version metadata and bilingual documentation updated for v0.9.0.

## [0.8.0] - 2026-10-07

### Added

- Temporary rule enable/disable control using Mihomo `/rules/disable`.
- Rules table columns for index, current state, and hit count.
- DNS Query diagnostics using the current Mihomo `/dns/query` API.
- Structured DNS result viewer for common record types.
- Regression tests for rule-state PATCH payloads and DNS query parameters.

### Changed

- Rules page now clearly states that disabled state resets after core restart.
- DNS diagnostics run off the Qt main thread.
- Version metadata and bilingual documentation updated for v0.8.0.

## [0.7.0] - 2026-10-07

### Added

- Proxy Providers page backed by the current Mihomo `/providers/proxies` API.
- Selected-provider update, bounded-concurrency bulk update, and provider healthcheck.
- Provider proxy-count and alive-count summary.
- Tools page for DNS cache flush and Fake-IP cache flush.
- Regression coverage for proxy-provider and cache maintenance endpoints.

### Changed

- Provider updates refresh both provider metadata and proxy groups.
- Version metadata and bilingual documentation updated for v0.7.0.

## [0.6.0] - 2026-10-07

### Added

- Rule Providers page backed by the current Mihomo `/providers/rules` API.
- Refresh, selected-provider update, and bounded-concurrency bulk provider update.
- Live Mihomo core memory metric on Overview.
- Safe local Profile deletion with path confinement.
- Subscription metadata cleanup for deleted profiles.
- Regression tests for rule providers, memory, profile deletion, and subscription cleanup.

### Changed

- Subscription request User-Agent now follows the current Iterduca version.
- Active Profile deletion stops the core and clears `active_profile` before file removal.
- Memory polling ignores stale results after core shutdown.
- Version metadata and bilingual documentation updated for v0.6.0.

## [0.5.0] - 2026-10-07

### Added

- Single-instance process guard using local Qt IPC.
- Existing-window activation when Iterduca is launched a second time.
- Windows startup integration with background tray launch.
- Mihomo executable auto-discovery from local directories and PATH.
- Mihomo version detection through the core `-v` command.
- Settings controls for core detection, version inspection, and Windows startup.
- Windows executable version-resource generation.
- Release packaging for standalone EXE, portable ZIP, and SHA256 checksum manifest.
- CI coverage for core discovery, startup command generation, core version detection, and version metadata generation.

### Changed

- Background startup no longer opens the main window when a system tray is available.
- Release artifacts now carry product/file version metadata.
- Version metadata and bilingual documentation updated for v0.5.0.

## [0.4.0] - 2026-10-07

### Added

- Windows TUN management page with administrator privilege detection.
- UAC relaunch path for TUN startup.
- Managed TUN configuration for mips, system, gvisor, and mixed stacks.
- Auto-route, automatic outbound-interface detection, DNS hijack, and strict-route settings.
- Optional RFC1918, loopback, link-local, and IPv6 local-network exclusions.
- Safe standard-mode recovery action for disabling TUN without deleting arbitrary system routes.
- Mihomo `-t` configuration preflight before core startup.
- Regression tests for TUN ownership, private-network bypass, and configuration validation.

### Changed

- TUN defaults to the current Mihomo-recommended `mips` stack.
- Iterduca-owned TUN fields take precedence over profile and override values.
- Windows system proxy is not enabled while TUN mode is active.
- Version metadata and bilingual documentation updated for v0.4.0.

## [0.3.0] - 2026-10-07

### Added

- Runtime YAML override editor with persistent local storage.
- Recursive deep-merge for nested Mihomo configuration sections.
- Protected application-owned runtime keys for Controller address, secret, mode, and mixed port.
- Full proxy-group latency testing with bounded background concurrency.
- Bulk update for all registered subscriptions.
- Automatic connection refresh while the Connections page is visible.
- Regression coverage for override precedence and bulk subscription updates.

### Changed

- Runtime configuration generation now applies user overrides before Iterduca-owned safety values.
- Profiles and Proxies pages gained bulk workflow controls.
- Version metadata and bilingual documentation updated for v0.3.0.

## [0.2.0] - 2026-10-07

### Added

- Connections page with refresh, per-connection close, and close-all controls.
- Rules page with type, payload, proxy columns, and local filtering.
- Subscription URL import and update service with atomic profile replacement.
- Selected proxy latency testing through the Mihomo Controller.
- Controller API support for rule retrieval and single-connection deletion.
- Subscription lifecycle and Controller endpoint regression tests.

### Changed

- Expanded the main navigation for connection and rule management.
- Profile UI now identifies subscription-backed profiles.
- Version metadata and bilingual documentation updated for v0.2.0.

## [0.1.0] - 2026-10-07

### Added

- Initial Windows-first PyQt6 desktop client.
- Mihomo core lifecycle management.
- YAML profile import and immutable source-profile handling.
- Disposable runtime configuration generation.
- Local Mihomo Controller API integration with generated bearer secret.
- Rule, Global, and Direct routing mode switching.
- Proxy-group discovery and node switching.
- Real-time upload and download traffic monitoring over WebSocket.
- Mihomo runtime log viewer.
- Windows system proxy enable and state restoration.
- Automatic cleanup when the Mihomo core exits unexpectedly.
- System tray controls.
- Persistent local settings.
- English and Chinese documentation.
- Windows CI with linting, GUI import smoke test, and unit tests.
