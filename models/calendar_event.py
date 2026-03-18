from odoo import api, fields, models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    dgc_turn_id = fields.Many2one(
        "dgc.appointment.turn",
        string="Turno DGC",
        copy=False,
    )
