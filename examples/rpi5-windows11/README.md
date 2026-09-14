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
unprivileged login (the examples below use `rf`). AISLOP requires CPython 3.12
or 3.13, so check the interpreter before installing:

```sh
uname -m                         # expected: aarch64
python3 --version                # must be 3.12.x or 3.13.x
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

Install 64-bit Python 3.12 or 3.13 and Ollama on Windows, then choose an Ollama
model that supports tool calling and fits the available 16 GB VRAM. Hardware
capacity does not guarantee that every model or context size will fit.

In PowerShell, copy this example directory to the Windows PC and run:

```powershell
cd C:\path\to\AISLOP\examples\rpi5-windows11
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
ollama pull <tool-capable-model>

$env:RF_MCP_URL = "http://192.168.1.20:8765/mcp"
$env:RF_MCP_API_TOKEN = Read-Host "AISLOP bearer token"
$env:OLLAMA_MODEL = "<tool-capable-model>"
python .\ollama_remote_client.py
```

Use `py -3.12` instead if that is the supported interpreter installed on the
PC. Environment variables above last only for that PowerShell process and keep
the token out of the command history. Do not put the token in a URL.

The client discovers tool definitions from the Pi, passes them to the local
Ollama model, and relays requested tool calls back to the Pi. Start with a
non-mutating prompt:

```text
Show the RF API contract and available receiver backends. Do not tune, record,
schedule, or create artifacts.
```

The confirmation language is guidance to the model, not a security boundary.
The bearer token grants access to every RF tool. Supervise the example and add
an application-enforced allowlist/approval UI before unattended use.

## 3. Verify the two-machine path

From Windows PowerShell, test the exact Pi address used by the MCP client:

```powershell
Test-NetConnection 192.168.1.20 -Port 8765
Invoke-RestMethod http://192.168.1.20:8765/healthz
```

`/healthz` is intentionally public and only proves reachability/readiness. A
successful tool listing additionally proves authentication and MCP transport.
The example prints the discovered tool count after it connects.

| Symptom | Action |
| --- | --- |
| TCP test fails | Check the Pi address, `systemctl status`, `ss`, VLAN/client isolation, and both host firewalls. |
| HTTP `401 Unauthorized` | Re-enter the exact token printed by `configure-auth.sh`; do not include `Bearer ` in the environment variable. |
| Health works but MCP fails | Confirm `RF_MCP_URL` ends in `/mcp` and that the service uses `streamable-http`. |
| No receiver appears | Diagnose drivers, USB permissions, utilities, and the SDR on the Pi—not on Windows. |
| Model never calls a tool | Select an Ollama model with tool-calling support and keep Ollama running locally. |

