import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class DgcAppointmentArea(models.Model):
    _name = "dgc.appointment.area"
    _description = "Área de Atención DGC"
    _order = "sequence, name"

    name = fields.Char(required=True, string="Nombre")
    code = fields.Char(required=True, size=10, string="Código")
    location = fields.Char(string="Ubicación")
    color = fields.Integer(string="Color")
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    avg_service_time = fields.Integer(
        string="Tiempo promedio de atención (min)",
        default=15,
    )
    max_counters = fields.Integer(
        string="Cantidad de puestos",
        default=1,
    )
    welcome_message = fields.Text(string="Mensaje de bienvenida")

    user_ids = fields.Many2many(
        "res.users",
        "dgc_area_user_rel",
        "area_id",
        "user_id",
        string="Operadores",
    )
    turn_ids = fields.One2many(
        "dgc.appointment.turn",
        "area_id",
        string="Turnos",
    )
    appointment_type_id = fields.Many2one(
        "appointment.type",
        string="Tipo de Cita",
        ondelete="set null",
        help="Tipo de cita de Odoo Appointment vinculado. Permite reserva por portal web y define horarios por día.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
    )

    pending_turn_count = fields.Integer(
        string="Turnos pendientes",
        compute="_compute_pending_turn_count",
    )
    max_daily_turns = fields.Integer(
        string="Máximo de turnos diarios",
        compute="_compute_max_daily_turns",
    )
    remaining_turns_today = fields.Integer(
        string="Turnos restantes hoy",
        compute="_compute_remaining_turns_today",
    )

    _unique_code = models.Constraint(
        "UNIQUE(code)",
        "El código de área debe ser único.",
    )

    @api.depends("turn_ids.state")
    def _compute_pending_turn_count(self):
        today = fields.Date.context_today(self)
        for area in self:
            area.pending_turn_count = self.env["dgc.appointment.turn"].search_count(
                [
                    ("area_id", "=", area.id),
                    ("date", "=", today),
                    ("state", "in", ("new", "waiting", "calling")),
                ]
            )

    def _get_today_schedule(self):
        """Return (start_hour, end_hour) for today.

        If the area has a linked appointment.type with slots for today's
        weekday, derive the schedule from the earliest start and latest end
        among those slots. Otherwise fall back to the global config params
        ``dgc_appointment_kiosk.hour_start`` / ``hour_end``.
        """
        self.ensure_one()
        if self.appointment_type_id and self.appointment_type_id.slot_ids:
            # Python weekday: 0=Monday..6=Sunday  →  appointment.slot weekday: '1'=Monday..'7'=Sunday
            today_weekday = str(fields.Date.context_today(self).weekday() + 1)
            today_slots = self.appointment_type_id.slot_ids.filtered(lambda s: s.weekday == today_weekday)
            if today_slots:
                start = min(today_slots.mapped("start_hour"))
                end = max(today_slots.mapped("end_hour"))
                return (start, end)

        # Fallback: global config parameters
        icp = self.env["ir.config_parameter"].sudo()
        hour_start = float(icp.get_param("dgc_appointment_kiosk.hour_start", "8.0"))
        hour_end = float(icp.get_param("dgc_appointment_kiosk.hour_end", "14.0"))
        return (hour_start, hour_end)

    def _compute_max_daily_turns(self):
        icp = self.env["ir.config_parameter"].sudo()
        fallback_start = float(icp.get_param("dgc_appointment_kiosk.hour_start", "8.0"))
        fallback_end = float(icp.get_param("dgc_appointment_kiosk.hour_end", "14.0"))

        for area in self:
            if area.avg_service_time <= 0:
                area.max_daily_turns = 0
                continue

            if area.appointment_type_id and area.appointment_type_id.slot_ids:
                # Slot-based capacity: sum minutes from today's slots
                today_weekday = str(fields.Date.context_today(self).weekday() + 1)
                today_slots = area.appointment_type_id.slot_ids.filtered(lambda s, wd=today_weekday: s.weekday == wd)
                if today_slots:
                    total_minutes = sum((s.end_hour - s.start_hour) * 60 for s in today_slots)
                    area.max_daily_turns = int(total_minutes / area.avg_service_time * area.max_counters)
                    continue

            # Fallback: global config hours
            minutes = (fallback_end - fallback_start) * 60
            area.max_daily_turns = int(minutes / area.avg_service_time * area.max_counters)

    def _compute_remaining_turns_today(self):
        today = fields.Date.context_today(self)
        for area in self:
            used = self.env["dgc.appointment.turn"].search_count(
                [
                    ("area_id", "=", area.id),
                    ("date", "=", today),
                    ("state", "!=", "no_show"),
                ]
            )
            area.remaining_turns_today = max(area.max_daily_turns - used, 0)

    # ---- Phase 3: Staff user sync ----

    def write(self, vals):
        res = super().write(vals)
        if "user_ids" in vals:
            for area in self.filtered("appointment_type_id"):
                area.appointment_type_id.staff_user_ids = area.user_ids
        return res

    # ---- Phase 5: Auto-create appointment.type ----

    def action_create_appointment_type(self):
        """Create an appointment.type linked to this area with default slots Mon-Fri."""
        self.ensure_one()
        icp = self.env["ir.config_parameter"].sudo()
        hour_start = float(icp.get_param("dgc_appointment_kiosk.hour_start", "8.0"))
        hour_end = float(icp.get_param("dgc_appointment_kiosk.hour_end", "14.0"))

        tz = (
            self.company_id.resource_calendar_id.tz
            or self.env.company.resource_calendar_id.tz
            or "America/Argentina/Buenos_Aires"
        )

        # Build slot records for Monday (1) through Friday (5)
        slot_vals = []
        for weekday in ("1", "2", "3", "4", "5"):
            slot_vals.append(
                (
                    0,
                    0,
                    {
                        "weekday": weekday,
                        "start_hour": hour_start,
                        "end_hour": hour_end,
                    },
                )
            )

        appointment_type = self.env["appointment.type"].create(
            {
                "name": self.name,
                "appointment_duration": self.avg_service_time / 60.0,
                "category": "recurring",
                "staff_user_ids": [(6, 0, self.user_ids.ids)],
                "appointment_tz": tz,
                "is_published": True,
                "slot_ids": slot_vals,
            }
        )

        self.appointment_type_id = appointment_type

        return {
            "type": "ir.actions.act_window",
            "res_model": "appointment.type",
            "res_id": appointment_type.id,
            "view_mode": "form",
            "target": "current",
            "name": _("Tipo de Cita"),
        }

    def action_view_appointment_type(self):
        """Open the linked appointment.type in form view."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "appointment.type",
            "res_id": self.appointment_type_id.id,
            "view_mode": "form",
            "target": "current",
            "name": _("Tipo de Cita"),
        }
