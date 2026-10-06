# Changelog

All notable changes to Iterduca are documented here.

The project follows Semantic Versioning.

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
