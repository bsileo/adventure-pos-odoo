#!/usr/bin/env bash
# Manage a developer-owned Adventure POS GCP VM for remote development.
# Usage: ./scripts/remote-dev.sh [init-ssh|create|start|stop|status|ip|url|open|ssh|cursor|up|init-db|bootstrap|fetch-branch]
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

sanitize_name() {
  tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9-' '-' | sed 's/^-*//; s/-*$//; s/--*/-/g'
}

default_user="${REMOTE_DEV_USER:-${USER:-$(whoami)}}"
sanitized_user="$(printf '%s' "$default_user" | sanitize_name)"
if [[ -z "$sanitized_user" ]]; then
  sanitized_user="dev"
fi
sanitized_user="${sanitized_user:0:40}"
sanitized_user="${sanitized_user%-}"

action="${1:-status}"
branch_name="${2:-}"
project="${REMOTE_DEV_GCP_PROJECT:-adventure-pos-sandbox}"
zone="${REMOTE_DEV_GCP_ZONE:-us-central1-a}"
instance_prefix="${REMOTE_DEV_INSTANCE_PREFIX:-adventurepos-dev}"
instance_name="${REMOTE_DEV_GCP_INSTANCE:-${instance_prefix}-${sanitized_user}}"
vm_user="${REMOTE_DEV_VM_USER:-deploy}"
repo_path="${REMOTE_DEV_REPO_PATH:-/srv/adventurepos/adventure-pos-odoo}"
repo_url="${REMOTE_DEV_REPO_URL:-git@github.com:bsileo/adventure-pos-odoo.git}"
repo_branch="${REMOTE_DEV_REPO_BRANCH:-develop}"
odoo_port="${REMOTE_DEV_ODOO_PORT:-8069}"
ssh_key="${REMOTE_DEV_SSH_KEY:-}"
service_account="${REMOTE_DEV_SERVICE_ACCOUNT:-adventurepos-remote-dev-vm@${project}.iam.gserviceaccount.com}"
access_scopes="${REMOTE_DEV_ACCESS_SCOPES:-cloud-platform}"

ensure_command() {
  local command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Missing required command: $command_name" >&2
    exit 1
  fi
}

ensure_gcloud() {
  ensure_command gcloud
}

get_ip() {
  ensure_gcloud
  gcloud compute instances describe "$instance_name" \
    --zone="$zone" \
    --project="$project" \
    --format='value(networkInterfaces[0].accessConfigs[0].natIP)'
}

instance_exists() {
  gcloud compute instances describe "$instance_name" \
    --zone="$zone" \
    --project="$project" \
    --format='value(name)' >/dev/null 2>&1
}

ensure_instance_exists() {
  if ! instance_exists; then
    echo "Remote dev VM '$instance_name' was not found in $project/$zone." >&2
    echo "Run './scripts/remote-dev.sh create' first, or set REMOTE_DEV_GCP_INSTANCE to an existing VM." >&2
    exit 1
  fi
}

resolve_ssh_public_key_path() {
  if [[ -n "${REMOTE_DEV_SSH_PUBLIC_KEY_PATH:-}" ]]; then
    echo "$REMOTE_DEV_SSH_PUBLIC_KEY_PATH"
    return
  fi

  local candidate
  for candidate in "${HOME}/.ssh/id_ed25519.pub" "${HOME}/.ssh/id_rsa.pub"; do
    if [[ -f "$candidate" ]]; then
      echo "$candidate"
      return
    fi
  done

  echo "No SSH public key found. Run './scripts/remote-dev.sh init-ssh', set REMOTE_DEV_SSH_PUBLIC_KEY_PATH, or create ~/.ssh/id_ed25519.pub." >&2
  exit 1
}

init_ssh_key() {
  ensure_command ssh-keygen

  local ssh_dir="${HOME}/.ssh"
  local private_key_path="${ssh_dir}/id_ed25519"
  local public_key_path="${ssh_dir}/id_ed25519.pub"

  if [[ -f "$public_key_path" ]]; then
    echo "SSH public key already exists: $public_key_path"
    return
  fi

  mkdir -p "$ssh_dir"
  ssh-keygen -t ed25519 -f "$private_key_path" -N ""
  echo "Created SSH key pair:"
  echo "  Private: $private_key_path"
  echo "  Public:  $public_key_path"
}

