#!/usr/bin/env bash
# Idempotent bootstrap for a developer-owned Adventure POS remote dev VM.
set -euo pipefail

REPO_URL="${1:-git@github.com:bsileo/adventure-pos-odoo.git}"
REPO_BRANCH="${2:-develop}"
REPO_PATH="${3:-/srv/adventurepos/adventure-pos-odoo}"
PARENT_DIR="$(dirname "$REPO_PATH")"
GITHUB_KEY_PATH="${HOME}/.ssh/github_adventurepos"
GITHUB_PUBLIC_KEY_PATH="${GITHUB_KEY_PATH}.pub"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This bootstrap script expects to run on a Linux VM." >&2
  exit 1
fi

if ! command -v sudo >/dev/null 2>&1; then
  echo "sudo is required on the VM." >&2
  exit 1
fi

install_git_if_needed() {
  if command -v git >/dev/null 2>&1; then
    return
  fi
  sudo apt-get update
  sudo apt-get install -y git
}

install_docker_if_needed() {
  if command -v docker >/dev/null 2>&1; then
    return
  fi

  sudo apt-get update
  sudo apt-get install -y ca-certificates curl
  sudo install -m 0755 -d /etc/apt/keyrings
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  sudo usermod -aG docker "$USER"
}

ensure_github_ssh() {
  mkdir -p "${HOME}/.ssh"
  chmod 700 "${HOME}/.ssh"
  touch "${HOME}/.ssh/known_hosts"
  chmod 600 "${HOME}/.ssh/known_hosts"

  if ! ssh-keygen -F github.com >/dev/null 2>&1; then
    ssh-keyscan -H github.com >> "${HOME}/.ssh/known_hosts"
  fi

  if [[ ! -f "$GITHUB_KEY_PATH" ]]; then
    ssh-keygen -t ed25519 -f "$GITHUB_KEY_PATH" -N ""
  fi
  chmod 600 "$GITHUB_KEY_PATH"
  chmod 644 "$GITHUB_PUBLIC_KEY_PATH"

  cat > "${HOME}/.ssh/config" <<EOF
Host github.com
  HostName github.com
  User git
  IdentityFile $GITHUB_KEY_PATH
  IdentitiesOnly yes
EOF
  chmod 600 "${HOME}/.ssh/config"
}

print_github_access_instructions() {
  cat <<EOF

GitHub access is not configured for this VM yet.

Add this public key to GitHub as either:
- a repository deploy key on the Adventure POS repo, or
- an SSH key on your GitHub user account with access to the repo

GitHub path for a deploy key:
  Repo -> Settings -> Deploy keys -> Add deploy key

Public key:
$(cat "$GITHUB_PUBLIC_KEY_PATH")

After adding the key in GitHub, rerun bootstrap from your laptop.

If you prefer HTTPS instead of SSH, set REMOTE_DEV_REPO_URL before bootstrapping.
EOF
}

ensure_workspace() {
  local cloned_repo=0

  sudo mkdir -p "$PARENT_DIR"
  sudo chown "$USER":"$USER" "$PARENT_DIR"

  if [[ ! -d "$REPO_PATH/.git" ]]; then
    if ! git clone "$REPO_URL" "$REPO_PATH"; then
      print_github_access_instructions
      exit 1
    fi
    cloned_repo=1
  fi

  cd "$REPO_PATH"

  if [[ "$cloned_repo" -eq 1 ]]; then
    git checkout "$REPO_BRANCH"
  fi

  if [[ ! -f .env && -f .env.example ]]; then
    cp .env.example .env
  fi
}

install_git_if_needed
install_docker_if_needed
ensure_github_ssh
ensure_workspace

cat <<EOF
Remote dev VM bootstrap complete.

Repo path: $REPO_PATH
Branch to use: $REPO_BRANCH

Next steps:
1. SSH back in if Docker was just installed so your user picks up the docker group.
2. Review $REPO_PATH/.env and set POSTGRES_PASSWORD plus any optional keys.
3. Start services with: cd $REPO_PATH && docker compose up -d
4. Initialize the database once if needed with:
   cd $REPO_PATH && bash ./scripts/odoo-init-db.sh
EOF
