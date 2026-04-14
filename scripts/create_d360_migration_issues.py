"""Create GitHub issues + Project items for Dive Shop 360 migration.

Usage (repo root, with ``gh`` authenticated):

  python scripts/create_d360_migration_issues.py
  python scripts/create_d360_migration_issues.py 5   # skip first 5 definitions (recovery)

Edits ``REPO``, ``BRANCH``, ``MILESTONE``, ``PROJECT`` at top if your fork differs.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

REPO = "bsileo/adventure-pos-odoo"
BRANCH = "feat/chore-github-development-tracking"
MILESTONE = "Migration: Dive Shop 360"
PROJECT = 5
PROJECT_OWNER = "bsileo"
DOC = f"https://github.com/{REPO}/blob/{BRANCH}/docs/migrations"
SCRIPTS = f"https://github.com/{REPO}/blob/{BRANCH}/scripts/migrations"


def doc_link(filename: str) -> str:
    return f"[{filename}]({DOC}/{filename})"


def script_readme_link() -> str:
    return f"[README.md]({SCRIPTS}/README.md)"


def related_repo(path: str) -> str:
    return f"https://github.com/{REPO}/blob/{BRANCH}/{path}"


def run_gh(argv: list[str], input_text: str | None = None) -> str:
    r = subprocess.run(
        ["gh", *argv],
        capture_output=True,
        text=True,
        input=input_text,
        check=True,
    )
    return (r.stdout or "").strip()


def add_issue(title: str, body: str, labels: list[str] | None = None) -> int:
    labels = labels or ["type:chore"]
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", encoding="utf-8", delete=False
    ) as tmp:
        tmp.write(body)
        path = tmp.name
    try:
        args = [
            "issue",
            "create",
            "-R",
            REPO,
            "-t",
            title,
            "-F",
            path,
            "--milestone",
            MILESTONE,
        ]
        for lb in labels:
            args.extend(["-l", lb])
        url = run_gh(args)
        m = re.search(r"/issues/(\d+)(?:\s|$)", url)
        if not m:
            raise RuntimeError(f"Could not parse issue number from: {url!r}")
        num = int(m.group(1))
        run_gh(
            [
                "project",
                "item-add",
                str(PROJECT),
                "--owner",
                PROJECT_OWNER,
                "--url",
                f"https://github.com/{REPO}/issues/{num}",
            ]
        )
        print(f"Created #{num}: {title}")
        return num
    finally:
        Path(path).unlink(missing_ok=True)


def main() -> None:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    skip = int(sys.argv[1]) if len(sys.argv) > 1 else 0

    catalog = related_repo("docs/data-model/product-catalog.md")
    tenant = related_repo("docs/architecture/tenant-provisioning.md")

    issues: list[tuple[str, str, list[str] | None]] = [
        (
            "migration(d360): program overview & doc index",
            f"""## Program overview

Tracking issue for **Dive Shop 360 → Adventure POS** migration work (milestone **{MILESTONE}**).

**Doc index:** {doc_link("README.md")}

### Workstream issues

Link child issues from the board; this issue is the entry point.

**Branch for doc links:** `{BRANCH}` (point to `main` after merge).
""",
            None,
        ),
        (
            "migration(d360): document Dive Shop 360 export surface",
            f"""## Epic 1 — Source system inventory

Complete the per-object export inventory during discovery (UI/API paths, formats, limits, samples).

**Doc:** {doc_link("dive-shop-360-export-inventory.md")}

### Acceptance criteria
- [ ] Table filled for customers, products, sales, certs, gift cards, layaways, etc.
- [ ] Gaps and follow-ups recorded in the doc
""",
            None,
        ),
        (
            "migration(d360): obtain sanitized sample exports (pilot + edge cases)",
            f"""## Epic 1 — Sample data

Collect redacted or secure-store samples: small shop, large catalog, messy variants, international, tax edge cases.

**Doc:** {doc_link("sample-exports-pii-and-retention.md")} (sample exports & PII)

### Acceptance criteria
- [ ] At least one full-object sample set per critical entity (where D360 allows)
- [ ] No raw PII committed to the repo
""",
            None,
        ),
        (
            "migration(d360): define retention and parallel-run policy",
            f"""## Epic 1 — Operational policy

Agree freeze, read-only D360 window, accounting ownership, export retention.

**Doc:** {doc_link("sample-exports-pii-and-retention.md")} (parallel-run & retention)

### Acceptance criteria
- [ ] Written policy per engagement template in doc
- [ ] Contacts / roles filled for next pilot
""",
            None,
        ),
        (
            "migration(d360): D360 → Odoo mapping matrix",
            f"""## Epic 2 — Mapping

Fill mapping matrix: source fields → Odoo models, transforms, idempotency keys, owner (master vs tenant).

**Doc:** {doc_link("dive-shop-360-odoo-mapping.md")}
**Related:** [product catalog model]({catalog})

### Acceptance criteria
- [ ] One row per migrated object type needed for go-live
- [ ] Gap log started with owners
""",
            None,
        ),
        (
            "migration(d360): decide catalog strategy for migrated shops",
            f"""## Epic 2 — Catalog strategy

Choose tenant-local import vs master baseline vs hybrid; record decision for pilots.

**Doc:** {doc_link("catalog-strategy-migrated-shops.md")}

### Acceptance criteria
- [ ] Strategy A/B/C selected and signed off
- [ ] Linked from mapping matrix where product owner depends on it
""",
            None,
        ),
        (
            "migration(d360): certifications / training data approach",
            f"""## Epic 2 — Certs / training

