from odoo import api, fields, models
from odoo.exceptions import AccessError

from .dgc_appointment_turn import _today_tz

DGC_COLOR_MAP = {
    0: '#F06050', 1: '#F4A460', 2: '#F7CD1F', 3: '#6CC1ED',
    4: '#814968', 5: '#EB7E7F', 6: '#2C8397', 7: '#475577',
    8: '#D6145F', 9: '#30C381', 10: '#9365B8', 11: '#1abc9c',
}


class AppointmentType(models.Model):
    _inherit = "appointment.type"

    # --- DGC-specific fields ---
    is_dgc_area = fields.Boolean("Es Área DGC", default=False)
    dgc_code = fields.Char("Código", size=10)
    dgc_location = fields.Char("Ubicación")
    dgc_color = fields.Integer("Color")
    dgc_max_counters = fields.Integer(
        "Cantidad de puestos",
        default=1,
    )
    dgc_welcome_message = fields.Text("Mensaje de bienvenida")
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
        ondelete="set null",
    )

    # --- Relations ---
    turn_ids = fields.One2many(
        "dgc.appointment.turn",
        "area_id",
        string="Turnos",
    )
    operator_box_ids = fields.One2many(
        "dgc.operator.box",
        "area_id",
        string="Boxes/Ventanillas",
    )
    non_working_date_ids = fields.One2many(
        "dgc.non_working.date",
        "area_id",
        string="Fechas no laborables",
    )

    # --- Computed ---
    active_box_count = fields.Integer(
        "Ventanillas activas",
        compute="_compute_active_box_count",
    )
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

    def _get_capacity_params(self):
        """Return shared capacity parameters for a single DGC area record.

        Returns a dict with:
        - ``service_minutes``: service time in minutes (float)
        - ``counters``: effective number of parallel counters (int)
        - ``available``: whether the area is open today (bool)
        - ``fallback_start``: ICP fallback start hour (float)
        - ``fallback_end``: ICP fallback end hour (float)

        If the area cannot serve turns (not DGC, no service time,
        no active boxes, or non-working day), ``available`` is False
        and ``counters`` is 0.
        """
        self.ensure_one()
        icp = self.env["ir.config_parameter"].sudo()
        fallback_start = float(icp.get_param("dgc_appointment_kiosk.hour_start", "8.0"))
        fallback_end = float(icp.get_param("dgc_appointment_kiosk.hour_end", "14.0"))

        service_minutes = self.appointment_duration * 60 if self.appointment_duration > 0 else 0
        result = {
            "service_minutes": service_minutes,
            "counters": 0,
            "available": False,
            "fallback_start": fallback_start,
            "fallback_end": fallback_end,
        }

        if not self.is_dgc_area or service_minutes <= 0:
            return result
        if self.active_box_count <= 0:
            return result

        counters = (
            min(self.active_box_count, self.dgc_max_counters)
            if self.dgc_max_counters
            else self.active_box_count
        )
        result["counters"] = counters

        if not self._is_available_today():
            return result

        result["available"] = True
        return result

    def _get_service_time_minutes(self):
        """Return service time in minutes from appointment_duration (hours)."""
        self.ensure_one()
        return self.appointment_duration * 60 if self.appointment_duration > 0 else 0

    @api.depends("operator_box_ids.active")
    def _compute_active_box_count(self):
        dgc_recs = self.filtered("is_dgc_area")
        non_dgc = self - dgc_recs
        non_dgc.active_box_count = 0
        if not dgc_recs:
            return
        groups = self.env["dgc.operator.box"]._read_group(
            domain=[
                ("area_id", "in", dgc_recs.ids),
                ("active", "=", True),
            ],
            groupby=["area_id"],
            aggregates=["__count"],
        )
        counts = {area.id: count for area, count in groups}
        for rec in dgc_recs:
            rec.active_box_count = counts.get(rec.id, 0)

    def _is_available_today(self):
        """Return False when active_box_count == 0 or today is a non-working date."""
        self.ensure_one()
        if self.active_box_count <= 0:
            return False
        today = _today_tz(self.env)
        if self.non_working_date_ids.filtered(lambda d: d.date == today):
            return False
        return True

    @api.depends("turn_ids.state")
    def _compute_pending_turn_count(self):
        today = _today_tz(self.env)
        dgc_recs = self.filtered("is_dgc_area")
        non_dgc = self - dgc_recs
        non_dgc.pending_turn_count = 0
        if not dgc_recs:
            return

        groups = self.env["dgc.appointment.turn"]._read_group(
            domain=[
                ("area_id", "in", dgc_recs.ids),
                ("date", "=", today),
                ("state", "in", ("new", "waiting", "calling")),
            ],
            groupby=["area_id"],
            aggregates=["__count"],
        )
        counts = {area.id: count for area, count in groups}
        for rec in dgc_recs:
            rec.pending_turn_count = counts.get(rec.id, 0)

    @api.depends(
        "is_dgc_area",
        "appointment_duration",
        "dgc_max_counters",
        "active_box_count",
        "non_working_date_ids.date",
        "slot_ids.weekday",
        "slot_ids.start_hour",
        "slot_ids.end_hour",
    )
    def _compute_max_daily_turns(self):
        for rec in self:
            params = rec._get_capacity_params()
            if not params["available"]:
                rec.max_daily_turns = 0
                continue

            service_minutes = params["service_minutes"]
            counters = params["counters"]

            # Use own slot_ids (we ARE the appointment.type)
            if rec.slot_ids:
                today_weekday = str(_today_tz(self.env).weekday() + 1)
                today_slots = rec.slot_ids.filtered(lambda s, wd=today_weekday: s.weekday == wd)
                if today_slots:
                    total_minutes = sum((s.end_hour - s.start_hour) * 60 for s in today_slots)
                    rec.max_daily_turns = int(total_minutes / service_minutes * counters)
                    continue

            # Fallback: global config hours
            minutes = (params["fallback_end"] - params["fallback_start"]) * 60
            rec.max_daily_turns = int(minutes / service_minutes * counters)

    @staticmethod
    def _now_float_tz(env):
        """Return current local time as a float (e.g. 13.75 for 13:45)."""
        try:
            # Access company.partner_id.tz to verify ACL; the tz value itself
            # is resolved by context_timestamp from the user/context.
            _tz = env.company.partner_id.tz  # noqa: F841 — ACL probe
        except AccessError:
            pass
        rec = env["dgc.appointment.turn"]
        local_now = fields.Datetime.context_timestamp(rec, fields.Datetime.now())
        return local_now.hour + local_now.minute / 60.0

    @api.depends(
        "is_dgc_area",
        "appointment_duration",
        "dgc_max_counters",
        "active_box_count",
        "non_working_date_ids.date",
        "slot_ids.weekday",
        "slot_ids.start_hour",
        "slot_ids.end_hour",
        "turn_ids.state",
        "turn_ids.date",
    )
    def _compute_remaining_turns_today(self):
        today = _today_tz(self.env)
        dgc_recs = self.filtered("is_dgc_area")
        non_dgc = self - dgc_recs
        non_dgc.remaining_turns_today = 0
        if not dgc_recs:
            return

        now_float = self._now_float_tz(self.env)

        # Count turns still pending (active states that consume future capacity)
        ACTIVE_STATES = ("new", "waiting", "calling", "serving")
        groups = self.env["dgc.appointment.turn"]._read_group(
            domain=[
                ("area_id", "in", dgc_recs.ids),
                ("date", "=", today),
                ("state", "in", ACTIVE_STATES),
            ],
            groupby=["area_id"],
            aggregates=["__count"],
        )
        pending = {area.id: count for area, count in groups}

        for rec in dgc_recs:
            params = rec._get_capacity_params()
            if not params["available"]:
                rec.remaining_turns_today = 0
                continue

            service_minutes = params["service_minutes"]
            counters = params["counters"]
            fallback_start = params["fallback_start"]
            fallback_end = params["fallback_end"]

            # Calculate remaining minutes from now until closing
            remaining_minutes = 0.0
            if rec.slot_ids:
                today_weekday = str(today.weekday() + 1)
                today_slots = rec.slot_ids.filtered(lambda s, wd=today_weekday: s.weekday == wd)
                for slot in today_slots:
                    if now_float >= slot.end_hour:
                        # Slot already passed
                        continue
                    elif now_float <= slot.start_hour:
                        # Slot hasn't started yet — full slot
                        remaining_minutes += (slot.end_hour - slot.start_hour) * 60
                    else:
                        # Currently inside this slot — partial
                        remaining_minutes += (slot.end_hour - now_float) * 60
            else:
                # Fallback global hours
                if now_float >= fallback_end:
                    remaining_minutes = 0.0
                elif now_float <= fallback_start:
                    remaining_minutes = (fallback_end - fallback_start) * 60
                else:
                    remaining_minutes = (fallback_end - now_float) * 60

            max_remaining_from_now = int(remaining_minutes / service_minutes * counters)
            turns_still_pending = pending.get(rec.id, 0)
            rec.remaining_turns_today = max(max_remaining_from_now - turns_still_pending, 0)

    def _get_today_schedule(self):
        """Return (start_hour, end_hour) for today from slots or fallback."""
        self.ensure_one()
        if self.slot_ids:
            today_weekday = str(_today_tz(self.env).weekday() + 1)
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

    def _get_display_hex_color(self):
        """Map Odoo color index (0-11) to a hex color string."""
        self.ensure_one()
        return DGC_COLOR_MAP.get(self.dgc_color, '#3498db')

    @api.model
    def _get_dgc_areas_for_user(self, user=None):
        """Retorna las areas DGC asignadas al usuario via staff_user_ids.

        Admins y area managers ven todas las areas DGC.
        Operadores solo ven las areas donde estan en staff_user_ids.

        Args:
            user: Recordset de res.users. Si es None, usa el usuario actual.

        Returns:
            Recordset de appointment.type con las areas DGC del usuario.
        """
        if user is None:
            user = self.env.user
        if user.has_group("dgc_appointment_kiosk.group_dgc_area_manager"):
            return self.sudo().search([('is_dgc_area', '=', True)])
        return self.sudo().search([
            ('is_dgc_area', '=', True),
            ('staff_user_ids', 'in', user.id),
        ])
