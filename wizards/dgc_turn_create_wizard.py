from odoo import api, fields, models
from odoo.exceptions import UserError


class DgcTurnCreateWizard(models.TransientModel):
    _name = "dgc.turn.create.wizard"
    _description = "Crear turno manualmente"

    citizen_dni = fields.Char(string="DNI/CUIT", required=True)
    citizen_name = fields.Char(string="Nombre completo")
    citizen_email = fields.Char(string="Email")
    notes = fields.Text(string="Observaciones")
    area_id = fields.Many2one(
        "appointment.type",
        string="Área",
        required=True,
        domain="[('is_dgc_area', '=', True), ('active', '=', True), ('id', 'in', available_area_ids)]",
    )
    available_area_ids = fields.Many2many(
        "appointment.type",
        compute="_compute_available_area_ids",
    )

    @api.depends_context("uid")
    def _compute_available_area_ids(self):
        user_areas = self.env['appointment.type']._get_dgc_areas_for_user()
        for wizard in self:
            wizard.available_area_ids = user_areas

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        user_areas = self.env['appointment.type']._get_dgc_areas_for_user()
        if len(user_areas) == 1 and "area_id" in fields_list:
            res["area_id"] = user_areas.id
        return res

    @api.onchange("citizen_dni")
    def _onchange_citizen_dni(self):
        if not self.citizen_dni:
            return
        partner = self.env["res.partner"].sudo().search(
            [("vat", "=", self.citizen_dni)], limit=1,
        )
        if partner:
            self.citizen_name = partner.name
            self.citizen_email = partner.email or ""

    def action_create_turn(self):
        self.ensure_one()
        Turn = self.env["dgc.appointment.turn"].sudo()

        # Validate DNI
        if not Turn._validate_dni(self.citizen_dni):
            raise UserError("El DNI/CUIT ingresado no es válido.")

        # Validate area belongs to operator
        user_area_ids = self.env['appointment.type']._get_dgc_areas_for_user().ids
        if self.area_id.id not in user_area_ids:
            raise UserError("No tiene permisos para crear turnos en esta área.")

        # Check capacity (sudo to bypass appointment record rules)
        if self.area_id.sudo().remaining_turns_today <= 0:
            raise UserError("No hay más turnos disponibles para esta área hoy.")

        # Find or create partner
        partner_result = Turn._find_or_create_partner(
            self.citizen_dni, self.citizen_name, self.citizen_email,
        )

        # Create turn (sudo bypasses operator's missing create ACL)
        turn = Turn.create({
            "citizen_dni": self.citizen_dni,
            "citizen_name": self.citizen_name or "",
            "citizen_email": self.citizen_email or "",
            "notes": self.notes or "",
            "area_id": self.area_id.id,
            "partner_id": partner_result.get("partner_id"),
            "source": "manual",
        })

        return {
            "type": "ir.actions.act_window",
            "name": turn.turn_number,
            "res_model": "dgc.appointment.turn",
            "res_id": turn.id,
            "view_mode": "form",
            "target": "current",
        }
