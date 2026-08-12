#!/usr/bin/env bash
# Ensure Docker Engine + Compose plugin are available (local or Cursor cloud).
# Idempotent. Does not start application containers.
set -euo pipefail

log() { printf '%s\n' "$*"; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1
}

install_docker_packages() {
  if need_cmd docker && docker compose version >/dev/null 2>&1; then
    return 0
  fi

  if ! need_cmd apt-get; then
    echo "Docker is missing and apt-get is unavailable. Install Docker Engine + Compose manually." >&2
    exit 1
  fi

  log "Installing Docker Engine and Compose plugin..."
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq docker.io docker-compose-v2
}

ensure_docker_group() {
  if ! getent group docker >/dev/null 2>&1; then
    return 0
  fi
  if id -nG "${USER:-$(id -un)}" 2>/dev/null | tr ' ' '\n' | grep -qx docker; then
    return 0
  fi
  # Best-effort; a new login may still be required for non-sudo docker.
  sudo usermod -aG docker "${USER:-$(id -un)}" 2>/dev/null || true
}

docker_info_ok() {
  if docker info >/dev/null 2>&1; then
    return 0
  fi
  if need_cmd sudo && sudo docker info >/dev/null 2>&1; then
    return 0
  fi
  return 1
}

start_dockerd() {
  if docker_info_ok; then
    return 0
  fi

  log "Starting Docker daemon..."
  if need_cmd systemctl && systemctl is-system-running >/dev/null 2>&1; then
    sudo systemctl start docker || true
  fi

  if ! docker_info_ok; then
    # Cursor cloud / container hosts often lack a working systemd for dockerd.
    if ! pgrep -x dockerd >/dev/null 2>&1; then
      sudo dockerd >/tmp/dockerd.log 2>&1 &
    fi
  fi

  local attempt
  for attempt in $(seq 1 60); do
    if docker_info_ok; then
      return 0
    fi
    sleep 1
  done

  echo "Docker daemon did not become ready. See /tmp/dockerd.log if present." >&2
  tail -n 40 /tmp/dockerd.log 2>/dev/null || true
  exit 1
}

docker_cli() {
  if docker info >/dev/null 2>&1; then
    docker "$@"
  else
    sudo docker "$@"
  fi
}

ensure_socket_access() {
  # Disposable cloud/dev VMs: allow the current user to talk to the daemon without
  # a new login shell (usermod group membership does not apply to this session).
  if docker info >/dev/null 2>&1; then
    return 0
  fi
  if [[ -S /var/run/docker.sock ]]; then
    sudo chmod 666 /var/run/docker.sock 2>/dev/null || true
  fi
}

configure_storage_for_nested_hosts() {
  # Cursor cloud VMs often run on overlayfs; nested overlay Docker fails with
  # "operation not permitted" / "invalid argument". Prefer vfs in that case.
  local daemon_json="/etc/docker/daemon.json"
  local root_fs
  root_fs="$(findmnt -no FSTYPE / 2>/dev/null || true)"
  if [[ "$root_fs" != "overlay" && "$root_fs" != "overlay2" ]]; then
    return 0
  fi
  if [[ -f "$daemon_json" ]] && grep -q '"storage-driver"[[:space:]]*:[[:space:]]*"vfs"' "$daemon_json"; then
    return 0
  fi
  log "Detected overlay root filesystem; configuring Docker storage-driver=vfs for nested containers..."
  sudo mkdir -p /etc/docker
  if [[ -f "$daemon_json" ]]; then
    sudo cp "$daemon_json" "${daemon_json}.bak.$(date +%s)" || true
  fi
  sudo tee "$daemon_json" >/dev/null <<'EOF'
{
  "storage-driver": "vfs"
}
EOF
  # Restart daemon so the driver takes effect (safe on disposable cloud VMs).
  if pgrep -x dockerd >/dev/null 2>&1; then
    sudo pkill dockerd || true
    sleep 2
  fi
}

install_docker_packages
ensure_docker_group
configure_storage_for_nested_hosts
start_dockerd
ensure_socket_access

# Export helper for callers that source this file.
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
  :
else
  docker_cli version >/dev/null
  docker_cli compose version
  log "Docker is ready."
fi
