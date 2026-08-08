# -*- coding: utf-8 -*-
"""Tidewater contributor: portal users for equipment demo customers.

Reuses dive_shop_pos_seed partner XML ids. Passwords are fictional and
documented in docs/seed-data.md.
"""

import logging

_logger = logging.getLogger(__name__)

SEED_MODULE = "adventure_equipment_portal_seed"
CUSTOMER_MODULE = "dive_shop_pos_seed"

# Fixed demo passwords (fictional) — also listed in docs/seed-data.md.
PORTAL_USERS = (
    {
        "xml_name": "portal_user_certified_current",
        "partner_xml": "customer_certified_current",
        "login": "certified_current@example.test",
        "password": "tidewater",
    },
    {
        "xml_name": "portal_user_nitrox",
        "partner_xml": "customer_nitrox",
        "login": "nitrox@example.test",
        "password": "tidewater",
    },
    {
        "xml_name": "portal_user_uncertified",
        "partner_xml": "customer_uncertified",
        "login": "uncertified@example.test",
        "password": "tidewater",
    },
)


def seed_tidewater(env, reset=False):
    stats = {"created": 0, "updated": 0, "skipped": False}

    module = (
        env["ir.module.module"]
        .sudo()
        .search(
            [("name", "=", "adventure_equipment_portal"), ("state", "=", "installed")],
            limit=1,
        )
    )
    if not module:
        stats["skipped"] = True
        stats["reason"] = "adventure_equipment_portal not installed"
        return stats

    if reset:
        stats["deleted"] = _reset(env)

    portal_group = env.ref("base.group_portal")
    Users = env["res.users"].sudo().with_context(no_reset_password=True)
    Imd = env["ir.model.data"].sudo()

    for spec in PORTAL_USERS:
        partner = env.ref(
            "%s.%s" % (CUSTOMER_MODULE, spec["partner_xml"]),
            raise_if_not_found=False,
        )
        if not partner:
            _logger.warning(
                "Tidewater portal seed: missing partner %s", spec["partner_xml"]
            )
            continue

        existing = env.ref(
            "%s.%s" % (SEED_MODULE, spec["xml_name"]), raise_if_not_found=False
        )
        vals = {
            "name": partner.name,
            "login": spec["login"],
            "partner_id": partner.id,
            "company_id": env.company.id,
            "group_ids": [(6, 0, [portal_group.id])],
        }
        if existing and existing.exists():
            # Keep password stable for demos; only refresh login/partner/groups.
            existing.write(
                {
                    "name": partner.name,
                    "login": spec["login"],
                    "partner_id": partner.id,
                    "group_ids": [(6, 0, [portal_group.id])],
                }
            )
            existing.write({"password": spec["password"]})
            stats["updated"] += 1
            continue

        user_by_login = Users.search([("login", "=", spec["login"])], limit=1)
        if user_by_login:
            user_by_login.write(
                {
                    "name": partner.name,
                    "partner_id": partner.id,
                    "group_ids": [(6, 0, [portal_group.id])],
                    "password": spec["password"],
                }
            )
            Imd.create(
                {
                    "module": SEED_MODULE,
                    "name": spec["xml_name"],
                    "model": "res.users",
                    "res_id": user_by_login.id,
                    "noupdate": True,
                }
            )
            stats["updated"] += 1
            continue

        user = Users.create({**vals, "password": spec["password"]})
        Imd.create(
            {
                "module": SEED_MODULE,
                "name": spec["xml_name"],
                "model": "res.users",
                "res_id": user.id,
                "noupdate": True,
            }
        )
        stats["created"] += 1

    _logger.info("Tidewater adventure_equipment_portal seed: %s", stats)
    return stats


def _reset(env):
    Imd = env["ir.model.data"].sudo()
    deleted = 0
    xml_records = Imd.search(
        [("module", "=", SEED_MODULE), ("model", "=", "res.users")]
    )
    for xml_record in xml_records:
        user = env["res.users"].sudo().browse(xml_record.res_id)
        if user.exists() and not user._is_admin():
            user.unlink()
            deleted += 1
        if xml_record.exists():
            xml_record.unlink()
    return deleted
