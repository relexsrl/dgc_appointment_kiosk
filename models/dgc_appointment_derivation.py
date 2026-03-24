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
        "appointment.type",
        string="Área origen",
        required=True,
        ondelete="restrict",
    )
    to_area_id = fields.Many2one(
        "appointment.type",
        string="Área destino",
        required=True,
        ondelete="restrict",
    )
    reason = fields.Text(string="Motivo", required=True)
    user_id = fields.Many2one(
        "res.users",
        string="Derivado por",
        default=lambda self: self.env.uid,
        required=True,
        ondelete="restrict",
    )
    derivation_date = fields.Datetime(
        string="Fecha de derivación",
        default=fields.Datetime.now,
        required=True,
    )
    new_turn_id = fields.Many2one(
        "dgc.appointment.turn",
        string="Nuevo Turno",
        readonly=True,
        ondelete="set null",
    )
