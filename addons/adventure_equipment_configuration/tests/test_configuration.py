# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestEquipmentConfiguration(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Config = cls.env["adventure.equipment.configuration"]
        cls.Line = cls.env["adventure.equipment.configuration.line"]
        cls.Asset = cls.env["adventure.equipment.asset"]
        cls.partner = cls.env["res.partner"].create({"name": "Config Test Customer"})
        cls.other = cls.env["res.partner"].create({"name": "Other Customer"})
        cls.category = cls.env.ref("adventure_equipment.equipment_category_regulator")
        cls.asset = cls.Asset.create(
            {
                "partner_id": cls.partner.id,
                "category_id": cls.category.id,
                "nickname": "Primary Reg",
                "brand_name": "TestBrand",
                "model_name": "ModelX",
                "lifecycle_state": "active",
                "acquisition_source": "manual_shop",
            }
        )
        cls.other_asset = cls.Asset.create(
            {
                "partner_id": cls.other.id,
                "category_id": cls.category.id,
                "nickname": "Other Reg",
                "lifecycle_state": "active",
                "acquisition_source": "manual_shop",
            }
        )

    def test_create_packing_and_configuration(self):
        packing = self.Config.create(
            {
                "name": "Quarry packing",
                "partner_id": self.partner.id,
                "list_kind": "packing",
            }
        )
        config = self.Config.create(
            {
                "name": "Cold water",
                "partner_id": self.partner.id,
                "list_kind": "configuration",
            }
        )
        self.assertEqual(packing.list_kind, "packing")
        self.assertEqual(config.list_kind, "configuration")
        self.assertFalse(packing.has_broken_references)

    def test_list_kind_immutable_after_lines(self):
        packing = self.Config.create(
            {
                "name": "Kind lock",
                "partner_id": self.partner.id,
                "list_kind": "packing",
            }
        )
        packing.write({"list_kind": "configuration"})
        self.Line.create(
            {
                "configuration_id": packing.id,
                "line_type": "text",
                "name": "Spare mask",
            }
        )
        with self.assertRaises(ValidationError):
            packing.write({"list_kind": "packing"})

    def test_asset_must_belong_to_owner(self):
        config = self.Config.create(
            {
                "name": "Owner check",
                "partner_id": self.partner.id,
                "list_kind": "configuration",
            }
        )
        with self.assertRaises(ValidationError):
            self.Line.create(
                {
                    "configuration_id": config.id,
                    "line_type": "asset",
                    "asset_id": self.other_asset.id,
                }
            )

    def test_quantity_line_and_snapshot(self):
        config = self.Config.create(
            {
                "name": "With weight",
                "partner_id": self.partner.id,
                "list_kind": "configuration",
            }
        )
        weight = self.Line.create(
            {
                "configuration_id": config.id,
                "line_type": "quantity",
                "name": "Lead weight",
                "quantity": 12.0,
                "quantity_uom_label": "lb",
            }
        )
        asset_line = self.Line.create(
            {
                "configuration_id": config.id,
                "line_type": "asset",
                "asset_id": self.asset.id,
            }
        )
        self.assertEqual(weight.reference_state, "ok")
        self.assertEqual(asset_line.reference_state, "ok")
        self.assertTrue(asset_line.asset_snapshot_name)
        self.assertIn("Primary", asset_line.asset_snapshot_name)

    def test_retire_and_archive_leave_broken_reference(self):
        config = self.Config.create(
            {
                "name": "Broken refs",
                "partner_id": self.partner.id,
                "list_kind": "configuration",
            }
        )
        line = self.Line.create(
            {
                "configuration_id": config.id,
                "line_type": "asset",
                "asset_id": self.asset.id,
            }
        )
        self.asset.action_retire()
        line.invalidate_recordset()
        config.invalidate_recordset()
        self.assertEqual(line.reference_state, "unavailable")
        self.assertTrue(config.has_broken_references)

        self.asset.action_activate()
        line.invalidate_recordset()
        self.assertEqual(line.reference_state, "ok")

        self.asset.active = False
        line.invalidate_recordset()
        config.invalidate_recordset()
        self.assertEqual(line.reference_state, "archived")
        self.assertTrue(config.has_broken_references)

    def test_asset_unlink_keeps_line_with_missing_state(self):
        asset = self.Asset.create(
            {
                "partner_id": self.partner.id,
                "category_id": self.category.id,
                "nickname": "Disposable",
                "lifecycle_state": "draft",
                "acquisition_source": "manual_shop",
            }
        )
        config = self.Config.create(
            {
                "name": "Unlink case",
                "partner_id": self.partner.id,
                "list_kind": "packing",
            }
        )
        line = self.Line.create(
            {
                "configuration_id": config.id,
                "line_type": "asset",
                "asset_id": asset.id,
            }
        )
        snapshot = line.asset_snapshot_name
        # Managers can unlink; use sudo in test like manager.
        asset.sudo().unlink()
        line.invalidate_recordset()
        config.invalidate_recordset()
        self.assertFalse(line.asset_id)
        self.assertEqual(line.asset_snapshot_name, snapshot)
        self.assertEqual(line.reference_state, "missing")
        self.assertTrue(config.has_broken_references)
        self.assertEqual(len(config.line_ids), 1)

    def test_move_up_down(self):
        config = self.Config.create(
            {
                "name": "Reorder",
                "partner_id": self.partner.id,
                "list_kind": "packing",
            }
        )
        # Tied sequences (old portal default) must still move exactly one spot.
        a = self.Line.create(
            {
                "configuration_id": config.id,
                "line_type": "text",
                "name": "A",
                "sequence": 10,
            }
        )
        b = self.Line.create(
            {
                "configuration_id": config.id,
                "line_type": "text",
                "name": "B",
                "sequence": 10,
            }
        )
        c = self.Line.create(
            {
                "configuration_id": config.id,
                "line_type": "text",
                "name": "C",
                "sequence": 10,
            }
        )
        self.assertEqual(
            config.line_ids.sorted(lambda l: (l.sequence, l.id)).mapped("name"),
            ["A", "B", "C"],
        )

        b.action_move_up()
        self.assertEqual(
            config.line_ids.sorted(lambda l: (l.sequence, l.id)).mapped("name"),
            ["B", "A", "C"],
        )

        # After a partial resequence, moving C up must swap with A only (one spot),
        # not jump to B via "nearest lower sequence".
        c.action_move_up()
        self.assertEqual(
            config.line_ids.sorted(lambda l: (l.sequence, l.id)).mapped("name"),
            ["B", "C", "A"],
        )

        c.action_move_down()
        self.assertEqual(
            config.line_ids.sorted(lambda l: (l.sequence, l.id)).mapped("name"),
            ["B", "A", "C"],
        )

        # Ends are no-ops beyond the edge.
        b.action_move_up()
        self.assertEqual(
            config.line_ids.sorted(lambda l: (l.sequence, l.id)).mapped("name"),
            ["B", "A", "C"],
        )
        c.action_move_down()
        self.assertEqual(
            config.line_ids.sorted(lambda l: (l.sequence, l.id)).mapped("name"),
            ["B", "A", "C"],
        )

    def test_create_assigns_increasing_sequence(self):
        config = self.Config.create(
            {
                "name": "Seq create",
                "partner_id": self.partner.id,
                "list_kind": "packing",
            }
        )
        a = self.Line.create(
            {"configuration_id": config.id, "line_type": "text", "name": "A"}
        )
        b = self.Line.create(
            {"configuration_id": config.id, "line_type": "text", "name": "B"}
        )
        c = self.Line.create(
            {"configuration_id": config.id, "line_type": "text", "name": "C"}
        )
        self.assertLess(a.sequence, b.sequence)
        self.assertLess(b.sequence, c.sequence)
        self.assertEqual(
            config.line_ids.sorted(lambda l: (l.sequence, l.id)).mapped("name"),
            ["A", "B", "C"],
        )

    def test_hard_delete_list(self):
        config = self.Config.create(
            {
                "name": "Delete me",
                "partner_id": self.partner.id,
                "list_kind": "packing",
            }
        )
        self.Line.create(
            {"configuration_id": config.id, "line_type": "text", "name": "Item"}
        )
        config_id = config.id
        config.unlink()
        self.assertFalse(self.Config.browse(config_id).exists())
        self.assertFalse(self.Line.search([("configuration_id", "=", config_id)]))
