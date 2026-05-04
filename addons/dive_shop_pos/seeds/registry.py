# -*- coding: utf-8 -*-

from odoo import fields


class SeedRegistry:
    """Small idempotent seed helper keyed by stable XML IDs."""

    def __init__(self, env, module):
        self.env = env
        self.module = module
        self.imd = env["ir.model.data"].sudo()
        self.created = []
        self.updated = []

    def ref(self, name):
        record = self.env.ref("%s.%s" % (self.module, name), raise_if_not_found=False)
        return record.sudo() if record else record

    def upsert(self, model_name, xml_name, values):
        model = self.env[model_name].sudo()
        values = self._filter_values(model, values)
        record = self.ref(xml_name)
        if record and record.exists():
            record.write(values)
            self.updated.append((model_name, xml_name))
            return record

        record = model.create(values)
        self.imd.create(
            {
                "module": self.module,
                "name": xml_name,
                "model": model_name,
                "res_id": record.id,
                "noupdate": True,
            }
        )
        self.created.append((model_name, xml_name))
        return record

    def reset(self):
        model_order = [
            "adventure.rental.condition.log",
            "adventure.rental.maintenance.event",
            "adventure.rental.line",
            "adventure.rental.reservation",
            "adventure.rental.asset",
            "adventure.rental.fee.rule",
            "adventure.rental.package.template",
            "stock.lot",
        ]
        deleted = 0
        for model_name in model_order:
            xml_records = self.imd.search([("module", "=", self.module), ("model", "=", model_name)])
            for xml_record in xml_records:
                record = self.env[model_name].sudo().browse(xml_record.res_id)
                if record.exists():
                    record.unlink()
                    deleted += 1
                if xml_record.exists():
                    xml_record.unlink()
        return deleted

    def summary(self):
        return {
            "created": len(self.created),
            "updated": len(self.updated),
        }

    def today(self):
        return fields.Date.context_today(self.env.user)

    def _filter_values(self, model, values):
        return {key: value for key, value in values.items() if key in model._fields}
