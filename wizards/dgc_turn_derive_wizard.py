from odoo import fields, models
from odoo.exceptions import UserError


class DgcTurnDeriveWizard(models.TransientModel):
    _name = "dgc.turn.derive.wizard"
    _description = "Asistente de derivación de turno"

    turn_id = fields.Many2one(
        "dgc.appointment.turn",
        string="Turno",
        required=True,
    )
    to_area_id = fields.Many2one(
        "appointment.type",
        string="Área destino",
        required=True,
        domain=[("is_dgc_area", "=", True), ("active", "=", True)],
    )
    reason = fields.Text(string="Motivo", required=True)

    def action_derive(self):
        self.ensure_one()
        turn = self.turn_id
        if not turn:
            raise UserError("No se encontró el turno a derivar.")
        from_area = turn.area_id

        self.env["dgc.appointment.derivation"].create({
            "turn_id": turn.id,
            "from_area_id": from_area.id,
            "to_area_id": self.to_area_id.id,
            "reason": self.reason,
            "user_id": self.env.uid,
        })

        turn.write({
            "state": "derived",
        })

        # Create new turn in destination area
        turn.write({
            "area_id": self.to_area_id.id,
            "state": "waiting",
        })

        # Notify destination area
        channel = f"dgc_turn_area_{self.to_area_id.id}"
        self.env["bus.bus"]._sendone(channel, "dgc_turn_update", {
            "action": "derived",
            "turn_id": turn.id,
            "turn_number": turn.turn_number,
            "citizen_name": turn.citizen_name or "",
            "area_id": self.to_area_id.id,
            "area_name": self.to_area_id.name,
            "state": "waiting",
            "from_area": from_area.name,
        })

        return {"type": "ir.actions.act_window_close"}
