from odoo import fields, models


class DgcNonWorkingDate(models.Model):
    _name = "dgc.non_working.date"
    _description = "Fecha no laborable"
    _order = "date"

    date = fields.Date(required=True)
    area_id = fields.Many2one(
        "appointment.type",
        string="Area",
        required=True,
        ondelete="cascade",
        domain="[('is_dgc_area', '=', True)]",
    )
    name = fields.Char("Descripcion")

    _unique_date_area = models.Constraint(
        "UNIQUE(date, area_id)",
        "Ya existe una fecha no laborable para esta area en esa fecha.",
    )
