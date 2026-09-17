# Raspberry Pi 5 server and Windows 11 Ollama client

This example separates the RF workload from the model workload:

```text
SDR + Raspberry Pi 5 (8 GB)                 Windows 11 (64 GB RAM, 16 GB VRAM)
rf-mcp, receiver drivers, DSP, artifacts <-- LAN / Streamable HTTP --> MCP client + Ollama
                 :8765/mcp                  Authorization: Bearer ...
```

The Pi remains the only machine connected to the SDR. It tunes the receiver,
runs AISLOP's DSP and decoder subprocesses, and stores captures. The Windows
GPU is used by Ollama for the language model; MCP does not move SDR hardware or
DSP execution to Windows. Consequently, select capture sizes, concurrent jobs,
and decoders for the Pi's CPU and 8 GB memory rather than the client's 64 GB.

This is a trusted-LAN example. AISLOP does not provide TLS. Do not forward TCP
8765 from the router or expose it to the Internet. For an untrusted network,
keep AISLOP bound to loopback and use an SSH tunnel or a TLS reverse proxy as
described in the main documentation.

## 1. Prepare the Raspberry Pi server

Use a 64-bit, glibc-based Raspberry Pi OS installation and a dedicated,
unprivileged login (the examples below use `rf`). AISLOP requires CPython 3.12,
3.13, or 3.14, so check the interpreter before installing:

```sh
uname -m                         # expected: aarch64
python3 --version                # must be 3.12.x, 3.13.x, or 3.14.x
sudo apt update
sudo apt install -y git python3-venv openssl curl
```

Install the appropriate SDR utilities and USB permissions from the main
README, connect the SDR and antenna, then install AISLOP:

```sh
git clone https://github.com/BoondockMark/AISLOP.git
cd AISLOP
git checkout <reviewed-commit-or-v1.0.0-tag>
sudo -v
./scripts/install-service.sh
./scripts/configure-auth.sh
```

`configure-auth.sh` prints a random token once. Store it in a password manager;
the same value is needed on Windows. The generated service already selects
Streamable HTTP, port 8765, persistent storage under `~/SDR-MCP-data`, and a
`0.0.0.0` LAN bind.

Limit inbound access to the Windows client's static IP. For example, if the
Windows PC is `192.168.1.50` and `ufw` is the Pi's active firewall:

```sh
sudo ufw allow from 192.168.1.50 to any port 8765 proto tcp
sudo ufw status
sudo systemctl restart SDR-MCP.service
curl --fail http://127.0.0.1:8765/healthz
ss -ltnp 'sport = :8765'
hostname -I
```

Do not enable a second firewall manager solely for this example. Apply the
equivalent source-IP rule in the firewall already managing the Pi. Reserve the
Pi's address in DHCP (this guide uses `192.168.1.20`) or use working local DNS.

## 2. Prepare the Windows client

Install 64-bit Python 3.12, 3.13, or 3.14 and Ollama on Windows, then choose an
Ollama model that supports tool calling and fits the available 16 GB VRAM. Hardware
capacity does not guarantee that every model or context size will fit.

Copy this example directory to the Windows PC, open Command Prompt, and run:

```bat
cd /d C:\path\to\AISLOP\examples\rpi5-windows11
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
ollama pull <tool-capable-model>
```

### Configure a reusable `.env` file

The Python client loads the three required settings from a local `.env`. Create
it from the safe template:

```bat
copy .env.example .env
notepad .env
```

Set all three values in `.env`:

```dotenv
RF_MCP_URL=http://192.168.1.20:8765/mcp
RF_MCP_API_TOKEN=paste-the-token-printed-by-configure-auth-on-the-pi
OLLAMA_MODEL=the-exact-name-shown-by-ollama-list
```

`RF_MCP_URL` is the Pi's stable LAN address (or DNS name), including port 8765
and the `/mcp` suffix. `RF_MCP_API_TOKEN` is the token printed once by
`configure-auth.sh`; enter only its value, without quotes and without the
`Bearer ` prefix. `OLLAMA_MODEL` must exactly match a tool-capable model already
shown by `ollama list`. Values in this example must not contain inline comments.

The repository ignores `.env` files, but treat this file as a password: do not
commit, share, or copy it into logs. The template contains placeholders only.
Ensure the Ollama desktop app is running (or run `ollama serve` in a separate
window), then launch the client directly from Command Prompt:

