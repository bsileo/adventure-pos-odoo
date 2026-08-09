# -*- coding: utf-8 -*-
"""Tidewater contributor: sample packing lists and configurations.

Reuses dive_shop_pos_seed partners and adventure_equipment_scuba_seed assets
when present. Safe to skip when dependencies are missing.
"""

import logging

_logger = logging.getLogger(__name__)

SEED_MODULE = "adventure_equipment_configuration_seed"
CUSTOMER_MODULE = "dive_shop_pos_seed"
SCUBA_SEED_MODULE = "adventure_equipment_scuba_seed"


def seed_tidewater(env, reset=False):
    stats = {"created": 0, "updated": 0, "skipped": False}

    module = (
        env["ir.module.module"]
        .sudo()
        .search(
            [
                ("name", "=", "adventure_equipment_configuration"),
                ("state", "=", "installed"),
            ],
            limit=1,
        )
    )
    if not module:
        stats["skipped"] = True
        stats["reason"] = "adventure_equipment_configuration not installed"
        return stats

    if "adventure.equipment.configuration" not in env:
        stats["skipped"] = True
        stats["reason"] = "configuration model not loaded"
        return stats

    maya = env.ref(
        "%s.customer_certified_current" % CUSTOMER_MODULE, raise_if_not_found=False
    )
    luis = env.ref("%s.customer_nitrox" % CUSTOMER_MODULE, raise_if_not_found=False)
    if not maya and not luis:
        stats["skipped"] = True
        stats["reason"] = "Tidewater customers not seeded yet"
        return stats

    if reset:
        stats["deleted"] = _reset(env)

    company = env.company
    seeder = _TidewaterConfigurationSeed(env, company)
    if maya:
        created, updated = seeder.seed_maya(maya)
        stats["created"] += created
        stats["updated"] += updated
    if luis:
        created, updated = seeder.seed_luis(luis)
        stats["created"] += created
        stats["updated"] += updated
    return stats


def _reset(env):
    Imd = env["ir.model.data"].sudo()
    rows = Imd.search([("module", "=", SEED_MODULE)])
    deleted = 0
    # Delete configurations first (cascade lines).
    config_ids = []
    for row in rows:
        if row.model == "adventure.equipment.configuration":
            config_ids.append(row.res_id)
    configs = env["adventure.equipment.configuration"].sudo().browse(config_ids).exists()
    deleted += len(configs)
    configs.unlink()
    rows.unlink()
    return deleted


