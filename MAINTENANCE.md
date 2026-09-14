# Maintenance and release policy

## Lifecycle and version support

AISLOP is unmaintained after its initial release:

- `aislop-sdr` 1.0.0 is the only planned package release (PyPI publication is
  pending, and the repository-install instructions remain available meanwhile);
- no version receives bug, compatibility, dependency, decoder, hardware,
  operating-system, or security fixes;
- no response, review, disclosure, or release timetable is promised; and
- users must evaluate, isolate, patch/fork, or replace the software themselves.

The RF API reports contract version 1.0 and Semantic Versioning compatibility
rules so clients can interpret the installed server. Those rules constrain any
hypothetical future release; they are not a commitment to produce or support
one. The RF API version is distinct from the package version.

The supported-at-release runtime matrix is CPython 3.12/3.13 on 64-bit Windows,
macOS, and glibc Linux. The systemd deployment and decoder integration are
Linux-specific, and real receivers additionally depend on external drivers and
utilities. “Supported at release” means acceptance was run for 1.0.0, not that
future OS, Python, hardware, decoder, or browser changes will be addressed.

## Components

`rf-mcp` and its dashboard are the packaged radio application. The `aislop`
workspace-observer entry point remains a compatibility component only; it does
not expand the support policy and must not be confused with the RF API.
Persistent RF data under `RF_MCP_DATA_DIR` is owned and retained by the operator;
uninstall and project abandonment do not migrate, repair, or delete it.

## Contributions and release authority

Outside contributions are not accepted. Issues and pull requests create no
obligation to review, merge, respond, or release. Only the repository owner may
approve a release by creating its version tag. Only the owner or an automation
identity authorized through the protected release environment may publish.
Passing CI is necessary for a hypothetical release but is not approval or a
support promise.

Package ownership will not be transferred merely because the project is
unmaintained. Any future policy change, maintainer transfer, or release must be
announced in the repository and package registry in a committed replacement for
this policy; users must not rely on it beforehand.
