#!/usr/bin/env bash
# Create or update GitHub labels for Adventure POS. Requires: gh auth login
# Usage: ./scripts/sync-github-labels.sh
set -euo pipefail
cd "$(dirname "$0")/.."

upsert_label() {
  local name="$1"
  local color="$2"
  local desc="${3:-}"
  if gh label create "$name" --color "$color" --description "$desc" 2>/dev/null; then
    return 0
  fi
  gh label edit "$name" --color "$color" --description "$desc"
}

# type / process
upsert_label "type:chore" "C5DEF5" "Tooling, docs-only, or internal refactor"
upsert_label "risk:db-migration" "B60205" "Schema/data migration—test upgrades carefully"
upsert_label "agent:ready" "0E7490" "Spec complete enough for an AI agent to implement"

# modules (match addons/*)
upsert_label "module:adventure_base" "0E8A16" "addons/adventure_base"
upsert_label "module:adventure_pos" "5319E7" "addons/adventure_pos"
upsert_label "module:adventure_inventory" "FBCA04" "addons/adventure_inventory"
upsert_label "module:adventure_customers" "D4C5F9" "addons/adventure_customers"
upsert_label "module:adventure_purchase" "F9D0C4" "addons/adventure_purchase"
upsert_label "module:adventure_reports" "C2E0C6" "addons/adventure_reports"

echo "Labels synced. Default templates use GitHub's built-in bug / enhancement labels."
