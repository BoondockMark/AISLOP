# Multi-SDR RF Lab security architecture and release gate

## Scope and trust boundaries

`rf-mcp` is receive-only in the RF sense; it is **not** a read-only process. It
controls SDR receiver subprocesses, runs optional decoders, writes SQLite state
and artifacts, serves a network-facing dashboard/API/MCP endpoint, can schedule
work, and can deliver configured webhooks. Protected assets include the bearer
token, receiver access, station configuration, locations/schedules, webhook
secrets, raw IQ/audio/images, decoded content, catalog metadata, and service
availability.

1. MCP hosts, browsers, and API clients cross the HTTP boundary. Tool schemas
   validate structured arguments; dashboard handlers independently validate
   their inputs. Treat all clients and model-generated arguments as untrusted.
2. The process crosses a hardware/subprocess boundary to Airspy HF+ or RTL-SDR
   tools, WSJT-X programs, Fldigi/audio playback, SSTV, and ffmpeg. Executables
   and `PATH` are administrator-controlled trusted inputs. Arguments remain
   arrays and must not pass through a shell.
3. The process crosses a writable storage boundary at `RF_MCP_DATA_DIR`.
   Database rows and artifact paths can contain sensitive station and received
   data. The service account and filesystem permissions are the authorization
   boundary.
4. Webhook delivery and satellite/space-weather refresh features cross an
   outbound network boundary. Destinations and downloaded data are untrusted;
   outbound firewalling and destination allowlisting belong to the deployment.
5. Python and system packages cross a supply-chain boundary. The reviewed lock,
   clean wheel, external decoder packages, drivers, and OS are all trusted code.

The packaged fake receiver is safe for deterministic verification only when
explicitly registered in that process. It avoids hardware access but still
exercises DSP, catalog writes, artifacts, HTTP, and MCP.

## Network deployment and authentication

HTTP defaults to `127.0.0.1:8765`. `/health` and `/healthz` are intentionally
public and disclose status, service name, version, and whether authentication is
required. If `RF_MCP_API_TOKEN` is unset, every other route is also public. Set a
random token of at least 32 allowed characters before network exposure. Bearer
comparison is constant-time. Dashboard login creates a process-local 12-hour
HttpOnly, SameSite=Strict session; restarting invalidates sessions.

The same token grants the complete MCP tool set, dashboard controls, API calls,
live streams, and downloads. It provides neither per-user identity nor
per-receiver/tool scopes. The application has no TLS. Keep loopback for a local
host; otherwise deploy behind a trusted TLS reverse proxy and firewall, restrict
source networks, impose request/body/connection/rate limits, redact credentials,
and do not trust forwarded identity headers as authorization. The systemd helper
stores `RF_MCP_API_TOKEN` in root-owned mode-0600 `/etc/SDR-MCP.env`.

## Storage, retention, and deletion

The SQLite WAL catalog and all subdirectories of `RF_MCP_DATA_DIR` are
persistent. Captures and derived audio may contain intercepted communications;
plots, filenames, decoded text, station locations, TLE/pass plans, fingerprints,
and webhook records can also be sensitive. Apply local law and radio rules,
collect only authorized signals, use an encrypted volume where appropriate,
and grant the service user exclusive access. Protect database, WAL, backups,
crash dumps, swap, browser storage, host transcripts, and proxy/system logs.

Artifact/session cleanup and delete tools are intentionally destructive and may
cascade through related state. Require host-side approval for all mutating,
receiver-control, decoder, schedule, notification, and cleanup calls. Back up
the database and artifact tree as one unit and test restoration. Uninstalling
the package does not erase data.

Logs and diagnostics must redact `Authorization`, dashboard cookies,
`RF_MCP_API_TOKEN`, webhook secrets, request/response bodies, decoded payloads,
precise locations, device serials, and sensitive paths. Capability and decoder
output can reveal installed software and received content.

## Subprocess and receiver controls

Install receiver and decoder executables from trusted sources at root-controlled
paths; do not let the service account modify executables, its virtual
environment, or `PATH`. Device selectors and decoder settings are validated,
but external tools and drivers remain native attack surface. Use the supplied
systemd hardening as a baseline, a dedicated unprivileged account, narrow USB
permissions, `NoNewPrivileges`, filesystem protection, resource limits, and
outbound filtering. Keep the writable exception limited to `RF_MCP_DATA_DIR`.

Long captures, scans, streams, decoder work, queued jobs, schedules, and artifact
growth can exhaust CPU, memory, device time, and disk despite application
bounds. Monitor `get_storage_status`, recovery/admission/job state, free space,
process resources, and subprocess timeouts. Configure retention and pin only
necessary evidence. A result is not calibrated dBm unless the referenced
receiver calibration has a documented reference source. Decoder/classifier
output is fallible and must not trigger safety-critical action without review.

## Release gate and residual risk

A release requires the complete supported Python/OS test matrix; deterministic
installed-wheel HTTP/MCP/fake-receiver acceptance; formatting, lint, typing,
locked dependency validation and vulnerability audit; secret scan; threat-model
review; clean build metadata; wheel-content validation (including RF modules and
dashboard assets); checksums, SBOM, provenance attestation; and owner approval.
External receiver/decoder versions and service configuration must be recorded in
production because they are not pinned by the Python wheel.

Residual risks include a stolen all-powerful token, plaintext traffic without a
proxy, malicious/compromised native tools or drivers, unauthorized reception,
RF-generated hostile decoder inputs, webhook data exfiltration/SSRF-like reach,
resource exhaustion, SQLite/filesystem corruption, local races, false RF
classification, and retention outside the server in MCP hosts and browsers.
Version 1.0.0 is unmaintained, so passing the historical release gate does not
imply current vulnerability support.

The legacy `aislop` workspace observer has a different root-confinement threat
model and does not represent the RF application's security behavior.