Pick archive-only, partner notes, or custom model path; sync with D360 export reality.

**Doc:** {doc_link("certifications-training-migration.md")}

### Acceptance criteria
- [ ] Option 1/2/3 chosen and rationale recorded
- [ ] Follow-on module issue filed if Option 3
""",
            None,
        ),
        (
            "migration(d360): migration phases, checkpoints, rollback triggers",
            f"""## Epic 3 — Process

Operationalize discover → dry-run → pilot → cutover → hypercare with rollback thresholds.

**Doc:** {doc_link("runbook-phases-and-checkpoints.md")}

### Acceptance criteria
- [ ] Team agrees checkpoints C1–C4
- [ ] Example rollback triggers tuned for first customer
""",
            None,
        ),
        (
            "migration(d360): cutover weekend checklist",
            f"""## Epic 3 — Cutover

Freeze, import order, smoke tests, artifacts checklist for go-live weekend.

**Doc:** {doc_link("runbook-cutover-weekend.md")}

### Acceptance criteria
- [ ] Checklist used in one table-top exercise
- [ ] Import order aligned with stock/history strategy
""",
            None,
        ),
        (
            "migration(d360): validation report template adoption",
            f"""## Epic 3 — Validation

Use consistent post-import counts, spot checks, accounting handoff.

**Doc:** {doc_link("validation-report-template.md")}

### Acceptance criteria
- [ ] Template completed for first dry-run
- [ ] Accountant sign-off line understood by shop
""",
            None,
        ),
        (
            "migration(d360): evaluate Odoo import tooling (UI vs RPC vs shell)",
            f"""## Epic 4 — Tooling

Pick defaults per object type; document for implementers.

**Doc:** {doc_link("odoo-import-tooling-evaluation.md")}

### Acceptance criteria
- [ ] Decision table filled for products, partners, stock, history
- [ ] Script location convention agreed (if any)
""",
            None,
        ),
        (
            "migration(d360): chart of accounts & fiscal localization baseline",
            f"""## Epic 4 — Fiscal baseline

CoA, taxes, journals before transactional / stock imports.

**Doc:** {doc_link("chart-of-accounts-localization.md")}
**Related:** [tenant provisioning]({tenant})

### Acceptance criteria
- [ ] Checklist in doc completed for pilot tenant country
- [ ] Accountant review recorded
""",
            None,
        ),
        (
            "migration(d360): stock opening & valuation strategy (no double-count)",
            f"""## Epic 4 — Stock

Opening inventory vs historical window; align with accountant.

**Doc:** {doc_link("stock-opening-valuation-strategy.md")}
**Related:** historical POS spike doc

### Acceptance criteria
- [ ] Method A/B chosen; cutover date rule documented
- [ ] Linked to validation report expectations
""",
            None,
        ),
        (
            "migration(d360): D360 CSV normalizer spec (optional tool)",
            f"""## Epic 5 — Normalizer

Implement only if pilots need transforms; PII-safe logging.

**Doc:** {doc_link("d360-csv-normalizer-spec.md")}
**Scripts stub:** {script_readme_link()}

### Acceptance criteria
- [ ] Build/no-build decision after first pilot imports
- [ ] If built, lives under agreed path with no secrets in repo
""",
            None,
        ),
        (
            "migration(d360): external ID convention for idempotent reimports",
            f"""## Epic 5 — External IDs

Standardize `d360.{{object}}.{{id}}` usage across CSV/RPC imports.

**Doc:** {doc_link("external-id-convention.md")}

### Acceptance criteria
- [ ] Convention reflected in mapping matrix
- [ ] Idempotency test passes (see related issue)
""",
            None,
        ),
        (
            "migration(d360): historical POS / sales import spike (risk:db-migration)",
            f"""## Epic 5 — History import

Spike recent-window history without breaking stock or closed periods; accountant sign-off.

**Doc:** {doc_link("historical-pos-import-spike.md")}

### Acceptance criteria
- [ ] Approach chosen (full POS vs journal-only vs archive, etc.)
- [ ] Prototype on copy DB with N-month subset
""",
            ["type:chore", "risk:db-migration"],
        ),
        (
            "migration(d360): pilot dry-run on staging tenant DB",
            f"""## Epic 6 — Pilot

Full pipeline on staging; runtime and failure metrics.

**Doc:** {doc_link("pilot-dry-run-procedure.md")}

### Acceptance criteria
- [ ] Dry-run executed with validation report
- [ ] Gaps logged to mapping matrix
""",
            None,
        ),
        (
            "migration(d360): idempotency test (double-import safety)",
            f"""## Epic 6 — Hardening

Prove second run does not duplicate partners/products/stock.

**Doc:** {doc_link("idempotency-test-procedure.md")}

### Acceptance criteria
- [ ] Test executed on disposable DB copy
- [ ] Pass/fail recorded; fixes tracked if fail
""",
            None,
        ),
        (
            "migration(d360): staff training & hypercare checklist",
            f"""## Epic 6 — Go-live support

Train on Odoo POS vs D360; run hypercare checklist.

**Doc:** {doc_link("training-hypercare-checklist.md")}

### Acceptance criteria
- [ ] Training session completed; attendee list
- [ ] Known differences table filled for first customer
""",
            None,
        ),
    ]

    for title, body, labels in issues[skip:]:
        add_issue(title, body, labels)

    print("Done. Open project:", f"https://github.com/users/{PROJECT_OWNER}/projects/{PROJECT}")


if __name__ == "__main__":
    main()
