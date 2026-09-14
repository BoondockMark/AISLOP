# AISLOP

**Automated Inspection, Scanning, Listening & Observation Platform**

> Artificially Intelligent Software, Lovingly Orphaned Promptly.

AISLOP is a snarking app built with confidence, autocomplete, and absolutely no
dangerous burden of human comprehension. It is proof that software can look
finished long before anybody understands what it does.

## Full disclosure

I do **not** understand this code. I did **not** write a single line of it.
Every function in AISLOP was produced by ChatGPT's Codex; my role was to ask for
things, accept the results, and maintain an unwavering belief that green checks
are a substitute for knowledge.

I also have **no plans to maintain AISLOP after its initial release**. In policy
terms, that means version 1.0.0 is the only planned release and receives no bug,
compatibility, or security fixes. See the [maintenance and release policy](MAINTENANCE.md)
for the deliberately short lifecycle.

Use this project at your own risk. If it works, Codex deserves the credit. If it
breaks, the repository has achieved its intended state.

## What is MCP?

[Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is an open
protocol that lets an AI application connect to external tools and data through
a standard client/server interface. In less responsible terms: it is a USB-C
port for language models, except every device plugged into it can read your
files and has opinions.

AISLOP is intended to run as an **MCP server**. An MCP-compatible host—such as a
desktop AI application, editor, or agent—acts as the client. The host starts or
contacts AISLOP, discovers the tools AISLOP advertises, and allows the model to
invoke those tools on the user's behalf. This is much more convenient than
giving an unpredictable machine a shell directly, while preserving much of the
same excitement.

## Project status and supported systems

AISLOP 1.0.0 is the sole planned release of the `aislop-sdr`
distribution. The packaged product is **Multi-SDR RF Lab**, started with
`rf-mcp`; it is a receive-only radio application with an MCP RF API and a web
dashboard. Version 1.0.0 receives no maintenance or security fixes. See
[MAINTENANCE.md](MAINTENANCE.md) before deploying it.

The release is tested with **CPython 3.12 and 3.13** on 64-bit Windows, macOS,
and glibc-based Linux. The documented production service is systemd on
64-bit, glibc-based Linux (kernel 5.15 or newer). Windows 11 and macOS 13 or
newer can run the Python application, dashboard, MCP service, and fake receiver,
but the supplied service installer and Linux decoder/audio integration do not
apply there. PyPy, Python outside 3.12–3.13, 32-bit systems, WSL, BSD, mobile,
and musl-based Linux are unsupported.

The old `aislop` executable is still included only for compatibility. It is a
separate bounded workspace observer, has a different CLI and security model,
and is not the radio application. Its frozen reference is in
[the legacy specification](docs/specification.md#legacy-workspace-observer).
Do not put `aislop --allow-root ...`, port 8000, or `AISLOP_AUTH_TOKEN` in an
`rf-mcp` configuration.

## Install the packaged radio application

### Requirements

Install as an unprivileged user in a dedicated virtual environment. The core
package can start and can run the deterministic fake receiver without radio
hardware. Real reception requires one of these supported command-line hardware
stacks on `PATH`, plus the device's OS driver/USB permissions and an antenna:

- **Airspy HF+**: `airspyhf_info` and `airspyhf_rx` from the Airspy HF+ tools.
  The implemented ranges are 9 kHz–31 MHz and 60–260 MHz at 768 ksample/s.
- **RTL-SDR**: `rtl_test` and `rtl_sdr` from `rtl-sdr`. The implemented range is
  24 MHz–1.766 GHz, with sample rates from 225,001 to 3,200,000 sample/s.

Decoder integrations are optional capabilities, not Python-package
requirements. `ffmpeg` supplies live browser audio; the WSJT-X command-line
decoders (`jt9`, `jt4`, `wsprd`), Fldigi plus its XML-RPC/audio-loopback setup,
and the `sstv` WAV decoder are invoked as subprocesses when their corresponding
features are used. The scripts in `scripts/` install/configure these Linux
integrations. Check availability with the MCP tools
`list_digital_decoder_capabilities`, `get_fldigi_status`, and
`list_sstv_decoder_capabilities`; absence must be treated as an unavailable
capability, not a successful decode.

### Package install

The `aislop-sdr` project is not currently active on PyPI: its trusted-publisher
registration is pending. Consequently, `pip install aislop-sdr==1.0.0` will not
work until the repository owner completes the first trusted publication. Do not
install a similarly named, unverified distribution or remove the version pin.

Until PyPI publication succeeds, install from a reviewed repository checkout:

```sh
git clone https://github.com/BoondockMark/AISLOP.git
cd AISLOP
python3 -m venv .venv
. .venv/bin/activate                    # Windows: .venv\Scripts\activate
python -m pip install .
rf-mcp --version
```

For a reproducible installation, check out the reviewed commit (or the
`v1.0.0` tag once it exists) before running `pip install .`; the default branch
can change. The expected output is `rf-mcp 1.0.0`.

After a tagged release completes, the same wheel and source archive are attached
to the [GitHub v1.0.0 release](https://github.com/BoondockMark/AISLOP/releases/tag/v1.0.0),
so they remain an installation source even if PyPI publishing fails. Download
the wheel for offline inspection, verify it against `SHA256SUMS` from that
release, and install its local path with `python -m pip install
./aislop_sdr-1.0.0-py3-none-any.whl`.

Once the [PyPI project](https://pypi.org/project/aislop-sdr/) is active, the
short installation command is `python -m pip install aislop-sdr==1.0.0`.
Source development instead uses `uv sync --all-groups`. On systemd Linux,
`scripts/install-service.sh` creates `.venv`, installs the checkout, and enables
`SDR-MCP.service`; review the script and set authentication before exposing that
service.

### Data and artifacts

`RF_MCP_DATA_DIR` selects the writable data root and defaults to
`~/SDR-MCP-data`. At startup and during operations the application creates an
SQLite catalog named `SDR-MCP.sqlite3` (with SQLite WAL files as needed) and
subdirectories including `captures/`, `plots/`, `results/`, `audio/`,
`fm-surveys/`, `weak-signal/`, `fldigi/`, `sstv/`, and `satellite/`. Jobs,
receiver configuration, schedules, observations, station memories, and artifact
metadata persist in the catalog; IQ, JSON, plots, WAV files, exports, and SSTV
images persist as files. Back up the database and the complete data root
together. Uninstalling the wheel does **not** remove this data.

## Run and connect

`rf-mcp` accepts only `--help` and `--version`; runtime configuration is through
environment variables. Its default is Streamable HTTP on
`127.0.0.1:8765`, with the MCP endpoint at `/mcp`, readiness at `/health` and
`/healthz`, and the dashboard at `http://127.0.0.1:8765/dashboard` (also `/`).
The principal settings are:

| Variable | Default | Meaning |
| --- | --- | --- |
| `RF_MCP_TRANSPORT` | `streamable-http` | `streamable-http` for dashboard/API/MCP, or `stdio` for MCP only. |
| `RF_MCP_HOST` | `127.0.0.1` | HTTP bind address. Use `0.0.0.0` only behind appropriate network controls. |
| `RF_MCP_PORT` | `8765` | HTTP listen port. |
| `RF_MCP_DATA_DIR` | `~/SDR-MCP-data` | Persistent catalog and artifact root. |
| `RF_MCP_API_TOKEN` | unset | Optional HTTP bearer token; at least 32 characters from letters, digits, `. _ ~ -`. |

Start locally:

```sh
RF_MCP_DATA_DIR="$HOME/SDR-MCP-data" rf-mcp
```

Keep that process running while using the dashboard. A successful HTTP startup
prints a Uvicorn message containing `http://127.0.0.1:8765`; verify the public
readiness route before opening the browser:

```sh
curl --fail http://127.0.0.1:8765/healthz
```

If the browser reports that the site cannot be reached, this is a listener or
network-location problem, not a missing API token. Check the following:

1. Include the configured port in the browser URL. For a machine whose hostname
   is `minirackdisplay`, the default dashboard URL is
   **`http://minirackdisplay:8765/dashboard`**, not
   `http://minirackdisplay`. The latter uses port 80, but RF MCP listens on port
   8765 by default. Test the same hostname and port that the browser uses with
   `curl --verbose http://minirackdisplay:8765/healthz`.
2. Start `rf-mcp`, not the legacy `aislop` command, from the activated virtual
   environment. `rf-mcp --version` should work in the same shell.
3. Leave `RF_MCP_TRANSPORT` unset or set it to `streamable-http`. The `stdio`
   transport is for a host-managed MCP subprocess and does not start a web
   server or dashboard.
4. Read the server's terminal output. A startup exception means there is no
   listener; on Linux/macOS, `curl --verbose http://127.0.0.1:8765/healthz` and
   `ss -ltnp 'sport = :8765'` distinguish that case from a browser problem. A
   listener shown as `127.0.0.1:8765` accepts only same-machine connections;
   it cannot accept a connection addressed to the machine from another
   computer. Stop that process and restart it with a LAN bind:

   ```sh
   RF_MCP_HOST=0.0.0.0 RF_MCP_DATA_DIR="$HOME/SDR-MCP-data" rf-mcp
   ss -ltnp 'sport = :8765' # should now show 0.0.0.0:8765
   ```

   The packaged systemd unit already sets `RF_MCP_HOST=0.0.0.0`; if it still
   binds to loopback, inspect `/etc/SDR-MCP.env` for an overriding
   `RF_MCP_HOST=127.0.0.1`, then restart and verify the service:

   ```sh
   sudo systemctl restart SDR-MCP.service
   sudo systemctl --no-pager --full status SDR-MCP.service
   ss -ltnp 'sport = :8765'
   ```

   Also check that another process is not already using port 8765. A LAN bind
   exposes the unauthenticated dashboard unless `RF_MCP_API_TOKEN` is set, so
   limit access with the host firewall or configure authentication before
   allowing untrusted clients.
5. Interpret `127.0.0.1` as the machine where the browser runs. If `rf-mcp`
   runs in a container, VM, WSL instance, SSH host, or another computer, its
   loopback address is not the browser machine's loopback address. Publish or
   forward port 8765, and set `RF_MCP_HOST=0.0.0.0` only with an API token and
   appropriate firewall/TLS controls. For SSH, a local tunnel such as
   `ssh -L 8765:127.0.0.1:8765 user@server` avoids exposing the listener.
6. From the browser machine, check `getent hosts minirackdisplay` (or
   `nslookup minirackdisplay`) and compare it with the server's addresses from
   `hostname -I`. If the hostname resolves to the wrong address, fix local DNS
   or `/etc/hosts`. If name resolution is correct but the remote curl fails,
   allow TCP port 8765 through the host firewall and any container/VM port
   publishing layer.

Changing the configured port changes both checks and the dashboard URL. For
example, with `RF_MCP_PORT=9000`, use `http://127.0.0.1:9000/dashboard`.

Without `RF_MCP_API_TOKEN`, every HTTP route is unauthenticated. If a token is
set, `/health` and `/healthz` remain public, while `/mcp`, dashboard assets,
JSON APIs, live streams, and artifact downloads require it. The dashboard
accepts a bearer header or its login form/session cookie. MCP clients must send
`Authorization: Bearer <token>`. The service does not terminate TLS and bearer
authentication is not multi-user authorization; use a TLS reverse proxy,
firewall, and a dedicated service account before binding beyond loopback.
`scripts/configure-auth.sh` writes a generated or supplied token to root-only
`/etc/SDR-MCP.env` for the systemd service.

A conventional remote MCP host entry is:

```json
{
  "mcpServers": {
    "rf-lab": {
      "type": "streamable-http",
      "url": "http://127.0.0.1:8765/mcp",
      "headers": {
        "Authorization": "Bearer replace-with-at-least-32-safe-characters"
      }
    }
  }
}
```

For a host that launches local stdio servers, configure the RF executable—not
the legacy observer—and do not set an HTTP token:

```json
{
  "mcpServers": {
    "rf-lab": {
      "command": "/absolute/path/to/.venv/bin/rf-mcp",
      "args": [],
      "env": {
        "RF_MCP_TRANSPORT": "stdio",
        "RF_MCP_DATA_DIR": "/absolute/writable/path/SDR-MCP-data"
      }
    }
  }
}
```

GUI hosts may not inherit the shell's `PATH`; use the absolute executable path
and ensure receiver/decoder subprocesses are also discoverable. Restart the
host after editing its configuration.

For product-specific setup, authentication guidance, first prompts, an Ollama
tool-loop example, and troubleshooting, see [Connect AISLOP to ChatGPT and
Ollama](docs/mcp-clients.md).

## Deterministic post-install verification (no SDR required)

The fake receiver is a packaged test/demo backend, not an RF simulator selected
by a production environment flag. The following verification registers it as
the default `airspyhf` backend only in the verification process. It creates a
deterministic 12 kHz IQ tone, exercises the real HTTP, MCP, DSP, catalog, and
artifact paths, and never probes radio hardware.

Run this sequence from an activated environment containing the installed wheel:

```sh
set -eu
rf-mcp --version | tee /tmp/rf-mcp-version.txt
test "$(cat /tmp/rf-mcp-version.txt)" = "rf-mcp 1.0.0"

export RF_MCP_DATA_DIR="$(mktemp -d)"
export RF_MCP_TRANSPORT=streamable-http
export RF_MCP_HOST=127.0.0.1
export RF_MCP_PORT=18765
export RF_MCP_API_TOKEN=verification-token-0123456789abcdef

python -c "from rf_mcp.fake_receiver import FakeStreamingReceiverBackend; from rf_mcp.receiver_backend import register_backend; register_backend(FakeStreamingReceiverBackend(name='airspyhf')); from rf_mcp.server import main; main()" >/tmp/rf-mcp.log 2>&1 &
RF_MCP_PID=$!
trap 'kill "$RF_MCP_PID" 2>/dev/null || true' EXIT

until curl --fail --silent http://127.0.0.1:18765/healthz > /tmp/rf-health.json; do
  kill -0 "$RF_MCP_PID"
  sleep 0.1
done
python -c 'import json; d=json.load(open("/tmp/rf-health.json")); assert d["status"]=="ok" and d["service"]=="SDR-MCP" and d["version"]=="1.0.0" and d["authentication_required"] is True'

curl --fail --silent \
  -H "Authorization: Bearer $RF_MCP_API_TOKEN" \
  http://127.0.0.1:18765/assets/rf-dashboard.js \
  | grep -q refreshDashboard

python - <<'PY'
import asyncio, os
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def verify():
    headers = {"Authorization": f"Bearer {os.environ['RF_MCP_API_TOKEN']}"}
    async with streamablehttp_client("http://127.0.0.1:18765/mcp", headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = {tool.name for tool in (await session.list_tools()).tools}
            required = {"get_rf_api_contract", "list_devices", "inspect_spectrum", "list_rf_jobs", "list_rf_artifacts"}
            assert required <= tools, required - tools
            device = (await session.call_tool("list_devices", {})).structuredContent
            assert device["model"] == "deterministic-test-tone" and device["hardware"] is False
            observation = (await session.call_tool("inspect_spectrum", {
                "center_frequency_hz": 100000000,
                "duration_seconds": 0.25,
                "fft_size": 1024,
                "threshold_above_noise_db": 6,
                "include_plot": False
            })).structuredContent
            assert observation["receiver_backend"] == "airspyhf"
            assert observation["sample_rate_hz"] == 768000
            assert observation["captured_samples"] >= 192000
            assert observation["job_id"].startswith("inspect-")
            print(observation["job_id"])

asyncio.run(verify())
PY

test -f "$RF_MCP_DATA_DIR/SDR-MCP.sqlite3"
find "$RF_MCP_DATA_DIR" -type f -print
```

A successful run verifies the executable version, readiness document,
authenticated dashboard JavaScript delivery, MCP initialization and tool
discovery, a hardware-free observation, and persistent catalog/artifacts.

## Use the RF application

The stable RF API contract is returned by `get_rf_api_contract`. Frequencies are
integer Hz and times are UTC ISO 8601. Measurements are relative digital-domain
levels unless a saved receiver calibration with a documented reference source
supports a calibrated claim. The stable v1 core covers health/readiness,
receiver discovery and coordination, spectrum inspection and analysis,
broadcast FM, calibration, and persistent job/artifact/storage/recovery queries.
The server also advertises specialized tools for scanning, monitoring,
scheduling, alerts/webhooks, recordings, digital modes, SSTV, propagation,
satellites, classification, and signal fingerprints. Discover the installed
tool schemas rather than copying arguments from an older release.

Start with `list_devices` (or discovery/coordinator tools for multiple radios),
then call `inspect_spectrum` or `analyze_signal`. RF operations may create
persistent jobs and artifacts even when a response embeds a preview. Use
`list_rf_jobs`, `get_rf_job`, `list_rf_artifacts`, `get_rf_artifact`, and the
dashboard to inspect them; use the explicit cleanup tools and confirmation
parameters for destructive operations. Receiver control and decoder execution
are active local side effects even though the platform is receive-only.
Complete API, persistence, decoder, and security semantics are in
[docs/specification.md](docs/specification.md) and
[docs/security.md](docs/security.md).

## Best practices in AI SLOP coding

AISLOP aspires to the following standards of machine-assisted craftsmanship:

### 1. Superficial competence

The code should look clean, pass the obvious unit tests, and satisfy the demo.
Architectural consequences are deferred to a future maintainer who, as noted
above, does not exist. This produces the ideal combination of professional
presentation and load-bearing mystery.

Further reading: [What Is AI Slop in Code?](https://dev.to/heavykenny/what-is-ai-slop-in-code-235a)
and [What Is AI Slop? Detect and Prevent Low-Quality AI Code](https://larridin.com/developer-productivity-hub/what-is-ai-slop-detect-prevent-low-quality-ai-code).

### 2. Complexity inflation and over-abstraction

No operation is so simple that it cannot benefit from a wrapper, a manager, a
factory, and an `AbstractThingStrategyProvider`. Extra layers ensure that a
three-line behavior requires twelve files and the quiet acceptance of several
design patterns.

Further reading: [AI Slop in Code](https://www.managed-code.com/blog-post/ai-slop-in-code)
and [What Is AI Slop?](https://larridin.com/developer-productivity-hub/what-is-ai-slop-detect-prevent-low-quality-ai-code).

### 3. Pattern drift and duplication

Why reuse an existing abstraction when we can generate a nearly identical one
with a slightly different name? Duplicate utilities preserve each prompt's
unique artistic vision while turning bug fixes into a repository-wide scavenger
hunt.

Further reading: [What Is AI Slop?](https://larridin.com/developer-productivity-hub/what-is-ai-slop-detect-prevent-low-quality-ai-code)
and [AI Slop in Code](https://www.managed-code.com/blog-post/ai-slop-in-code).

### 4. Hollow testing

Tests should confirm that the implementation is implemented exactly as
implemented. Edge cases, user behavior, and inconvenient reality would only
make the suite less green. A mock of a mock is still confidence if the badge
says “passing.”

Further reading: [What Is AI Slop?](https://larridin.com/developer-productivity-hub/what-is-ai-slop-detect-prevent-low-quality-ai-code).

### 5. Ceremonial and redundant comments

Every self-evident line deserves a comment restating it in English. Comments
explaining *why* a decision was made are discouraged because that would require
someone to know why the decision was made.

Further reading: [AI Slop in Code](https://www.managed-code.com/blog-post/ai-slop-in-code).

### 6. Ghost references and unused imports

Unused imports are not clutter; they are aspirations. References to objects
that do not exist provide a flexible roadmap for features nobody requested.
Redundant declarations, meanwhile, give the code a reassuring sense of volume.

Further reading: [A discussion of AI slop and vibe coding](https://www.reddit.com/r/vibecoding/comments/1ny8v7q/anyone_care_to_explain_ai_slop/)
and [AI Slop: The Future of Software Engineering](https://davidkcaudill.medium.com/ai-slop-the-future-of-software-engineering-0eb0d2570a7a).

## Support

There is none.

Outside contributions are not accepted, so the project does not maintain
contribution or community conduct policies. Issues and pull requests may be
closed without review. For troubleshooting, paste the error into the next
available language model and continue the proud AISLOP tradition. Security
reports are handled as described in the [security policy](SECURITY.md).

## License

AISLOP is available under the [MIT License](LICENSE). Dependency and bundling
information is recorded in [third-party notices](THIRD_PARTY_NOTICES.md).
