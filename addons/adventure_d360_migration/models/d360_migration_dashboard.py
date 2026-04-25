# -*- coding: utf-8 -*-

from odoo import fields, models


class AdventureD360MigrationDashboard(models.Model):
    _name = "adventure.d360.migration.dashboard"
    _description = "D360 migration dashboard"

    name = fields.Char(required=True)

    def action_open_customer_workflow(self):
        self.ensure_one()
        return self.env.ref(
            "adventure_d360_migration.action_adventure_d360_customer_import_wizard"
        ).read()[0]

    def action_open_customer_batches(self):
        self.ensure_one()
        return self.env.ref(
            "adventure_d360_migration.action_adventure_d360_customer_import_batch"
        ).read()[0]
