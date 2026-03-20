from odoo import api, fields, models


class DgcOperatorBox(models.Model):
    _name = "dgc.operator.box"
    _description = "Box/Ventanilla de Operador"
    _order = "area_id, box_number"

    operator_id = fields.Many2one(
        "res.users",
        string="Operador",
        required=True,
        ondelete="cascade",
    )
    area_id = fields.Many2one(
        "appointment.type",
        string="Area",
        required=True,
        ondelete="cascade",
        domain="[('is_dgc_area', '=', True)]",
    )
    box_number = fields.Char(
        string="Nro. Box/Ventanilla",
        required=True,
        size=10,
    )
    active = fields.Boolean(default=True)

    _unique_operator_area = models.Constraint(
        "UNIQUE(operator_id, area_id)",
        "Ya existe un box asignado a este operador en esta area.",
    )

    @api.depends("operator_id", "box_number")
    def _compute_display_name(self):
        for rec in self:
            operator_name = rec.operator_id.name or ""
            rec.display_name = f"{operator_name} - Box {rec.box_number}"
