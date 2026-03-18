from odoo import api, fields, models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    dgc_turn_id = fields.Many2one(
        "dgc.appointment.turn",
        string="Turno DGC",
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        events = super().create(vals_list)
        events._create_dgc_turns_from_appointments()
        return events

    def _create_dgc_turns_from_appointments(self):
        """Auto-create DGC turns for calendar events linked to DGC appointment types."""
        if self.env.context.get("dgc_skip_turn_creation"):
            return

        Turn = self.env["dgc.appointment.turn"].sudo()

        for event in self:
            # Only process events whose appointment_type is a DGC area
            appt_type = event.appointment_type_id
            if not appt_type or not appt_type.is_dgc_area:
                continue

            # Use the appointment booker, fall back to first attendee partner
            booker = event.appointment_booker_id or event.partner_ids[:1]
            if not booker:
                continue

            dni = booker.vat or ""

            turn = Turn.with_context(dgc_skip_turn_creation=True).create({
                "citizen_dni": dni or f"PORTAL-{booker.id}",
                "citizen_name": booker.name or "",
                "citizen_email": booker.email or "",
                "area_id": appt_type.id,
                "partner_id": booker.id,
                "calendar_event_id": event.id,
                "source": "portal",
                "date": event.start.date() if event.start else fields.Date.context_today(self),
            })
            event.dgc_turn_id = turn.id

            turn._send_bus_notification("portal_booking")
