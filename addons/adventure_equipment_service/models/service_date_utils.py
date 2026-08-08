# -*- coding: utf-8 -*-
"""Shared date arithmetic for equipment service forecasting.

Interval units use calendar-aware math for months/years (via
``dateutil.relativedelta``) and fixed spans for days/weeks. Do not treat
12 months as 365 days.
"""

from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields


INTERVAL_UNITS = [
    ("days", "Days"),
    ("weeks", "Weeks"),
    ("months", "Months"),
    ("years", "Years"),
]

# Cron / sync batch size for large fleets.
SERVICE_CRON_BATCH_SIZE = 200


def to_date(value):
    """Normalize Odoo date/datetime/string values to ``datetime.date``."""
    if not value:
        return False
    if isinstance(value, date) and not hasattr(value, "hour"):
        return value
    return fields.Date.to_date(value)


def add_interval(start, quantity, unit):
    """Add a schedule interval to ``start``.

    :param start: baseline date
    :param quantity: positive integer
    :param unit: days|weeks|months|years
    """
    start = to_date(start)
    if not start or not quantity or not unit:
        return False
    quantity = int(quantity)
    if unit == "days":
        return start + timedelta(days=quantity)
    if unit == "weeks":
        return start + timedelta(weeks=quantity)
    if unit == "months":
        return start + relativedelta(months=quantity)
    if unit == "years":
        return start + relativedelta(years=quantity)
    raise ValueError(f"Unsupported interval unit: {unit}")


def subtract_days(value, days):
    value = to_date(value)
    if not value:
        return False
    return value - timedelta(days=int(days or 0))


def add_days(value, days):
    value = to_date(value)
    if not value:
        return False
    return value + timedelta(days=int(days or 0))


def compute_schedule_dates(due_date, warning_lead_days=0, grace_days=0):
    """Return ``(warning_date, due_date, grace_date)``.

    Semantics (inclusive boundaries used by status aging):

    * ``warning_date`` = due_date - warning_lead_days (or due_date if lead is 0)
    * ``grace_date`` = due_date + grace_days when grace_days > 0, else False
    """
    due_date = to_date(due_date)
    if not due_date:
        return False, False, False
    warning_lead_days = int(warning_lead_days or 0)
    grace_days = int(grace_days or 0)
    warning_date = (
        subtract_days(due_date, warning_lead_days) if warning_lead_days else due_date
    )
    grace_date = add_days(due_date, grace_days) if grace_days else False
    return warning_date, due_date, grace_date


def compute_requirement_status(
    *,
    today,
    due_date=None,
    warning_date=None,
    grace_date=None,
    waived=False,
    suspended=False,
    not_applicable=False,
    completed=False,
):
    """Pure status helper used by stored recomputation and tests.

    Inclusive/exclusive rules:

    * ``today < warning_date`` → current
    * ``warning_date <= today < due_date`` → due_soon
    * ``due_date <= today`` and (no grace or ``today <= grace_date``) → due
    * ``today > grace_date`` (or ``today > due_date`` when no grace) → overdue
    """
    if not_applicable:
        return "not_applicable"
    if waived:
        return "waived"
    if suspended:
        return "suspended"
    if completed:
        return "completed"

    due_date = to_date(due_date)
    if not due_date:
        return "unknown"

    today = to_date(today) or date.today()
    warning_date = to_date(warning_date) or due_date
    grace_date = to_date(grace_date)

    if today < warning_date:
        return "current"
    if today < due_date:
        return "due_soon"
    if grace_date:
        if today <= grace_date:
            return "due"
        return "overdue"
    # No grace: due on due_date, overdue after due_date.
    if today == due_date:
        return "due"
    if today > due_date:
        return "overdue"
    return "current"


# Asset rollup severity (highest wins among active evaluated requirements).
ASSET_STATUS_SEVERITY = {
    "overdue": 60,
    "due": 50,
    "due_soon": 40,
    "unknown": 30,
    "attention_required": 25,
    "current": 20,
    "not_applicable": 10,
}


def rollup_asset_service_status(requirement_statuses):
    """Compute asset-level service status from requirement statuses.

    Waived/suspended/completed requirements are ignored for severity. If only
    those remain (or there are no requirements), returns ``not_applicable``.
    """
    evaluated = [
        status
        for status in requirement_statuses
        if status not in ("waived", "suspended", "completed")
    ]
    if not evaluated:
        return "not_applicable"
    best = max(evaluated, key=lambda status: ASSET_STATUS_SEVERITY.get(status, 0))
    if best in (
        "overdue",
        "due",
        "due_soon",
        "unknown",
        "current",
        "not_applicable",
    ):
        return best
    return "attention_required"
