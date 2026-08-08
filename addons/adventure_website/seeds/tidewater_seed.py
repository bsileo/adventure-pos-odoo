# -*- coding: utf-8 -*-
"""Tidewater contributor: enable website chrome defaults for the demo shop.

Portal users for equipment demos live in adventure_equipment_portal.
"""

import logging

_logger = logging.getLogger(__name__)


def seed_tidewater(env, reset=False):
    """Ensure Website is usable for Tidewater demos (idempotent)."""
    stats = {"created": 0, "updated": 0, "skipped": False}

    website_mod = (
        env["ir.module.module"]
        .sudo()
        .search([("name", "=", "adventure_website"), ("state", "=", "installed")], limit=1)
    )
    if not website_mod:
        stats["skipped"] = True
        stats["reason"] = "adventure_website not installed"
        return stats

    ICP = env["ir.config_parameter"].sudo()
    ICP.set_param("auth_signup.invitation_scope", "b2c")
    ICP.set_param("auth_signup.reset_password", "True")
    # Avoid broken reCAPTCHA (enabled by default when google_recaptcha is installed).
    ICP.set_param("enable_recaptcha", "False")
    stats["updated"] += 3

    company = env.company.sudo()
    Website = env["website"].sudo()
    websites = Website.search([])
    for website in websites:
        vals = {}
        if website.name != company.name:
            vals["name"] = company.name
        if company and website.company_id != company:
            vals["company_id"] = company.id
        if vals:
            website.write(vals)
            stats["updated"] += 1

    _logger.info("Tidewater adventure_website seed: %s", stats)
    return stats
