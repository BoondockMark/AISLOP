# Changelog

All notable changes are recorded here. AISLOP uses [Semantic Versioning](https://semver.org/):
`MAJOR.MINOR.PATCH`, with standard prerelease identifiers such as `0.1.0-rc.1`.

## [Unreleased]

### Documentation

- Reframed installation and usage around the packaged `rf-mcp` Multi-SDR RF
  Lab application, its HTTP dashboard/MCP endpoint, supported receiver stacks,
  persistent data root, and authentication/host configuration.
- Added a deterministic installed-wheel verification procedure using the
  packaged fake receiver to check version, readiness, dashboard assets, MCP
  discovery, spectrum observation, and persistence without SDR hardware.
- Corrected the product specification and threat model for the stable RF API,
  SQLite catalog/artifacts, receiver and decoder subprocesses, outbound
  integrations, network exposure, and destructive data operations.
- Separated the retained `aislop` workspace observer as a legacy compatibility
  component and aligned security, maintenance, and release policy with the
  unmaintained 1.0.0-only lifecycle.

## [1.0.0] - 2026-09-07

### Added

- Packaged the `rf-mcp` Multi-SDR RF Lab receive-only radio server with its MCP
  RF tool API, network dashboard, JSON/live endpoints, persistent SQLite catalog,
  generated artifacts, hardware adapters, and optional subprocess decoders.
- Added Airspy HF+ and RTL-SDR receiver support plus an explicitly registered
  deterministic fake receiver for tests and demonstrations.
- Retained the earlier `aislop` bounded workspace observer as a separate legacy
  compatibility command.

[Unreleased]: https://github.com/BoondockMark/AISLOP/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/BoondockMark/AISLOP/releases/tag/v1.0.0
