#!/usr/bin/env bash
# Manage a private Adventure POS GCP VM through OS Login and IAP.
# Usage: ./scripts/remote-dev.sh [create|start|stop|status|ip|url|open|tunnel|ssh|cursor|up|init-db|bootstrap|fetch-branch]
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

sanitize_name() {
  tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9-' '-' | sed 's/^-*//; s/-*$//; s/--*/-/g'
}

default_user="${REMOTE_DEV_USER:-${USER:-$(whoami)}}"
sanitized_user="$(printf '%s' "$default_user" | sanitize_name)"
[[ -n "$sanitized_user" ]] || sanitized_user="dev"
sanitized_user="${sanitized_user:0:40}"
sanitized_user="${sanitized_user%-}"

action="${1:-status}"
branch_name="${2:-}"
project="${REMOTE_DEV_GCP_PROJECT:-adventure-pos-sandbox}"
zone="${REMOTE_DEV_GCP_ZONE:-us-central1-a}"
instance_prefix="${REMOTE_DEV_INSTANCE_PREFIX:-adventurepos-dev}"
instance_name="${REMOTE_DEV_GCP_INSTANCE:-${instance_prefix}-${sanitized_user}}"
repo_path="${REMOTE_DEV_REPO_PATH:-/srv/adventurepos/adventure-pos-odoo}"
repo_url="${REMOTE_DEV_REPO_URL:-git@github.com:bsileo/adventure-pos-odoo.git}"
repo_branch="${REMOTE_DEV_REPO_BRANCH:-develop}"
odoo_port="${REMOTE_DEV_ODOO_PORT:-8069}"
service_account="${REMOTE_DEV_SERVICE_ACCOUNT:-adventurepos-remote-dev-vm@${project}.iam.gserviceaccount.com}"
access_scopes="${REMOTE_DEV_ACCESS_SCOPES:-cloud-platform}"

ensure_command() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 1; }
}

ensure_gcloud() { ensure_command gcloud; }

get_ip() {
  ensure_gcloud
  gcloud compute instances describe "$instance_name" --zone="$zone" --project="$project" \
    --format='value(networkInterfaces[0].networkIP)'
}

instance_exists() {
  gcloud compute instances describe "$instance_name" --zone="$zone" --project="$project" \
    --format='value(name)' >/dev/null 2>&1
}

ensure_instance_exists() {
  instance_exists || { echo "Remote dev VM '$instance_name' was not found in $project/$zone." >&2; exit 1; }
}

create_instance() {
  ensure_gcloud
  if instance_exists; then
    echo "Remote dev VM '$instance_name' already exists."
    return
  fi
  gcloud compute instances create "$instance_name" \
    --zone="$zone" --project="$project" \
    --machine-type="${REMOTE_DEV_MACHINE_TYPE:-e2-standard-2}" \
    --boot-disk-size="${REMOTE_DEV_BOOT_DISK_SIZE:-50GB}" \
    --image-family="${REMOTE_DEV_IMAGE_FAMILY:-ubuntu-2204-lts}" \
    --image-project="${REMOTE_DEV_IMAGE_PROJECT:-ubuntu-os-cloud}" \
    --service-account="$service_account" --scopes="$access_scopes" \
    --tags="${REMOTE_DEV_NETWORK_TAGS:-adventurepos-remote-dev,iap-ssh}" \
    --no-address \
    --metadata=enable-oslogin=TRUE,enable-oslogin-2fa=TRUE,block-project-ssh-keys=TRUE
}

run_ssh() {
  ensure_gcloud
  local remote_command="${1:-}"
  local args=(compute ssh "$instance_name" --zone="$zone" --project="$project" --tunnel-through-iap)
  [[ -z "$remote_command" ]] || args+=(--command="$remote_command")
  gcloud "${args[@]}"
}

run_remote_bootstrap() {
  gcloud compute ssh "$instance_name" --zone="$zone" --project="$project" --tunnel-through-iap \
    --command="bash -s -- $(printf '%q' "$repo_url") $(printf '%q' "$repo_branch") $(printf '%q' "$repo_path")" \
    < "${ROOT_DIR}/scripts/remote-dev-bootstrap.sh"
}

fetch_branch_from_vm() {
  local remote_name="${REMOTE_DEV_FETCH_REMOTE:-gcp-dev}" remote_url current_url
  [[ -n "$branch_name" ]] || { echo "Branch name is required." >&2; exit 1; }
  ensure_command git
  ensure_instance_exists
  gcloud compute config-ssh --project="$project" --tunnel-through-iap --quiet
  remote_url="${instance_name}.${zone}.${project}:${repo_path}"
  if git remote | grep -qx "$remote_name"; then
    current_url="$(git remote get-url "$remote_name")"
    [[ "$current_url" == "$remote_url" ]] || git remote set-url "$remote_name" "$remote_url"
  else
    git remote add "$remote_name" "$remote_url"
  fi
  git fetch "$remote_name" "$branch_name"
  git branch --list "$branch_name" | grep -q . && { echo "Local branch '$branch_name' already exists." >&2; exit 1; }
  git checkout -b "$branch_name" FETCH_HEAD
  git push -u origin "$branch_name"
}

case "$action" in
  create) create_instance ;;
  start)
    ensure_instance_exists
    gcloud compute instances start "$instance_name" --zone="$zone" --project="$project"
    echo "Private IP: $(get_ip)"
    echo "Run '$0 tunnel', then open http://127.0.0.1:${odoo_port}"
    ;;
  stop) ensure_instance_exists; gcloud compute instances stop "$instance_name" --zone="$zone" --project="$project" ;;
  status) ensure_instance_exists; gcloud compute instances describe "$instance_name" --zone="$zone" --project="$project" --format='value(status)' ;;
  ip) ensure_instance_exists; get_ip ;;
  url) echo "http://127.0.0.1:${odoo_port}" ;;
  open)
    url="http://127.0.0.1:${odoo_port}"
    if command -v open >/dev/null 2>&1; then open "$url"; elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$url"; else echo "$url"; fi
    ;;
  tunnel)
    ensure_instance_exists
    gcloud compute start-iap-tunnel "$instance_name" "$odoo_port" \
      --local-host-port="127.0.0.1:${odoo_port}" --zone="$zone" --project="$project"
    ;;
  ssh) ensure_instance_exists; run_ssh ;;
  cursor)
    ensure_instance_exists
    gcloud compute config-ssh --project="$project" --tunnel-through-iap --quiet
    echo "Connect Cursor to ${instance_name}.${zone}.${project}, then open ${repo_path}."
    ;;
  up) ensure_instance_exists; run_ssh "cd $(printf '%q' "$repo_path") && docker compose up -d && bash ./scripts/odoo-init-db.sh" ;;
  init-db) ensure_instance_exists; run_ssh "cd $(printf '%q' "$repo_path") && bash ./scripts/odoo-init-db.sh" ;;
  bootstrap) ensure_instance_exists; run_remote_bootstrap ;;
  fetch-branch) fetch_branch_from_vm ;;
  *) echo "Usage: $0 [create|start|stop|status|ip|url|open|tunnel|ssh|cursor|up|init-db|bootstrap|fetch-branch]" >&2; exit 1 ;;
esac
