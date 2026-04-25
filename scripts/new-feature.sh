#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 1 ]] || [[ -z "${1// }" ]]; then
  echo "Usage: scripts/new-feature.sh <feature-name>" >&2
  exit 1
fi

feature_name="$1"
branch_name="feature/${feature_name}"

git fetch origin
git switch develop
git pull origin develop
git switch -c "${branch_name}"

echo "Created feature branch from develop: ${branch_name}"