class _TidewaterConfigurationSeed:
    def __init__(self, env, company):
        self.env = env
        self.company = company
        self.imd = env["ir.model.data"].sudo()

    def _ref(self, xml_name):
        return self.env.ref("%s.%s" % (SEED_MODULE, xml_name), raise_if_not_found=False)

    def _scuba_asset(self, xml_name):
        return self.env.ref(
            "%s.%s" % (SCUBA_SEED_MODULE, xml_name), raise_if_not_found=False
        )

    def _upsert_config(self, xml_name, values, line_specs):
        Config = self.env["adventure.equipment.configuration"].sudo()
        Line = self.env["adventure.equipment.configuration.line"].sudo()
        record = self._ref(xml_name)
        created = updated = 0
        if record and record.exists():
            # Do not rewrite list_kind if lines exist.
            write_vals = {
                key: value
                for key, value in values.items()
                if key != "list_kind" or not record.line_ids
            }
            record.write(write_vals)
            updated = 1
        else:
            record = Config.create(values)
            self.imd.create(
                {
                    "name": xml_name,
                    "module": SEED_MODULE,
                    "model": Config._name,
                    "res_id": record.id,
                    "noupdate": True,
                }
            )
            created = 1

        for idx, (line_xml, line_vals) in enumerate(line_specs):
            line_vals = dict(line_vals, configuration_id=record.id, sequence=(idx + 1) * 10)
            line = self._ref(line_xml)
            if line and line.exists():
                # Avoid partner mismatch if asset missing.
                safe = {k: v for k, v in line_vals.items() if k != "configuration_id"}
                if safe.get("asset_id") is False:
                    safe.pop("asset_id", None)
                line.write(safe)
                updated += 1
                continue
            if line_vals.get("asset_id") is False:
                # Skip asset lines when scuba assets are not present.
                if line_vals.get("line_type") == "asset":
                    continue
                line_vals.pop("asset_id", None)
            line = Line.create(line_vals)
            self.imd.create(
                {
                    "name": line_xml,
                    "module": SEED_MODULE,
                    "model": Line._name,
                    "res_id": line.id,
                    "noupdate": True,
                }
            )
            created += 1
        return created, updated

    def seed_maya(self, partner):
        al80 = self._scuba_asset("eq_maya_al80")
        reg = self._scuba_asset("eq_maya_regulator")
        bcd = self._scuba_asset("eq_maya_bcd")
        computer = self._scuba_asset("eq_maya_computer")

        packing_lines = [
            (
                "line_maya_quarry_reg",
                {
                    "line_type": "asset" if reg else "text",
                    "asset_id": reg.id if reg else False,
                    "name": reg.display_name if reg else "Primary regulator",
                },
            ),
            (
                "line_maya_quarry_bcd",
                {
                    "line_type": "asset" if bcd else "text",
                    "asset_id": bcd.id if bcd else False,
                    "name": bcd.display_name if bcd else "BCD",
                },
            ),
            (
                "line_maya_quarry_computer",
                {
                    "line_type": "asset" if computer else "text",
                    "asset_id": computer.id if computer else False,
                    "name": computer.display_name if computer else "Dive computer",
                },
            ),
            (
                "line_maya_quarry_text",
                {
                    "line_type": "text",
                    "name": "Spare mask + reef-safe sunscreen",
                    "notes": "Keep in mesh bag",
                },
            ),
        ]
        created, updated = self._upsert_config(
            "cfg_maya_quarry_packing",
            {
                "name": "Quarry day packing",
                "partner_id": partner.id,
                "company_id": self.company.id,
                "list_kind": "packing",
                "customer_note": "Cold quarry checklist for Dutch Springs–style days.",
                "sequence": 10,
            },
            packing_lines,
        )

        config_lines = [
            (
                "line_maya_cold_suit_text",
                {
                    "line_type": "text",
                    "name": "Dry suit (bring from home)",
                    "role_code": "exposure",
                },
            ),
            (
                "line_maya_cold_al80",
                {
                    "line_type": "asset" if al80 else "text",
                    "asset_id": al80.id if al80 else False,
                    "name": al80.display_name if al80 else "AL80",
                    "role_code": "primary_cylinder",
                },
            ),
            (
                "line_maya_cold_reg",
                {
                    "line_type": "asset" if reg else "text",
                    "asset_id": reg.id if reg else False,
                    "name": reg.display_name if reg else "Primary regulator",
                    "role_code": "primary_reg",
                },
            ),
            (
                "line_maya_cold_weight",
                {
                    "line_type": "quantity",
                    "name": "Lead weight",
                    "quantity": 12.0,
                    "quantity_uom_label": "lb",
                    "notes": "Add 2 lb with thick undergarment",
                },
            ),
            (
                "line_maya_cold_computer",
                {
                    "line_type": "asset" if computer else "text",
                    "asset_id": computer.id if computer else False,
                    "name": computer.display_name if computer else "Computer",
                    "role_code": "primary_computer",
                },
            ),
        ]
        c2, u2 = self._upsert_config(
            "cfg_maya_cold_configuration",
            {
                "name": "Cold water configuration",
                "partner_id": partner.id,
                "company_id": self.company.id,
                "list_kind": "configuration",
                "customer_note": "Baseline cold-water setup; updated spring 2026.",
                "sequence": 20,
            },
            config_lines,
        )
        return created + c2, updated + u2

    def seed_luis(self, partner):
        packing_lines = [
            (
                "line_luis_warm_text_mask",
                {"line_type": "text", "name": "Mask / fins / snorkel"},
            ),
            (
                "line_luis_warm_text_smb",
                {"line_type": "text", "name": "SMB + spool"},
            ),
            (
                "line_luis_warm_text_cert",
                {"line_type": "text", "name": "C-card + nitrox card"},
            ),
        ]
        return self._upsert_config(
            "cfg_luis_warm_packing",
            {
                "name": "Warm water travel packing",
                "partner_id": partner.id,
                "company_id": self.company.id,
                "list_kind": "packing",
                "customer_note": "Fly-carry packing list; rent BCD/tank at destination.",
                "sequence": 10,
            },
            packing_lines,
        )