create_instance() {
  local machine_type="${REMOTE_DEV_MACHINE_TYPE:-e2-standard-2}"
  local boot_disk_size="${REMOTE_DEV_BOOT_DISK_SIZE:-50GB}"
  local image_family="${REMOTE_DEV_IMAGE_FAMILY:-ubuntu-2204-lts}"
  local image_project="${REMOTE_DEV_IMAGE_PROJECT:-ubuntu-os-cloud}"
  local network_tags="${REMOTE_DEV_NETWORK_TAGS:-adventurepos-remote-dev}"
  local firewall_rule="${REMOTE_DEV_FIREWALL_RULE:-adventurepos-remote-dev-odoo}"
  local odoo_source_ranges="${REMOTE_DEV_ODOO_SOURCE_RANGES:-0.0.0.0/0}"
  local pubkey_path pubkey temp_file

  ensure_gcloud
  if instance_exists; then
    echo "Remote dev VM '$instance_name' already exists."
  else
    pubkey_path="$(resolve_ssh_public_key_path)"
    pubkey="$(<"$pubkey_path")"
    if [[ -z "$pubkey" ]]; then
      echo "SSH public key file '$pubkey_path' is empty." >&2
      exit 1
    fi

    temp_file="$(mktemp)"
    trap 'rm -f "$temp_file"' RETURN
    printf '%s:%s\n' "$vm_user" "$pubkey" > "$temp_file"

    gcloud compute instances create "$instance_name" \
      --zone="$zone" \
      --project="$project" \
      --machine-type="$machine_type" \
      --boot-disk-size="$boot_disk_size" \
      --image-family="$image_family" \
      --image-project="$image_project" \
      --service-account="$service_account" \
      --scopes="$access_scopes" \
      --tags="$network_tags" \
      --metadata-from-file "ssh-keys=$temp_file"
  fi

  if gcloud compute firewall-rules describe "$firewall_rule" --project="$project" --format='value(name)' >/dev/null 2>&1; then
    echo "Firewall rule '$firewall_rule' already exists."
  else
    gcloud compute firewall-rules create "$firewall_rule" \
      --project="$project" \
      --direction=INGRESS \
      --allow="tcp:${odoo_port}" \
      --target-tags="$network_tags" \
      --source-ranges="$odoo_source_ranges" \
      --description="Allow Adventure POS remote dev Odoo access on port ${odoo_port}"
  fi

  echo
  echo "Next steps:"
  echo "  1. ./scripts/remote-dev.sh start"
  echo "  2. ./scripts/remote-dev.sh bootstrap"
  echo "  3. ./scripts/remote-dev.sh cursor"
}

ssh_args=()
if [[ -n "$ssh_key" ]]; then
  ssh_args+=(-i "$ssh_key")
fi
ssh_args+=(-o StrictHostKeyChecking=accept-new)

run_ssh() {
  ensure_command ssh
  local ip
  ip="$(get_ip)"
  if [[ -z "$ip" ]]; then
    echo "Instance '$instance_name' does not have a public IP yet." >&2
    exit 1
  fi
  ssh "${ssh_args[@]}" "${vm_user}@${ip}" "$@"
}

print_cursor_details() {
  local ip
  ip="$(get_ip)"
  cat <<EOF
Cursor Remote SSH target:
  Host: ${instance_name}
  HostName: ${ip}
  User: ${vm_user}

Open this exact folder in Cursor after connecting:
  ${repo_path}

Do not open $(dirname "$repo_path"); it is only the parent folder and Source Control may not detect the nested repo.

Suggested SSH config snippet:
Host ${instance_name}
  HostName ${ip}
  User ${vm_user}
  StrictHostKeyChecking accept-new
EOF
  if [[ -n "$ssh_key" ]]; then
    cat <<EOF
  IdentityFile ${ssh_key}
EOF
  fi
}