```bat
rem This also confirms that the local Ollama service is reachable.
ollama list
.venv\Scripts\python.exe ollama_remote_client.py
```

Existing PowerShell workflows can continue to use `run-client.ps1`. The Python
client does not replace environment variables that are already set, so a
one-time Command Prompt session can override `.env` without editing the file:

```bat
set "RF_MCP_URL=http://192.168.1.20:8765/mcp"
set /p "RF_MCP_API_TOKEN=AISLOP bearer token: "
set "OLLAMA_MODEL=<tool-capable-model>"
.venv\Scripts\python.exe ollama_remote_client.py
```

Use `py -3.12` or `py -3.14` instead if that is the supported interpreter
installed on the PC. Directly assigned environment variables last only for
that Command Prompt process, and `set /p` keeps the token itself out of command
history (although it is visible while typed). Do not put the token in a URL.
Values loaded from `.env` apply only to the Python process; they do not modify
the Windows user or system environment.

The client discovers tool definitions from the Pi, but passes only a curated
20-tool starter set to the local Ollama model on each request. This reduces the
schema context consumed by the common discovery, spectrum, FM, digital, SSTV,
band-scan, job, artifact, and storage workflows. It also rejects a tool call
outside that allowlist if the model invents one. Edit `ESSENTIAL_TOOL_NAMES` in
`ollama_remote_client.py` when a different workflow needs more tools; the Pi
continues to advertise the complete API to other MCP clients.

This is a client-side reduction, not a server-side authorization boundary. The
bearer token still grants access to every RF tool to software that calls the Pi
directly. The selected tool schemas are sent with every Ollama chat request, so
keeping this set focused reduces repeated input-token use. Start with a
non-mutating prompt:

```text
Show the RF API contract and available receiver backends. Do not tune, record,
schedule, or create artifacts.
```

After the `you>` prompt appears, ask in ordinary language. The client lets the
model choose from these workflow groups:

| Workflow | Included tools |
| --- | --- |
| Discover and check | `get_rf_api_contract`, `get_server_health`, `list_devices`, `list_digital_decoder_capabilities`, `list_sstv_decoder_capabilities` |
| Inspect and decode | `inspect_spectrum`, `analyze_signal`, `receive_broadcast_fm`, `decode_digital_signal`, `decode_sstv`, `list_fm_stations` |
| Band scan | `start_band_scan`, `get_band_scan_status`, `get_band_scan_results`, `stop_band_scan` |
| Retrieve results | `list_rf_jobs`, `get_rf_job`, `list_rf_artifacts`, `get_rf_artifact`, `get_storage_status` |

For example, ask `Inspect the spectrum around 100.1 MHz for two seconds` or
`Start a band scan from 88 to 108 MHz, then report its status`. Review the
model's requested action before allowing receiver changes or recordings. Enter
another prompt after each answer; press `Ctrl+C` to exit. Generated captures
and results remain on the Pi under its configured `RF_MCP_DATA_DIR`, rather
than being copied automatically to the Windows client.

The confirmation language is guidance to the model, not a security boundary.
The bearer token grants access to every RF tool. Supervise the example and add
an application-enforced allowlist/approval UI before unattended use.

## 3. Verify the two-machine path

From Command Prompt, test the exact Pi address used by the MCP client:

```bat
curl.exe --fail http://192.168.1.20:8765/healthz
```

`/healthz` is intentionally public and only proves reachability/readiness. A
successful tool listing additionally proves authentication and MCP transport.
The example prints both the discovered server-tool count and the 20 tools it
exposes to Ollama after it connects.

| Symptom | Action |
| --- | --- |
| TCP test fails | Check the Pi address, `systemctl status`, `ss`, VLAN/client isolation, and both host firewalls. |
| HTTP `401 Unauthorized` | Re-enter the exact token printed by `configure-auth.sh`; do not include `Bearer ` in the environment variable. |
| Health works but MCP fails | Confirm `RF_MCP_URL` ends in `/mcp` and that the service uses `streamable-http`. |
| No receiver appears | Diagnose drivers, USB permissions, utilities, and the SDR on the Pi—not on Windows. |
| Model never calls a tool | Select an Ollama model with tool-calling support and keep Ollama running locally. |
