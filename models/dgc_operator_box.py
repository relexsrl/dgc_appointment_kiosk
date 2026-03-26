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

    def write(self, vals):
        # Track which areas had their active flag changed for bus notification
        notify_areas = self.env["appointment.type"]
        if "active" in vals:
            notify_areas = self.mapped("area_id")
        res = super().write(vals)
        if notify_areas:
            self._send_counter_changed(notify_areas)
        return res

    def _send_counter_changed(self, areas):
        """Send bus notification when counter active state changes."""
        for area in areas:
            area.invalidate_recordset(["active_box_count"])
            channel = f"dgc_turn_area_{area.id}"
            payload = {
                "action": "counter_changed",
                "area_id": area.id,
                "area_name": area.name,
                "active_box_count": area.active_box_count,
            }
            self.env["bus.bus"]._sendone(channel, "dgc_turn_update", payload)

    def action_toggle_box(self):
        """Toggle active state. Returns dict for dashboard update."""
        self.ensure_one()
        self.active = not self.active
        return {
            "box_active": self.active,
            "active_box_count": self.area_id.active_box_count,
        }
