# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from .registry import SeedRegistry


SEED_MODULE = "dive_shop_pos_seed"


class ScubaShopSeed:
    def __init__(self, env, reset=False):
        self.env = env
        self.registry = SeedRegistry(env, SEED_MODULE)
        self.reset_requested = reset
        self.records = {}
        self.stats = {}

    def run(self):
        if self.reset_requested:
            self.stats["deleted"] = self.registry.reset()
        self._seed_company()
        self._seed_categories()
        self._seed_products()
        self._seed_customers()
        self._seed_packages()
        self._seed_assets()
        self._seed_fee_rules()
        self._seed_reservations()
        self._seed_condition_and_maintenance()
        self.stats.update(self.registry.summary())
        self.stats.update(self._counts())
        return self.stats

    def _seed_company(self):
        company = self.registry.upsert(
            "res.company",
            "company_adventure_dive_center_dev",
            {
                "name": "Adventure Dive Center - Dev",
                "email": "ops@adventuredive.example",
                "phone": "+1 555-0100",
                "street": "100 Marina Way",
                "city": "Key Largo",
                "zip": "33037",
            },
        )
        self.records["company"] = company

    def _seed_categories(self):
        categories = {
            "rental_gear": "Dive Rental Gear",
            "rental_fees": "Dive Rental Fees",
            "fills_service": "Dive Fills & Service",
        }
        for key, name in categories.items():
            self.records["product_category_%s" % key] = self.registry.upsert(
                "product.category",
                "category_%s" % key,
                {"name": name},
            )
            self.records["pos_category_%s" % key] = self.registry.upsert(
                "pos.category",
                "pos_category_%s" % key,
                {"name": name},
            )

    def _seed_products(self):
        rental_specs = [
            ("full_scuba_kit", "Full Scuba Kit Rental", 89.0, "rental_gear", False),
            ("bcd", "BCD Rental", 28.0, "rental_gear", False),
            ("regulator_set", "Regulator Set Rental", 34.0, "rental_gear", True),
            ("wetsuit", "Wetsuit Rental", 24.0, "rental_gear", False),
            ("dive_computer", "Dive Computer Rental", 30.0, "rental_gear", True),
            ("aluminum_80_tank", "Aluminum 80 Tank Rental", 18.0, "rental_gear", True),
            ("mask_fins_snorkel", "Mask/Fins/Snorkel Rental", 22.0, "rental_gear", False),
            ("weight_system", "Weight System Rental", 12.0, "rental_gear", False),
        ]
        fee_specs = [
            ("rental_deposit", "Rental Deposit", 200.0, "rental_fees"),
            ("late_return_fee", "Late Return Fee", 35.0, "rental_fees"),
            ("damage_fee", "Damage Fee", 75.0, "rental_fees"),
            ("tank_fill_fee", "Tank Fill Fee", 12.0, "fills_service"),
            ("cleaning_adjustment_fee", "Cleaning/Adjustment Fee", 15.0, "fills_service"),
        ]
        for key, name, price, category_key, tracked in rental_specs:
            self.records["product_%s" % key] = self._product(
                key,
                name,
                price,
                category_key,
                is_rental=True,
                tracked=tracked,
            )
        for key, name, price, category_key in fee_specs:
            self.records["product_%s" % key] = self._product(
                key,
                name,
                price,
                category_key,
                is_rental=False,
                tracked=False,
            )

    def _product(self, key, name, price, category_key, is_rental, tracked):
        category = self.records["product_category_%s" % category_key]
        pos_category = self.records["pos_category_%s" % category_key]
        values = {
            "name": name,
            "sale_ok": True,
            "purchase_ok": False,
            "available_in_pos": True,
            "list_price": price,
            "standard_price": 0.0,
            "categ_id": category.id,
            "pos_categ_ids": [(6, 0, [pos_category.id])],
            "is_rental": is_rental,
            "tracking": "serial" if tracked else "none",
            "type": "consu",
            "detailed_type": "consu",
        }
        return self.registry.upsert("product.template", "product_%s" % key, values)

    def _seed_customers(self):
        customers = [
            (
                "customer_certified_current",
                "Maya Carter",
                {
                    "certification": {"agency": "PADI", "level": "Open Water", "expires": False},
                    "waiver": {"status": "current", "signed_on": "2026-01-15"},
                },
            ),
            (
                "customer_certified_expired_waiver",
                "Jon Ellis",
                {
                    "certification": {"agency": "SSI", "level": "Advanced Open Water", "expires": False},
                    "waiver": {"status": "expired", "signed_on": "2024-03-20"},
                },
            ),
            (
                "customer_uncertified",
                "Nora Singh",
                {
                    "certification": {"agency": False, "level": False, "expires": False},
                    "waiver": {"status": "missing", "signed_on": False},
                },
            ),
            (
                "customer_nitrox",
                "Luis Romero",
                {
                    "certification": {"agency": "NAUI", "level": "Nitrox", "expires": False},
                    "waiver": {"status": "current", "signed_on": "2026-02-08"},
                },
            ),
            (
                "customer_group",
                "Carter Family Dive Group",
                {
                    "group_size": 4,
                    "waiver": {"status": "partial", "signed_on": "2026-04-12"},
                },
            ),
        ]
        for key, name, payload in customers:
            self.records[key] = self.registry.upsert(
                "res.partner",
                key,
                {
                    "name": name,
                    "customer_rank": 1,
                    "email": "%s@example.test" % key.replace("customer_", ""),
                    "phone": "+1 555-%04d" % (1000 + len(self.records)),
                    "comment": "Dive shop seed customer. Requirements: %s" % payload,
                },
            )

    def _seed_packages(self):
        package_specs = [
            (
                "package_full_scuba_kit",
                "Full Scuba Kit",
                "full_scuba_kit",
                [
                    {"product": "bcd", "quantity": 1, "size_required": True},
                    {"product": "regulator_set", "quantity": 1, "serial_required": True},
                    {"product": "wetsuit", "quantity": 1, "size_required": True},
                    {"product": "aluminum_80_tank", "quantity": 1, "serial_required": True, "fill_required": True},
                    {"product": "mask_fins_snorkel", "quantity": 1, "size_required": True},
                    {"product": "weight_system", "quantity": 1, "weight_preference_required": True},
                ],
            ),
            (
                "package_bcd_regulator",
                "BCD + Regulator",
                "bcd",
                [
                    {"product": "bcd", "quantity": 1, "size_required": True},
                    {"product": "regulator_set", "quantity": 1, "serial_required": True},
                ],
            ),
            (
                "package_tank_weights",
                "Tank + Weights",
                "aluminum_80_tank",
                [
                    {"product": "aluminum_80_tank", "quantity": 1, "serial_required": True, "fill_required": True},
                    {"product": "weight_system", "quantity": 1, "weight_preference_required": True},
                ],
            ),
            (
                "package_snorkel_set",
                "Snorkel Set",
                "mask_fins_snorkel",
                [{"product": "mask_fins_snorkel", "quantity": 1, "size_required": True}],
            ),
            (
                "package_dive_computer_add_on",
                "Dive Computer Add-on",
                "dive_computer",
                [{"product": "dive_computer", "quantity": 1, "serial_required": True}],
            ),
        ]
        for key, name, package_product_key, components in package_specs:
            payload = []
            for component in components:
                product = self.records["product_%s" % component["product"]].product_variant_id
                payload_component = dict(component)
                payload_component["product_id"] = product.id
                payload_component["product_xml_id"] = "%s.product_%s" % (SEED_MODULE, component["product"])
                payload.append(payload_component)
            self.records[key] = self.registry.upsert(
                "adventure.rental.package.template",
                key,
                {
                    "name": name,
                    "product_id": self.records["product_%s" % package_product_key].product_variant_id.id,
                    "component_payload": payload,
                    "requirement_payload": {
                        "vertical": "scuba",
                        "requires_certification": name != "Snorkel Set",
                        "requires_waiver": True,
                    },
                },
            )

    def _seed_assets(self):
        asset_specs = [
            ("asset_bcd_xs_001", "BCD-XS-001", "bcd", "BCD-XS-001", "XS", "available", "good", 180),
            ("asset_bcd_m_001", "BCD-M-001", "bcd", "BCD-M-001", "M", "reserved", "good", 180),
            ("asset_bcd_l_001", "BCD-L-001", "bcd", "BCD-L-001", "L", "checked_out", "good", 180),
            ("asset_bcd_xl_001", "BCD-XL-001", "bcd", "BCD-XL-001", "XL", "repair", "damaged", 15),
            ("asset_reg_001", "REG-001", "regulator_set", "REG-001", False, "available", "good", 45),
            ("asset_reg_002", "REG-002", "regulator_set", "REG-002", False, "maintenance_due", "worn", -5),
            ("asset_reg_003", "REG-003", "regulator_set", "REG-003", False, "checked_out", "good", 90),
            ("asset_tank_al80_001", "AL80-001", "aluminum_80_tank", "AL80-001", False, "available", "good", 365),
            ("asset_tank_al80_002", "AL80-002", "aluminum_80_tank", "AL80-002", False, "checked_out", "good", 120),
            ("asset_tank_al80_003", "AL80-003", "aluminum_80_tank", "AL80-003", False, "maintenance_due", "worn", -30),
            ("asset_computer_001", "DC-001", "dive_computer", "DC-001", False, "available", "good", 240),
            ("asset_computer_002", "DC-002", "dive_computer", "DC-002", False, "retired", "damaged", -180),
            ("asset_wetsuit_m_001", "WS-M-001", "wetsuit", "WS-M-001", "M", "available", "good", 120),
            ("asset_wetsuit_l_001", "WS-L-001", "wetsuit", "WS-L-001", "L", "available", "worn", 120),
            ("asset_snorkel_set_001", "MFS-001", "mask_fins_snorkel", "MFS-001", "M/L", "available", "good", 90),
            ("asset_weight_system_001", "WGT-001", "weight_system", "WGT-001", False, "available", "good", 90),
        ]
        for key, name, product_key, barcode, size, state, condition, service_offset in asset_specs:
            product = self.records["product_%s" % product_key].product_variant_id
            lot = False
            if product.tracking != "none":
                lot = self.registry.upsert(
                    "stock.lot",
                    "lot_%s" % key.replace("asset_", ""),
                    {
                        "name": barcode,
                        "product_id": product.id,
                        "company_id": self.records["company"].id,
                    },
                )
            self.records[key] = self.registry.upsert(
                "adventure.rental.asset",
                key,
                {
                    "name": name,
                    "product_id": product.id,
                    "lot_id": lot.id if lot else False,
                    "barcode": barcode,
                    "state": state,
                    "condition_state": condition,
                    "service_due_date": self.registry.today() + timedelta(days=service_offset),
                    "requirement_payload": {
                        "vertical": "scuba",
                        "size_code": size,
                        "service_profile": self._service_profile(product_key, service_offset),
                    },
                },
            )

    def _service_profile(self, product_key, service_offset):
        if product_key == "aluminum_80_tank":
            return {
                "vip_due_days": service_offset,
                "hydro_due_days": max(service_offset, 365),
                "fill_status": "full" if service_offset >= 0 else "inspection_required",
            }
        if product_key == "regulator_set":
            return {"regulator_service_due_days": service_offset}
        return {"service_due_days": service_offset}

    def _seed_fee_rules(self):
        fee_rules = [
            ("fee_rule_deposit", "Standard Rental Deposit", "deposit", 200.0, "rental_deposit", 10),
            ("fee_rule_late", "Late Return Fee", "late", 35.0, "late_return_fee", 20),
            ("fee_rule_damage", "Damage Fee", "damage", 75.0, "damage_fee", 30),
            ("fee_rule_tank_fill", "Tank Fill Fee", "adjustment", 12.0, "tank_fill_fee", 40),
        ]
        for key, name, fee_type, amount, product_key, sequence in fee_rules:
            self.records[key] = self.registry.upsert(
                "adventure.rental.fee.rule",
                key,
                {
                    "sequence": sequence,
                    "name": name,
                    "fee_type": fee_type,
                    "amount": amount,
                    "product_id": self.records["product_%s" % product_key].product_variant_id.id,
                    "payload": {"vertical": "scuba"},
                },
            )

    def _seed_reservations(self):
        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        reservation_specs = [
            (
                "reservation_future_reserved",
                "DR-1001",
                "customer_certified_current",
                now + timedelta(days=2, hours=9),
                now + timedelta(days=4, hours=17),
                "reserved",
                200.0,
                [("line_future_full_kit", "full_scuba_kit", "package_full_scuba_kit", False, "ready", 1, 89.0, "M")],
            ),
            (
                "reservation_pickup_today",
                "DR-1002",
                "customer_certified_expired_waiver",
                now + timedelta(hours=2),
                now + timedelta(days=1, hours=17),
                "assigned",
                200.0,
                [("line_pickup_bcd", "bcd", "package_bcd_regulator", "asset_bcd_m_001", "ready", 1, 28.0, "M")],
            ),
            (
                "reservation_checked_out_due_today",
                "DR-1003",
                "customer_nitrox",
                now - timedelta(days=1, hours=3),
                now + timedelta(hours=4),
                "checked_out",
                200.0,
                [
                    ("line_checked_out_reg", "regulator_set", "package_full_scuba_kit", "asset_reg_003", "checked_out", 1, 34.0, False),
                    ("line_checked_out_tank", "aluminum_80_tank", "package_full_scuba_kit", "asset_tank_al80_002", "checked_out", 1, 18.0, False),
                ],
            ),
            (
                "reservation_overdue",
                "DR-1004",
                "customer_uncertified",
                now - timedelta(days=3),
                now - timedelta(days=1),
                "checked_out",
                200.0,
                [("line_overdue_bcd", "bcd", "package_bcd_regulator", "asset_bcd_l_001", "checked_out", 1, 28.0, "L")],
            ),
            (
                "reservation_returned_damaged",
                "DR-1005",
                "customer_group",
                now - timedelta(days=6),
                now - timedelta(days=4),
                "returned",
                200.0,
                [("line_returned_damaged_bcd", "bcd", "package_bcd_regulator", "asset_bcd_xl_001", "damaged", 1, 28.0, "XL")],
            ),
        ]
        for key, name, customer_key, pickup, returns, state, deposit, lines in reservation_specs:
            reservation = self.registry.upsert(
                "adventure.rental.reservation",
                key,
                {
                    "name": name,
                    "partner_id": self.records[customer_key].id,
                    "pickup_datetime": pickup,
                    "return_datetime": returns,
                    "state": state,
                    "deposit_amount": deposit,
                    "fee_amount": 0.0,
                    "requirement_payload": {"vertical": "scuba", "seed_scenario": key},
                },
            )
            self.records[key] = reservation
            for line_key, product_key, package_key, asset_key, condition, quantity, price, size in lines:
                line = self.registry.upsert(
                    "adventure.rental.line",
                    line_key,
                    {
                        "reservation_id": reservation.id,
                        "product_id": self.records["product_%s" % product_key].product_variant_id.id,
                        "package_template_id": self.records[package_key].id,
                        "asset_id": self.records[asset_key].id if asset_key else False,
                        "quantity": quantity,
                        "price_unit": price,
                        "size_code": size or False,
                        "condition_state": condition,
                        "requirement_payload": {"vertical": "scuba", "seed_scenario": line_key},
                    },
                )
                self.records[line_key] = line
                if asset_key:
                    self.records[asset_key].write({"current_reservation_line_id": line.id})

    def _seed_condition_and_maintenance(self):
        condition_specs = [
            ("condition_checkout_reg_003", "reservation_checked_out_due_today", "line_checked_out_reg", "asset_reg_003", "checkout", "good", "Regulator breathed normally during checkout."),
            ("condition_checkout_tank_002", "reservation_checked_out_due_today", "line_checked_out_tank", "asset_tank_al80_002", "checkout", "good", "Tank issued full at 3000 PSI."),
            ("condition_checkin_bcd_xl_001", "reservation_returned_damaged", "line_returned_damaged_bcd", "asset_bcd_xl_001", "checkin", "damaged", "Inflator button sticking; routed to repair bench."),
        ]
        for key, reservation_key, line_key, asset_key, event_type, condition, notes in condition_specs:
            self.registry.upsert(
                "adventure.rental.condition.log",
                key,
                {
                    "reservation_id": self.records[reservation_key].id,
                    "line_id": self.records[line_key].id,
                    "asset_id": self.records[asset_key].id,
                    "event_type": event_type,
                    "condition_state": condition,
                    "notes": notes,
                    "payload": {"vertical": "scuba"},
                },
            )
        maintenance_specs = [
            ("maintenance_reg_002_service", "asset_reg_002", "service", "open", "Annual regulator service is overdue.", 365),
            ("maintenance_bcd_xl_001_repair", "asset_bcd_xl_001", "repair", "open", "Repair sticky inflator button before next rental.", 30),
            ("maintenance_tank_003_inspection", "asset_tank_al80_003", "inspection", "open", "VIP expired; hold until inspection is complete.", 365),
            ("maintenance_computer_002_retired", "asset_computer_002", "retirement", "done", "Screen failure; retired from rental fleet.", 0),
        ]
        for key, asset_key, event_type, state, notes, next_service_offset in maintenance_specs:
            self.registry.upsert(
                "adventure.rental.maintenance.event",
                key,
                {
                    "asset_id": self.records[asset_key].id,
                    "event_type": event_type,
                    "state": state,
                    "notes": notes,
                    "next_service_date": self.registry.today() + timedelta(days=next_service_offset),
                    "payload": {"vertical": "scuba"},
                },
            )

    def _counts(self):
        return {
            "products": len(
                [
                    key
                    for key in self.records
                    if key.startswith("product_") and not key.startswith("product_category_")
                ]
            ),
            "customers": len([key for key in self.records if key.startswith("customer_")]),
            "packages": len([key for key in self.records if key.startswith("package_")]),
            "assets": len([key for key in self.records if key.startswith("asset_")]),
            "reservations": len([key for key in self.records if key.startswith("reservation_")]),
        }


def seed(env, reset=False):
    return ScubaShopSeed(env, reset=reset).run()
