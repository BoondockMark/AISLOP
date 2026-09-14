# Security policy

## Supported versions

| Version | Security fixes |
| --- | --- |
| 1.0.0 | No (unmaintained) |
| Unreleased source snapshots and all other versions | No |

AISLOP has no supported release line. Version 1.0.0 is the only planned release;
its PyPI publication is pending. It receives no bug, dependency, compatibility,
or security updates. Users must assess, isolate, patch/fork, or replace it
themselves. Do not expose `rf-mcp` merely because a historical CI or release
check passed.

## Reporting a vulnerability

Do **not** include credentials, received content, device serials, locations, or
private catalog/artifact data in a public issue. GitHub's **Security** tab and
**Report a vulnerability** may be used to notify the owner privately, including
the affected version, transport/bind configuration, hardware/decoder stack,
impact, and a minimal reproduction. This channel does not promise an
acknowledgement, assessment, embargo, fix, advisory, or release.

For immediate risk, stop the service, remove network/device access, revoke the
bearer token and webhook secrets, preserve necessary forensic copies of both the
SQLite catalog/WAL and artifact tree, and rotate any downstream credentials.
The RF threat model and deployment controls are in
[`docs/security.md`](docs/security.md).
