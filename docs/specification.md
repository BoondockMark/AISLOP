# Multi-SDR RF Lab product and protocol specification

**Package/server version:** 1.0.0
**RF API contract:** 1.0, stable
**Protocol:** Model Context Protocol (MCP)
**Transport:** Streamable HTTP by default; local stdio optionally

## Product boundary

The supported application in the `aislop-sdr` distribution is the `rf-mcp`
Multi-SDR RF Lab server. It is a receive-only RF acquisition, analysis, and
station-automation application with an MCP tool API and, in HTTP mode, a web
dashboard and JSON/live-stream endpoints. It is not merely a filesystem
observer and it is not read-only with respect to its own data: it records a
catalog, artifacts, settings, schedules, alerts, and observations and can launch
receiver and decoder subprocesses.

It requires CPython 3.12 or 3.13. The wheel contains NumPy/SciPy DSP,
Matplotlib/Pillow artifact generation, Starlette/Uvicorn web service code, and
the MCP Python SDK (`mcp>=1.30.0,<2`). Skyfield-backed satellite prediction is
optional through `aislop-sdr[satellite]`.

## Runtime and hardware

The Python application is release-tested on 64-bit Windows, macOS, and
Ubuntu/glibc Linux. The supported service deployment and integration scripts
are Linux/systemd-specific. Supported receiver adapters are:

| Backend | External programs | Implemented tuning/sample contract |
| --- | --- | --- |
| Airspy HF+ (`airspyhf`) | `airspyhf_info`, `airspyhf_rx` | 9 kHz–31 MHz and 60–260 MHz; 768 ksample/s |
| RTL-SDR (`rtl_sdr`) | `rtl_test`, `rtl_sdr` | 24 MHz–1.766 GHz; 225,001–3,200,000 sample/s |

Drivers, device access, suitable antennas, and the utilities above are operator
requirements, not wheel dependencies. `list_devices`,
`discover_attached_sdr_devices`, and coordinator tools expose availability.
Radio reception is never required for package verification: the packaged
`FakeStreamingReceiverBackend` can be explicitly registered by a test/demo
bootstrap and emits a deterministic IQ tone. It is not enabled by a production
flag and must not be mistaken for attached hardware.

## Configuration and endpoints

`rf-mcp` has `--help` and `--version`; it reads runtime configuration from the
environment. `RF_MCP_TRANSPORT` defaults to `streamable-http` and may be set to
`stdio`. HTTP uses `RF_MCP_HOST` (default `127.0.0.1`) and `RF_MCP_PORT`
(default `8765`). The routes are:

- `/mcp`: MCP Streamable HTTP endpoint;
- `/` and `/dashboard`: dashboard document;
- `/assets/rf-dashboard.css` and `/assets/rf-dashboard.js`: packaged assets;
- `/health` and `/healthz`: unauthenticated readiness/status;
- `/api/...`: dashboard operations, catalog views, and live audio/waterfall; and
- `/artifacts/<id>` and `/sstv-images/<id>`: catalog-mediated downloads.

`RF_MCP_API_TOKEN`, when set, must be at least 32 characters and contain only
ASCII letters, digits, dot, underscore, tilde, or hyphen. It protects all HTTP
routes except health. MCP and non-browser API clients send a bearer header; the
dashboard can exchange the token for a process-local, 12-hour, HttpOnly,
SameSite=Strict session cookie. An API token is invalid with stdio transport.
There is no TLS termination, user identity, role, or scope system. A non-loopback
bind therefore requires a trusted TLS reverse proxy, firewall, dedicated OS
account, and external access policy.

## RF API contract

`get_rf_api_contract` is the machine-readable authority. It declares Hz for
frequency, UTC ISO 8601 timestamps, and relative digital-domain measurements by
default. A dBm claim requires saved calibration with a documented reference
source. Clients must ignore unknown response fields and handle documented error
types.

The compatibility-guaranteed v1 core consists of:

- contract, health, and release-readiness tools;
- receiver device discovery, saved receiver inventory, selection, and
  qualification;
- `inspect_spectrum`, `analyze_signal`, and `receive_broadcast_fm`;
- receiver calibration save/get/list operations; and
- persistent RF job, artifact, storage, and recovery queries.

Installed discovery also advertises specialized tools for multi-receiver
coordination, admission queues, live listening/waterfall, station memory,
monitoring and scans, presets and schedules, alerts and webhooks, native digital
analysis, external weak-signal/Fldigi/SSTV decoding, recording sessions,
propagation, satellite planning/reception/telemetry, classification, and signal
fingerprints. These tools have real side effects in the application data root
and/or attached receiver. Clients must use MCP discovery for their exact JSON
schemas; this document deliberately does not duplicate hundreds of generated
fields.

The API contract describes how a hypothetical later version would evolve:
minor versions may add tools, optional parameters, enum values, and response
fields; patches fix defects without intentional contract changes; removals or
required-field changes require a major version, with at least one minor release
of deprecation notice. This compatibility language does **not** promise another
release; project policy currently supports only the unmaintained 1.0.0 release.

## Jobs, catalog, and artifacts

`RF_MCP_DATA_DIR` defaults to `~/SDR-MCP-data`. The catalog is
`SDR-MCP.sqlite3`, configured for SQLite WAL. It persists jobs, artifacts,
receivers, calibrations, presets, schedules, alerts, webhook destinations and
deliveries, station memories, recording sessions, decoder records, satellite
state, and other station metadata. Startup marks abandoned running jobs as
interrupted so recovery status is observable.

Payload files are stored below the same root in `captures`, `plots`, `results`,
`audio`, `fm-surveys`, `weak-signal`, `fldigi`, `sstv`, and `satellite` trees.
Artifact tools expose cataloged files and explicit pin/cleanup operations.
Deleting jobs, records, sessions, or old artifacts is a write/destructive action
and may require a `confirm_delete`-style parameter. Backups must capture the
SQLite database and artifact tree consistently. Neither wheel uninstall nor
process shutdown removes them.

## Subprocess integrations

Receiver backends execute fixed-structure argument arrays for their selected
utilities and stream IQ from subprocess pipes. Optional decoders execute:

- WSJT-X command-line programs (`jt9`, `jt4`, `wsprd`) for supported weak modes;
- Fldigi via its XML-RPC service plus a configured tokenized playback argument;
- the `sstv` command-line WAV decoder; and
- `ffmpeg` for encoded live dashboard audio.

Executable paths/names may be configured with the documented `RF_MCP_*`
variables in the relevant capability output and installer scripts. Input values
must never be concatenated into a shell command. Decoder availability and output
are diagnostic evidence, not guaranteed signal identification.

## Deterministic acceptance

The canonical post-install sequence is in the README. It checks `rf-mcp
--version`, polls `/healthz`, downloads the authenticated dashboard JavaScript,
initializes MCP and discovers the stable tools, registers the packaged fake as
the default receiver, calls `list_devices` and `inspect_spectrum`, and verifies
the SQLite catalog/artifact files. This is the release acceptance path on every
supported OS/Python pair and requires no physical radio.

## Legacy workspace observer

The distribution retains `aislop` solely for compatibility. It is a separate
bounded filesystem observer exposing `inspect_path`, `scan_text`, and
`observe_changes` over stdio or authenticated Streamable HTTP. It requires one
or more `--allow-root` arguments; its HTTP defaults are `127.0.0.1:8000`,
endpoint `/mcp`, and token variable `AISLOP_AUTH_TOKEN`. It creates no persistent
index. These command names, port, variables, capabilities, and threat model do
not apply to `rf-mcp`; no new radio documentation or host configuration should
use them.
