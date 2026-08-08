# Lifecycle states and transitions

Equipment **lifecycle** (`lifecycle_state`) describes operational status. It is separate from the Odoo **Archive** flag (`active`): archiving hides a record without changing lifecycle (see [Staff guide](STAFF_GUIDE.md)).

## States

| State | Meaning |
|-------|---------|
| `draft` | Registered but not yet in service |
| `active` | In normal use |
| `in_service` | With a technician / service provider |
| `out_for_service` | Temporarily unavailable for service |
| `loaned` | Loaned to someone (not a full ownership transfer) |
| `transferred` | Marked as transferred out (reclaim via transition to `active`) |
| `lost` | Reported lost |
| `stolen` | Reported stolen |
| `retired` | End of useful life; history retained |
| `disposed` | Final disposition; terminal state |

## Allowed transitions

Source: `LIFECYCLE_TRANSITIONS` in `models/equipment_asset.py`.

| From state | Allowed next states |
|------------|---------------------|
| `draft` | `active`, `retired`, `disposed` |
| `active` | `in_service`, `out_for_service`, `loaned`, `transferred`, `lost`, `stolen`, `retired`, `disposed` |
| `in_service` | `active`, `out_for_service`, `loaned`, `lost`, `stolen`, `retired`, `disposed` |
| `out_for_service` | `active`, `in_service`, `retired`, `disposed` |
| `loaned` | `active`, `lost`, `stolen`, `transferred` |
| `transferred` | `active` |
| `lost` | `active`, `retired`, `disposed` |
| `stolen` | `active`, `retired`, `disposed` |
| `retired` | `active`, `disposed` |
| `disposed` | *(none — terminal)* |

Invalid transitions raise a user error. Technical writes may pass context `equipment_skip_lifecycle_check` (internal use only).

## Common staff actions

| UI action | Typical transition |
|-----------|-------------------|
| Activate | → `active` (sets `in_service_date` if empty) |
| Mark out for service | → `out_for_service` |
| Returned from service | → `active` |
| Retire | → `retired` (sets `retired_on`) |
| Mark lost | → `lost` (sets `lost_on`) |
| Reactivate | → `active` |

Each meaningful change should generate an `adventure.equipment.event` row.

## Deletion policy

Only **draft** assets with at most one ownership row, no extra events beyond registration, and no documents may be deleted. Otherwise retire or archive.
