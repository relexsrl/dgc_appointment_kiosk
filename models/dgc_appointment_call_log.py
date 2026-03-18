from odoo import fields, models


class DgcAppointmentCallLog(models.Model):
    _name = "dgc.appointment.call.log"
    _description = "Log de llamadas de turno"
    _order = "call_datetime desc"

    turn_id = fields.Many2one(
        "dgc.appointment.turn",
        string="Turno",
        required=True,
        ondelete="cascade",
    )
    call_datetime = fields.Datetime(
        string="Fecha/Hora",
        default=fields.Datetime.now,
        required=True,
    )
    operator_id = fields.Many2one(
        "res.users",
        string="Operador",
        required=True,
    )
    call_number = fields.Integer(string="Llamada N°")