run_remote_compose_up() {
  local remote_command
  printf -v remote_command 'cd %q && docker compose up -d && bash ./scripts/odoo-init-db.sh' "$repo_path"
  run_ssh "$remote_command"
}

run_remote_init_db() {
  local remote_command
  printf -v remote_command 'cd %q && bash ./scripts/odoo-init-db.sh' "$repo_path"
  run_ssh "$remote_command"
}

run_remote_bootstrap() {
  ensure_command ssh
  local ip
  ip="$(get_ip)"
  if [[ -z "$ip" ]]; then
    echo "Instance '$instance_name' does not have a public IP yet." >&2
    exit 1
  fi
  ssh "${ssh_args[@]}" "${vm_user}@${ip}" "bash -s -- $(printf '%q' "$repo_url") $(printf '%q' "$repo_branch") $(printf '%q' "$repo_path")" < "${ROOT_DIR}/scripts/remote-dev-bootstrap.sh"
}

fetch_branch_from_vm() {
  local remote_name="${REMOTE_DEV_FETCH_REMOTE:-gcp-dev}"
  local ip remote_url current_url

  if [[ -z "$branch_name" ]]; then
    echo "Branch name is required. Example: ./scripts/remote-dev.sh fetch-branch feature/d360-customer-workflow" >&2
    exit 1
  fi

  ensure_command git
  ensure_gcloud
  ensure_instance_exists

  ip="$(get_ip)"
  if [[ -z "$ip" ]]; then
    echo "Instance '$instance_name' does not have a public IP yet." >&2
    exit 1
  fi

  remote_url="${vm_user}@${ip}:${repo_path}"
  if git remote | grep -qx "$remote_name"; then
    current_url="$(git remote get-url "$remote_name")"
    if [[ "$current_url" != "$remote_url" ]]; then
      git remote set-url "$remote_name" "$remote_url"
    fi
  else
    git remote add "$remote_name" "$remote_url"
  fi

  git fetch "$remote_name" "$branch_name"

  if git branch --list "$branch_name" | grep -q .; then
    echo "Local branch '$branch_name' already exists. Delete or rename it before fetching from the VM." >&2
    exit 1
  fi

  git checkout -b "$branch_name" FETCH_HEAD
  git push -u origin "$branch_name"
}

case "$action" in
  init-ssh)
    init_ssh_key
    ;;
  create)
    create_instance
    ;;
  start)
    ensure_gcloud
    ensure_instance_exists
    gcloud compute instances start "$instance_name" --zone="$zone" --project="$project"
    echo
    echo "Odoo URL: http://$(get_ip):${odoo_port}"
    echo "Cursor hint: ./scripts/remote-dev.sh cursor"
    ;;
  stop)
    ensure_gcloud
    ensure_instance_exists
    gcloud compute instances stop "$instance_name" --zone="$zone" --project="$project"
    ;;
  status)
    ensure_gcloud
    ensure_instance_exists
    gcloud compute instances describe "$instance_name" --zone="$zone" --project="$project" --format='value(status)'
    ;;
  ip)
    ensure_instance_exists
    get_ip
    ;;
  url)
    ensure_instance_exists
    echo "http://$(get_ip):${odoo_port}"
    ;;
  open)
    ensure_instance_exists
    url="http://$(get_ip):${odoo_port}"
    if command -v open >/dev/null 2>&1; then
      open "$url"
    elif command -v xdg-open >/dev/null 2>&1; then
      xdg-open "$url"
    else
      echo "$url"
    fi
    ;;
  ssh)
    ensure_instance_exists
    run_ssh
    ;;
  cursor)
    ensure_instance_exists
    print_cursor_details
    ;;
  up)
    ensure_instance_exists
    run_remote_compose_up
    ;;
  init-db)
    ensure_instance_exists
    run_remote_init_db
    ;;
  bootstrap)
    ensure_instance_exists
    run_remote_bootstrap
    ;;
  fetch-branch)
    fetch_branch_from_vm
    ;;
  *)
    echo "Usage: $0 [init-ssh|create|start|stop|status|ip|url|open|ssh|cursor|up|init-db|bootstrap|fetch-branch]" >&2
    exit 1
    ;;
esac
