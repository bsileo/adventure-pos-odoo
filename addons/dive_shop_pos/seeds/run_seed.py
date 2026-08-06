# -*- coding: utf-8 -*-

import argparse

from odoo.addons.dive_shop_pos.seeds import tideledger_identity as identity
from odoo.addons.dive_shop_pos.seeds.scuba_shop_seed import seed


SUPPORTED_PROFILES = (identity.SEED_PROFILE, identity.LEGACY_SEED_PROFILE)


def main(env, argv=None):
    parser = argparse.ArgumentParser(
        description="Seed AdventurePOS Tideledger (sandbox dive shop) data."
    )
    parser.add_argument(
        "--profile",
        default=identity.SEED_PROFILE,
        choices=list(SUPPORTED_PROFILES),
        help="tideledger is canonical; dive_shop remains as a legacy alias.",
    )
    parser.add_argument("--reset-seed", action="store_true")
    args = parser.parse_args(argv)

    if args.profile in SUPPORTED_PROFILES:
        return seed(env, reset=args.reset_seed)
    raise ValueError("Unsupported seed profile: %s" % args.profile)
