from odoo import fields, models


class AppointmentType(models.Model):
    _inherit = "appointment.type"

    dgc_area_ids = fields.One2many(
        "dgc.appointment.area",
        "appointment_type_id",
        string="Áreas DGC",
    )
