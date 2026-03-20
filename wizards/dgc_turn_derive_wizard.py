from odoo import api, fields, models
from odoo.exceptions import UserError


class DgcTurnDeriveWizard(models.TransientModel):
    _name = "dgc.turn.derive.wizard"
    _description = "Asistente de derivación de turno"

    turn_id = fields.Many2one(
        "dgc.appointment.turn",
        string="Turno",
        required=True,
    )

    # Related fields for source turn display
    source_turn_number = fields.Char(
        related="turn_id.turn_number", string="Nro. Turno", readonly=True,
    )
    source_citizen_dni = fields.Char(
        related="turn_id.citizen_dni", string="DNI", readonly=True,
    )
    source_citizen_name = fields.Char(
        related="turn_id.citizen_name", string="Ciudadano", readonly=True,
    )
    source_area_id = fields.Many2one(
        related="turn_id.area_id", string="Área Actual", readonly=True,
    )

    to_area_id = fields.Many2one(
        "appointment.type",
        string="Área destino",
        required=True,
        domain="[('is_dgc_area', '=', True), ('active', '=', True), ('id', '!=', source_area_id)]",
    )
    reason = fields.Text(string="Motivo", required=True)

    def action_derive(self):
        self.ensure_one()
        turn = self.turn_id
        if not turn:
            raise UserError("No se encontró el turno a derivar.")
        if self.to_area_id == turn.area_id:
            raise UserError("El área destino debe ser diferente al área actual del turno.")

        # 1. Create new turn in destination area (inherits citizen data)
        new_turn = self.env["dgc.appointment.turn"].sudo().create({
            "citizen_dni": turn.citizen_dni,
            "citizen_name": turn.citizen_name,
            "citizen_email": turn.citizen_email,
            "notes": turn.notes,
            "partner_id": turn.partner_id.id,
            "area_id": self.to_area_id.id,
            "source": turn.source,
            "date": turn.date,
        })

        # 2. Record derivation linking original → new
        self.env["dgc.appointment.derivation"].sudo().create({
            "turn_id": turn.id,
            "new_turn_id": new_turn.id,
            "from_area_id": turn.area_id.id,
            "to_area_id": self.to_area_id.id,
            "reason": self.reason,
            "user_id": self.env.uid,
        })

        # 3. Mark original as derived (single write)
        turn.write({"state": "derived"})

        # 4. Notify destination area
        new_turn._send_bus_notification("derived")

        return {"type": "ir.actions.act_window_close"}

    @api.onchange("to_area_id")
    def _onchange_to_area_id(self):
        if self.to_area_id and self.turn_id and self.to_area_id == self.turn_id.area_id:
            return {"warning": {
                "title": "Área inválida",
                "message": "El área destino no puede ser la misma que el área actual del turno.",
            }}
