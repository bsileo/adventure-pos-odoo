#!/usr/bin/env bash
# One-time bootstrap for the shared GCP sandbox VM. Run on the VM as a sudoer.
set -euo pipefail

REPO_URL="${1:-git@github.com:bsileo/adventure-pos-odoo.git}"
REPO_BRANCH="${2:-develop}"
REPO_PATH="${3:-/srv/adventurepos/adventure-pos-odoo}"
POSTGRES_PASSWORD="${4:-}"
PARENT_DIR="$(dirname "$REPO_PATH")"
DEPLOY_USER="deploy"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This bootstrap script expects to run on the Linux sandbox VM." >&2
  exit 1
fi

if [[ -z "$POSTGRES_PASSWORD" ]]; then
  echo "POSTGRES_PASSWORD argument is required." >&2
  exit 1
fi

sudo apt-get update
sudo apt-get install -y ca-certificates curl git

if ! id -u "$DEPLOY_USER" >/dev/null 2>&1; then
  sudo useradd --create-home --shell /bin/bash "$DEPLOY_USER"
fi

if [[ ! -d /etc/apt/keyrings ]]; then
  sudo install -m 0755 -d /etc/apt/keyrings
fi

if [[ ! -f /etc/apt/keyrings/docker.asc ]]; then
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update
fi

if ! command -v docker >/dev/null 2>&1; then
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
fi

sudo usermod -aG docker "$DEPLOY_USER"
sudo usermod -aG docker "$USER" || true

sudo mkdir -p "$PARENT_DIR" "/home/${DEPLOY_USER}/.ssh"
sudo chown -R "$DEPLOY_USER:$DEPLOY_USER" "$PARENT_DIR" "/home/${DEPLOY_USER}/.ssh"
sudo chmod 700 "/home/${DEPLOY_USER}/.ssh"

if [[ ! -f "/home/${DEPLOY_USER}/.ssh/github_adventurepos" ]]; then
  sudo -u "$DEPLOY_USER" ssh-keygen -t ed25519 -f "/home/${DEPLOY_USER}/.ssh/github_adventurepos" -N ""
fi

sudo -u "$DEPLOY_USER" bash -lc "
  set -euo pipefail
  touch ~/.ssh/known_hosts
  chmod 600 ~/.ssh/known_hosts ~/.ssh/github_adventurepos
  chmod 644 ~/.ssh/github_adventurepos.pub
  if ! ssh-keygen -F github.com >/dev/null 2>&1; then
    ssh-keyscan -H github.com >> ~/.ssh/known_hosts
  fi
  cat > ~/.ssh/config <<'EOF'
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/github_adventurepos
  IdentitiesOnly yes
EOF
  chmod 600 ~/.ssh/config
"

echo "GITHUB_DEPLOY_PUBLIC_KEY_BEGIN"
sudo -u "$DEPLOY_USER" cat "/home/${DEPLOY_USER}/.ssh/github_adventurepos.pub"
echo "GITHUB_DEPLOY_PUBLIC_KEY_END"

if [[ ! -d "$REPO_PATH/.git" ]]; then
  if ! sudo -u "$DEPLOY_USER" git clone "$REPO_URL" "$REPO_PATH"; then
    echo "Repo not cloned yet; add the public key above as a GitHub deploy key, then rerun."
    exit 75
  fi
fi

sudo -u "$DEPLOY_USER" bash -lc "
  set -euo pipefail
  cd '$REPO_PATH'
  git fetch origin
  git checkout '$REPO_BRANCH'
  git reset --hard origin/'$REPO_BRANCH'
  if [[ ! -f .env ]]; then
    cp .env.example .env
    sed -i 's/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${POSTGRES_PASSWORD}/' .env
  fi
  docker compose up -d
"
