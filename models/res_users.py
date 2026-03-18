from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    dgc_area_ids = fields.Many2many(
        "appointment.type",
        "dgc_appointment_type_user_rel",
        "user_id",
        "area_id",
        string="Áreas DGC asignadas",
        domain="[('is_dgc_area', '=', True)]",
    )
