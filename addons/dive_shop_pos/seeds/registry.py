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
            # Only write when a value actually changed. Skipping no-op writes keeps
            # re-seeding idempotent against records Odoo refuses to modify while in
            # use (e.g. pos.payment.method with an open PoS session).
            if self._values_differ(record, values):
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

    def _values_differ(self, record, values):
        """Return True when writing ``values`` would change ``record``.

        Conservative by design: any value we cannot confidently compare is
        treated as a change so behaviour matches an unconditional ``write``.
        """
        for key, value in values.items():
            try:
                field = record._fields[key]
                current = record[key]
            except Exception:
                return True
            try:
                if field.type == "many2one":
                    current_id = current.id or False
                    desired_id = value.id if hasattr(value, "id") else (value or False)
                    if current_id != desired_id:
                        return True
                elif field.type in ("many2many", "one2many"):
                    desired_ids = self._command_ids(value)
                    if desired_ids is None:
                        return True
                    if sorted(current.ids) != sorted(desired_ids):
                        return True
                elif current != value:
                    return True
            except Exception:
                return True
        return False

    @staticmethod
    def _command_ids(value):
        """Extract the id list from a ``[(6, 0, [ids])]`` command, else None."""
        if not isinstance(value, (list, tuple)):
            return None
        ids = None
        for command in value:
            if (
                isinstance(command, (list, tuple))
                and len(command) == 3
                and command[0] == 6
            ):
                ids = list(command[2])
            else:
                return None
        return ids
