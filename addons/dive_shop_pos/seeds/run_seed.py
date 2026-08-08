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
    scuba_module = (
        env["ir.module.module"]
        .sudo()
        .search(
            [("name", "=", "adventure_equipment_scuba"), ("state", "=", "installed")],
            limit=1,
        )
    )
    if scuba_module:
        try:
            from odoo.addons.adventure_equipment_scuba.seeds.tidewater_seed import (
                seed_tidewater,
            )
        except ImportError:
            _logger.warning(
                "adventure_equipment_scuba installed but Tidewater seed contributor "
                "could not be imported"
            )
        else:
            out["adventure_equipment_scuba"] = seed_tidewater(env, reset=reset)
    else:
        out["adventure_equipment_scuba"] = {
            "skipped": True,
            "reason": "adventure_equipment_scuba not installed",
        }
    return out
