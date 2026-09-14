#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="${PYTHON_BIN:-python3}"
service_user="${SUDO_USER:-${USER:-$(id -un)}}"
service_home="$(getent passwd "$service_user" | cut -d: -f6)"
venv_dir="$project_dir/.venv"
unit_dir="${SYSTEMD_UNIT_DIR:-/etc/systemd/system}"

if ! command -v "$python_bin" >/dev/null 2>&1; then
  echo "Python interpreter not found: $python_bin" >&2
  exit 1
fi

validate_python() {
  "$1" -c '
import sys
if not ((3, 12) <= sys.version_info[:2] < (3, 14)):
    raise SystemExit(
        f"Python 3.12 or 3.13 is required; found {sys.version_info.major}.{sys.version_info.minor}"
    )
'
}

if ! validate_python "$python_bin"; then
  echo "The RF MCP service requires a supported Python version (3.12 or 3.13)." >&2
  exit 1
fi

if [[ -z "$service_home" || "$service_home" == "/" ]]; then
  echo "Unable to resolve a safe home directory for $service_user" >&2
  exit 1
fi

if [[ "$project_dir" == *$'\n'* || "$project_dir" == *'"'* || "$project_dir" == *'%'* ]]; then
  echo "The project path contains characters that cannot be safely written to the systemd unit." >&2
  exit 1
fi

if [[ ! -x "$venv_dir/bin/python" ]]; then
  "$python_bin" -m venv "$venv_dir"
fi

if ! validate_python "$venv_dir/bin/python"; then
  echo "The existing virtual environment does not use Python 3.12 or 3.13: $venv_dir" >&2
  exit 1
fi

"$venv_dir/bin/python" -m pip install "$project_dir"
console_executable="$venv_dir/bin/rf-mcp"
if [[ ! -x "$console_executable" ]]; then
  echo "Package installation did not create the expected executable: $console_executable" >&2
  exit 1
fi

mkdir -p \
  "$service_home/SDR-MCP-data/captures" \
  "$service_home/SDR-MCP-data/plots" \
  "$service_home/SDR-MCP-data/results" \
  "$service_home/SDR-MCP-data/audio" \
  "$service_home/SDR-MCP-data/fm-surveys" \
  "$service_home/SDR-MCP-data/weak-signal"
mkdir -p "$service_home/SDR-MCP-data/fldigi" "$service_home/SDR-MCP-data/fldigi-config"
mkdir -p "$service_home/SDR-MCP-data/sstv"
mkdir -p "$service_home/SDR-MCP-data/matplotlib-cache"
service_tmp="$(mktemp)"
trap 'rm -f "$service_tmp"' EXIT

# Escape sed replacement metacharacters. Paths containing spaces are supported
# because the corresponding systemd values are quoted in the template.
sed_escape() {
  printf '%s' "$1" | sed -e 's/[\\&|]/\\&/g'
}
service_user_escaped="$(sed_escape "$service_user")"
service_home_escaped="$(sed_escape "$service_home")"
project_dir_escaped="$(sed_escape "$project_dir")"
sed \
  -e "s|__RF_MCP_USER__|$service_user_escaped|g" \
  -e "s|__RF_MCP_HOME__|$service_home_escaped|g" \
  -e "s|__RF_MCP_PROJECT_DIR__|$project_dir_escaped|g" \
  "$project_dir/systemd/SDR-MCP.service" > "$service_tmp"

sudo install -m 0644 "$service_tmp" "$unit_dir/SDR-MCP.service"
sudo systemctl daemon-reload
sudo systemctl enable --now SDR-MCP.service
sudo systemctl --no-pager --full status SDR-MCP.service

public_host="$(hostname -f 2>/dev/null || hostname)"
cat <<EOF

RF MCP is listening on TCP port 8765.
Open the dashboard at: http://${public_host}:8765/dashboard

The :8765 port is required. Opening http://${public_host} without it connects
to the default HTTP port (80), where this service is not listening.
Verify remote access with: curl --fail http://${public_host}:8765/healthz
EOF
