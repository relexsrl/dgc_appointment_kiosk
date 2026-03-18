from odoo import api, fields, models


class AppointmentType(models.Model):
    _inherit = "appointment.type"

    # --- DGC-specific fields ---
    is_dgc_area = fields.Boolean("Es Área DGC", default=False)
    dgc_code = fields.Char("Código", size=10)
    dgc_location = fields.Char("Ubicación")
    dgc_color = fields.Integer("Color")
    dgc_avg_service_time = fields.Integer(
        "Tiempo promedio de atención (min)",
        default=15,
    )
    dgc_max_counters = fields.Integer(
        "Cantidad de puestos",
        default=1,
    )
    dgc_welcome_message = fields.Text("Mensaje de bienvenida")
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
    )

    # --- Relations ---
    turn_ids = fields.One2many(
        "dgc.appointment.turn",
        "area_id",
        string="Turnos",
    )

    # --- Computed ---
    pending_turn_count = fields.Integer(
        "Turnos pendientes",
        compute="_compute_pending_turn_count",
    )
    max_daily_turns = fields.Integer(
        "Máximo de turnos diarios",
        compute="_compute_max_daily_turns",
    )
    remaining_turns_today = fields.Integer(
        "Turnos restantes hoy",
        compute="_compute_remaining_turns_today",
    )

    # --- Constraints ---
    _dgc_unique_code = models.Constraint(
        "UNIQUE(dgc_code)",
        "El código de área debe ser único.",
    )

    # --- Computed methods ---

    @api.depends("turn_ids.state")
    def _compute_pending_turn_count(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if not rec.is_dgc_area:
                rec.pending_turn_count = 0
                continue
            rec.pending_turn_count = self.env["dgc.appointment.turn"].search_count([
                ("area_id", "=", rec.id),
                ("date", "=", today),
                ("state", "in", ("new", "waiting", "calling")),
            ])

    def _compute_max_daily_turns(self):
        icp = self.env["ir.config_parameter"].sudo()
        fallback_start = float(icp.get_param("dgc_appointment_kiosk.hour_start", "8.0"))
        fallback_end = float(icp.get_param("dgc_appointment_kiosk.hour_end", "14.0"))

        for rec in self:
            if not rec.is_dgc_area or rec.dgc_avg_service_time <= 0:
                rec.max_daily_turns = 0
                continue

            # Use own slot_ids (we ARE the appointment.type now)
            if rec.slot_ids:
                today_weekday = str(fields.Date.context_today(self).weekday() + 1)
                today_slots = rec.slot_ids.filtered(lambda s, wd=today_weekday: s.weekday == wd)
                if today_slots:
                    total_minutes = sum((s.end_hour - s.start_hour) * 60 for s in today_slots)
                    rec.max_daily_turns = int(
                        total_minutes / rec.dgc_avg_service_time * rec.dgc_max_counters
                    )
                    continue

            # Fallback: global config hours
            minutes = (fallback_end - fallback_start) * 60
            rec.max_daily_turns = int(minutes / rec.dgc_avg_service_time * rec.dgc_max_counters)

    def _compute_remaining_turns_today(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if not rec.is_dgc_area:
                rec.remaining_turns_today = 0
                continue
            used = self.env["dgc.appointment.turn"].search_count([
                ("area_id", "=", rec.id),
                ("date", "=", today),
                ("state", "!=", "no_show"),
            ])
            rec.remaining_turns_today = max(rec.max_daily_turns - used, 0)

    def _get_today_schedule(self):
        """Return (start_hour, end_hour) for today from slots or fallback."""
        self.ensure_one()
        if self.slot_ids:
            today_weekday = str(fields.Date.context_today(self).weekday() + 1)
            today_slots = self.slot_ids.filtered(lambda s: s.weekday == today_weekday)
            if today_slots:
                return (
                    min(today_slots.mapped("start_hour")),
                    max(today_slots.mapped("end_hour")),
                )
        icp = self.env["ir.config_parameter"].sudo()
        return (
            float(icp.get_param("dgc_appointment_kiosk.hour_start", "8.0")),
            float(icp.get_param("dgc_appointment_kiosk.hour_end", "14.0")),
        )
