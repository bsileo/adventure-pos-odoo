# -*- coding: utf-8 -*-

import argparse

from odoo.addons.dive_shop_pos.seeds.scuba_shop_seed import seed


def main(env, argv=None):
    parser = argparse.ArgumentParser(description="Seed AdventurePOS dev data.")
    parser.add_argument("--profile", default="dive_shop", choices=["dive_shop"])
    parser.add_argument("--reset-seed", action="store_true")
    args = parser.parse_args(argv)

    if args.profile == "dive_shop":
        return seed(env, reset=args.reset_seed)
    raise ValueError("Unsupported seed profile: %s" % args.profile)
