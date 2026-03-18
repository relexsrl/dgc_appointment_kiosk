from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    dgc_area_ids = fields.Many2many(
        "dgc.appointment.area",
        "dgc_area_user_rel",
        "user_id",
        "area_id",
        string="Áreas DGC asignadas",
    )
