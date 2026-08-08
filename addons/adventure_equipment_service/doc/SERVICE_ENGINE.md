# Generic Equipment Service Engine

## Four concepts

1. **Equipment lifecycle** (`adventure.equipment.asset.lifecycle_state`) — operational state of the physical object.
2. **Service policy** — reusable rule: which equipment gets which service on what schedule.
3. **Service requirement** — one obligation on one asset (due dates + status).
4. **Service record** — permanent evidence of completed work.

Service status never auto-changes equipment lifecycle.

## Policy matching

`adventure.equipment.service.policy.find_applicable_policies(asset, on_date)`

Checks company, active flag, effective/expiration dates, then structured fields:

- product variant / template
- brand / manufacturer / model (case-insensitive)
- category
- tag
- company default / untargeted

No stored Python expressions.

## Precedence

`select_winning_policies` keeps **one winner per service type**:

1. Product variant (100)
2. Product template (90)
3. Brand + model (80)
4. Brand / manufacturer / model alone (70)
5. Category (60)
6. Tag (50)
7. Company default (10) / untargeted (5)

Tie-break: higher `priority`, then lower `id`.

Different service types always coexist.

## Requirement deduplication

- At most one **active policy-managed** requirement per `(asset, service_type)`.
- Manual / bulletin requirements are never removed by sync.
- Competing policies update `source_policy_id` on the single managed row.
- Superseded duplicates are deactivated/suspended, not deleted.

## Date math

- Days/weeks: `timedelta`
- Months/years: `dateutil.relativedelta` (calendar-aware; 12 months ≠ 365 days)

### Warning / due / grace (inclusive)

- `warning_date = due - warning_lead_days`
- `grace_date = due + grace_days` when grace > 0
- `today < warning` → current
- `warning <= today < due` → due_soon
- `due <= today` and (`today <= grace` or no grace on due day) → due
- after grace (or after due when no grace) → overdue

## Status aging

Dates are stored. `status` is persisted but recomputed by:

- requirement/policy/service writes
- `action_recalculate_status`
- daily `ir.cron` (`cron_process_equipment_service`)

Routine aging uses `mail_notrack` to avoid chatter spam.

## Next-due precedence after service completion

1. Explicit `next_recommended_date` on the service record
2. Active requirement override (left intact)
3. Policy / requirement interval from `service_date`
4. Unknown / incomplete history

## Overrides / waivers

- Managers only
- Audited (user, timestamp, reason, optional expiration)
- Policy sync does not erase active overrides
- Expired waivers/overrides reactivate evaluation automatically

## Service record states

`draft` → `completed` → `verified` → (optional) `voided`

Completed/verified records are protected; corrections void + replace.

## Cron / batching

- Batch size: 200 assets (`SERVICE_CRON_BATCH_SIZE`)
- Continuation via `ir.config_parameter` `adventure_equipment_service.cron_last_asset_id`
- Idempotent; no notifications/emails

## Asset rollup severity

Overdue → Due → Due Soon → Unknown → Current → Not Applicable

Waived/suspended/completed ignored for severity.

## Phase 3B extension points

Vertical modules (e.g. `adventure_equipment_scuba`) can:

- add service type / policy data XML
- inherit asset/requirement/record for sport fields
- extend matching via `_matches_asset` / `_specificity_score` overrides if needed
- add views/menus/tests without changing the generic engine core
