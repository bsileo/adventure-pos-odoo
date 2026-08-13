# -*- coding: utf-8 -*-

import argparse
import logging

from odoo.addons.dive_shop_pos.seeds import tidewater_identity as identity
from odoo.addons.dive_shop_pos.seeds.scuba_shop_seed import seed


_logger = logging.getLogger(__name__)

SUPPORTED_PROFILES = (identity.SEED_PROFILE,) + identity.LEGACY_SEED_PROFILES

# Modules installed by seed-tidewater / sandbox bootstrap as the Tidewater
# Dive Shop standard package (in addition to dive_shop_pos itself).
TIDEWATER_STANDARD_MODULES = (
    "dive_shop_pos",
    "adventure_equipment_scuba",
    "adventure_website",
    "adventure_equipment_portal",
)


def main(env, argv=None):
    parser = argparse.ArgumentParser(
        description="Seed AdventurePOS Tidewater Dive Shop (sandbox) data."
    )
    parser.add_argument(
        "--profile",
        default=identity.SEED_PROFILE,
        choices=list(SUPPORTED_PROFILES),
        help="tidewater is canonical; tideledger and dive_shop remain as aliases.",
    )
    parser.add_argument("--reset-seed", action="store_true")
    args = parser.parse_args(argv)

    if args.profile not in SUPPORTED_PROFILES:
        raise ValueError("Unsupported seed profile: %s" % args.profile)

    stats = seed(env, reset=args.reset_seed)
    stats["contributors"] = _run_optional_contributors(env, reset=args.reset_seed)
    return stats


def _run_optional_contributors(env, reset=False):
    """Run module-owned Tidewater contributors when those modules are installed."""
    out = {}
    out["adventure_equipment_scuba"] = _run_contributor(
        env,
        module_name="adventure_equipment_scuba",
        import_path="odoo.addons.adventure_equipment_scuba.seeds.tidewater_seed",
        reset=reset,
    )
    out["adventure_website"] = _run_contributor(
        env,
        module_name="adventure_website",
        import_path="odoo.addons.adventure_website.seeds.tidewater_seed",
        reset=reset,
    )
    out["adventure_equipment_portal"] = _run_contributor(
        env,
        module_name="adventure_equipment_portal",
        import_path="odoo.addons.adventure_equipment_portal.seeds.tidewater_seed",
        reset=reset,
    )
    return out


def _run_contributor(env, module_name, import_path, reset=False):
    module = (
        env["ir.module.module"]
        .sudo()
        .search([("name", "=", module_name), ("state", "=", "installed")], limit=1)
    )
    if not module:
        return {"skipped": True, "reason": "%s not installed" % module_name}
    try:
        from importlib import import_module

        seed_mod = import_module(import_path)
        seed_tidewater = getattr(seed_mod, "seed_tidewater")
    except Exception:
        _logger.warning(
            "%s installed but Tidewater seed contributor could not be imported",
            module_name,
            exc_info=True,
        )
        return {"skipped": True, "reason": "import failed"}
    return seed_tidewater(env, reset=reset)
