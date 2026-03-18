from odoo import fields, models


class DgcAppointmentDerivation(models.Model):
    _name = "dgc.appointment.derivation"
    _description = "Derivación de turno"
    _order = "derivation_date desc"

    turn_id = fields.Many2one(
        "dgc.appointment.turn",
        string="Turno",
        required=True,
        ondelete="cascade",
    )
    from_area_id = fields.Many2one(
        "dgc.appointment.area",
        string="Área origen",
        required=True,
    )
    to_area_id = fields.Many2one(
        "dgc.appointment.area",
        string="Área destino",
        required=True,
    )
    reason = fields.Text(string="Motivo", required=True)
    user_id = fields.Many2one(
        "res.users",
        string="Derivado por",
        default=lambda self: self.env.uid,
        required=True,
    )
    derivation_date = fields.Datetime(
        string="Fecha de derivación",
        default=fields.Datetime.now,
        required=True,
    )
