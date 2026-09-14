#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
service_user="${SUDO_USER:-${USER:-$(id -un)}}"
service_home="$(getent passwd "$service_user" | cut -d: -f6)"
unit_dir="${SYSTEMD_UNIT_DIR:-/etc/systemd/system}"
environment_file="${SDR_MCP_ENV_FILE:-/etc/SDR-MCP.env}"
keep_data=false

usage() {
  cat <<'EOF'
Usage: scripts/uninstall-service.sh [--keep-data]

Stops and removes SDR-MCP.service, its environment file, and the checkout's
virtual environment. By default it also removes ~/SDR-MCP-data, including all
captures and the SQLite catalog. Use --keep-data to retain that directory.
EOF
}

case "${1:-}" in
  "") ;;
  --keep-data) keep_data=true ;;
  -h|--help) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac

if [[ -z "$service_home" || "$service_home" == "/" ]]; then
  echo "Unable to resolve a safe home directory for $service_user" >&2
  exit 1
fi

# Do not fail when the service was only partially installed.
sudo systemctl disable --now SDR-MCP.service 2>/dev/null || true
sudo rm -f "$unit_dir/SDR-MCP.service" "$environment_file"
sudo systemctl daemon-reload
sudo systemctl reset-failed SDR-MCP.service 2>/dev/null || true

if [[ -f "$project_dir/.venv/pyvenv.cfg" ]]; then
  rm -rf -- "$project_dir/.venv"
fi

if [[ "$keep_data" == false ]]; then
  sudo rm -rf -- "$service_home/SDR-MCP-data"
fi

echo "SDR-MCP.service has been uninstalled."
if [[ "$keep_data" == true ]]; then
  echo "Preserved data in $service_home/SDR-MCP-data."
fi
