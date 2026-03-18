from odoo import api, fields, models


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
            area.pending_turn_count = self.env["dgc.appointment.turn"].search_count([
                ("area_id", "=", area.id),
                ("date", "=", today),
                ("state", "in", ("new", "waiting", "calling")),
            ])

    def _compute_max_daily_turns(self):
        icp = self.env["ir.config_parameter"].sudo()
        hour_start = float(icp.get_param("dgc_appointment_kiosk.hour_start", "8.0"))
        hour_end = float(icp.get_param("dgc_appointment_kiosk.hour_end", "14.0"))
        for area in self:
            if area.avg_service_time > 0:
                minutes = (hour_end - hour_start) * 60
                area.max_daily_turns = int(minutes / area.avg_service_time * area.max_counters)
            else:
                area.max_daily_turns = 0

    def _compute_remaining_turns_today(self):
        today = fields.Date.context_today(self)
        for area in self:
            used = self.env["dgc.appointment.turn"].search_count([
                ("area_id", "=", area.id),
                ("date", "=", today),
                ("state", "!=", "no_show"),
            ])
            area.remaining_turns_today = max(area.max_daily_turns - used, 0)
