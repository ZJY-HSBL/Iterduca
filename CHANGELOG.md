# Changelog

All notable changes to Iterduca are documented here.

The project follows Semantic Versioning.

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
