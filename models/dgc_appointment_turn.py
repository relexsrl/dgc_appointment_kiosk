import logging
import re
from datetime import datetime as _dt

import psycopg2

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)


def _today_tz(env):
    """Return today's date in the company's timezone."""
    try:
        # Try to get timezone from company, but may fail for public users (no ACL on partner_id)
        tz = env.company.partner_id.tz or "America/Argentina/Buenos_Aires"
    except AccessError:
        # Public user or no ACL: use default timezone
        tz = "America/Argentina/Buenos_Aires"
    rec = env["dgc.appointment.turn"]
    local_now = fields.Datetime.context_timestamp(rec, fields.Datetime.now())
    return local_now.date()

TURN_STATES = [
    ("new", _("Nuevo")),
    ("waiting", _("En espera")),
    ("calling", _("Llamando")),
    ("serving", _("Atendiendo")),
    ("done", _("Finalizado")),
    ("derived", _("Derivado")),
    ("no_show", _("No se presentó")),
]

PENDING_STATES = ("new", "waiting", "calling")
# States where a citizen is actively occupying a slot (used for duplicate checking).
# Matches the partial unique index dgc_turn_unique_dni_area_date_pending.
ACTIVE_STATES = ("new", "waiting", "calling", "serving")


class DgcAppointmentTurn(models.Model):
    _name = "dgc.appointment.turn"
    _description = "Turno DGC"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date asc"

    def init(self):
        self.env.cr.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
                dgc_turn_unique_dni_area_date_pending
            ON dgc_appointment_turn (citizen_dni, area_id, date)
            WHERE state IN ('new', 'waiting', 'calling', 'serving')
        """)

    turn_number = fields.Char(
        string="Número de turno",
        readonly=True,
        copy=False,
        tracking=True,
    )
    citizen_dni = fields.Char(
        string="DNI/CUIT",
        required=True,
        index=True,
        tracking=True,
    )
    citizen_name = fields.Char(string="Nombre")
    citizen_email = fields.Char(string="Email")
    notes = fields.Text(string="Notas")
    partner_id = fields.Many2one("res.partner", string="Contacto")
    calendar_event_id = fields.Many2one(
        "calendar.event",
        string="Cita",
        ondelete="set null",
        copy=False,
    )
    source = fields.Selection(
        [("kiosk", "Kiosco"), ("manual", "Manual"), ("portal", "Portal")],
        string="Origen",
        default="kiosk",
        required=True,
    )

    state = fields.Selection(
        TURN_STATES,
        string="Estado",
        default="new",
        required=True,
        tracking=True,
    )
    area_id = fields.Many2one(
        "appointment.type",
        string="Área",
        required=True,
        tracking=True,
        domain="[('is_dgc_area', '=', True)]",
    )
    operator_id = fields.Many2one(
        "res.users",
        string="Operador",
        tracking=True,
    )

    date = fields.Date(
        string="Fecha",
        default=fields.Date.context_today,
        required=True,
    )
    scheduled_datetime = fields.Datetime(
        string="Hora del turno",
        compute="_compute_scheduled_datetime",
        store=True,
    )
    call_date = fields.Datetime(string="Fecha de llamada")
    serve_date = fields.Datetime(string="Fecha de atención")
    done_date = fields.Datetime(string="Fecha de finalización")

    duration = fields.Float(
        string="Duración (min)",
        compute="_compute_duration",
        store=True,
    )
    wait_time = fields.Float(
        string="Tiempo de espera (min)",
        compute="_compute_wait_time",
        store=True,
    )
    call_count = fields.Integer(
        string="Veces llamado",
        default=0,
    )
    elapsed_time_display = fields.Char(
        string="Tiempo transcurrido",
        compute="_compute_elapsed_time_display",
    )
    operator_box = fields.Char(
        string="Box",
        compute="_compute_operator_box",
    )

    call_log_ids = fields.One2many(
        "dgc.appointment.call.log",
        "turn_id",
        string="Historial de llamadas",
    )
    derivation_ids = fields.One2many(
        "dgc.appointment.derivation",
        "turn_id",
        string="Derivaciones",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
    )

    @api.depends("calendar_event_id.start")
    def _compute_scheduled_datetime(self):
        for rec in self:
            rec.scheduled_datetime = rec.calendar_event_id.start if rec.calendar_event_id else False

    @api.depends("serve_date", "done_date")
    def _compute_duration(self):
        for turn in self:
            if turn.serve_date and turn.done_date:
                delta = turn.done_date - turn.serve_date
                turn.duration = delta.total_seconds() / 60.0
            else:
                turn.duration = 0.0

    @api.depends("create_date", "call_date")
    def _compute_wait_time(self):
        for turn in self:
            if turn.create_date and turn.call_date:
                delta = turn.call_date - turn.create_date
                turn.wait_time = delta.total_seconds() / 60.0
            else:
                turn.wait_time = 0.0

    def _compute_elapsed_time_display(self):
        now = fields.Datetime.now()
        for turn in self:
            if turn.state == "serving" and turn.serve_date:
                delta = now - turn.serve_date
                total_secs = max(int(delta.total_seconds()), 0)
                h, remainder = divmod(total_secs, 3600)
                m, s = divmod(remainder, 60)
                turn.elapsed_time_display = f"{h:02d}:{m:02d}:{s:02d}"
            else:
                turn.elapsed_time_display = ""

    @api.depends("operator_id", "area_id")
    def _compute_operator_box(self):
        # Batch read all relevant boxes to avoid N+1
        op_ids = [t.operator_id.id for t in self if t.operator_id]
        area_ids = [t.area_id.id for t in self if t.area_id]
        if op_ids and area_ids:
            boxes = self.env["dgc.operator.box"].sudo().search([
                ("operator_id", "in", op_ids),
                ("area_id", "in", area_ids),
            ])
            box_map = {(b.operator_id.id, b.area_id.id): b.box_number for b in boxes}
        else:
            box_map = {}
        for turn in self:
            turn.operator_box = box_map.get(
                (turn.operator_id.id, turn.area_id.id), ""
            ) if turn.operator_id and turn.area_id else ""

    @api.constrains("citizen_dni", "area_id", "date", "state")
    def _check_duplicate_turn(self):
        icp = self.env["ir.config_parameter"].sudo()
        allow_multiple = icp.get_param(
            "dgc_appointment_kiosk.allow_multiple_turns", "True"
        )
        for turn in self:
            if turn.state not in ACTIVE_STATES:
                continue
            domain = [
                ("citizen_dni", "=", turn.citizen_dni),
                ("date", "=", turn.date),
                ("state", "in", list(ACTIVE_STATES)),
                ("id", "!=", turn.id),
            ]
            if str(allow_multiple).lower() not in ("false", "0", ""):
                domain.append(("area_id", "=", turn.area_id.id))
            if self.search_count(domain):
                raise ValidationError(
                    _("Ya existe un turno pendiente para este DNI/CUIT "
                      "en la misma fecha y área.")
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("turn_number"):
                area = self.env["appointment.type"].browse(vals.get("area_id"))
                seq = self.env["ir.sequence"].next_by_code("dgc.appointment.turn") or "000"
                counter = seq.split("-")[-1] if "-" in seq else seq
                vals["turn_number"] = f"{area.dgc_code or 'GEN'}-{counter}"
            if vals.get("state", "new") == "new":
                vals["state"] = "waiting"
        try:
            with self.env.cr.savepoint():
                return super().create(vals_list)
        except psycopg2.IntegrityError as e:
            if "dgc_turn_unique_dni_area_date_pending" in str(e):
                raise ValidationError(
                    _("Ya existe un turno pendiente para este DNI/CUIT "
                      "en la misma fecha y área.")
                ) from None
            raise

    def action_call(self):
        self.ensure_one()
        if self.state not in ("waiting", "calling"):
            raise UserError(_("Solo se pueden llamar turnos en espera."))
        now = fields.Datetime.now()
        new_count = self.call_count + 1
        vals = {
            "state": "calling",
            "operator_id": self.env.uid,
            "call_count": new_count,
        }
        if not self.call_date:
            vals["call_date"] = now
        self.write(vals)
        self.env["dgc.appointment.call.log"].create({
            "turn_id": self.id,
            "call_datetime": now,
            "operator_id": self.env.uid,
            "call_number": new_count,
        })
        self._send_bus_notification("call")
        self._send_display_notification("call")

    def action_recall(self):
        self.ensure_one()
        if self.state != "calling":
            raise UserError(_("Solo se pueden re-llamar turnos en estado llamando."))
        new_count = self.call_count + 1
        self.write({"call_count": new_count})
        self.env["dgc.appointment.call.log"].create({
            "turn_id": self.id,
            "call_datetime": fields.Datetime.now(),
            "operator_id": self.env.uid,
            "call_number": new_count,
        })
        self._send_bus_notification("recall")
        self._send_display_notification("recall")

    def action_serve(self):
        self.ensure_one()
        if self.state != "calling":
            raise UserError(_("Solo se pueden atender turnos que están siendo llamados."))
        self.write({
            "state": "serving",
            "serve_date": fields.Datetime.now(),
            "operator_id": self.env.uid,
        })
        self._send_bus_notification("serve")
        self._send_display_notification("serve")

    def action_done(self):
        self.ensure_one()
        if self.state != "serving":
            raise UserError(_("Solo se pueden finalizar turnos en atención."))
        self.write({
            "state": "done",
            "done_date": fields.Datetime.now(),
        })
        self._send_bus_notification("done")
        self._send_display_notification("done")

    def action_no_show(self):
        self.ensure_one()
        if self.state != "calling":
            raise UserError(_("Solo se puede marcar 'No se presentó' a turnos llamados."))
        if self.call_count < 1:
            raise UserError(_("Debe llamar al turno al menos una vez antes de marcarlo como no presentado."))
        self.write({"state": "no_show"})
        self._send_bus_notification("no_show")
        self._send_display_notification("no_show")

    def action_derive(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Derivar Turno",
            "res_model": "dgc.turn.derive.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_turn_id": self.id},
        }

    def _send_bus_notification(self, action):
        self.ensure_one()
        area_channel = f"dgc_turn_area_{self.area_id.id}"
        payload = {
            "action": action,
            "turn_id": self.id,
            "turn_number": self.turn_number,
            "citizen_name": self.citizen_name or "",
            "citizen_dni": self.citizen_dni or "",
            "area_id": self.area_id.id,
            "area_name": self.area_id.name,
            "state": self.state,
            "call_count": self.call_count,
            "operator": self.operator_id.name or "",
            "operator_box": self.operator_box or "",
        }
        self.env["bus.bus"]._sendone(area_channel, "dgc_turn_update", payload)

    def _send_display_notification(self, action):
        """Broadcast turn update to the public display channel."""
        self.ensure_one()
        payload = {
            'action': action,
            'turn_id': self.id,
            'turn_number': self.turn_number,
            'area_name': self.area_id.name,
            'area_code': self.area_id.dgc_code,
            'area_color': self.area_id._get_display_hex_color(),
            'state': self.state,
            'operator_box': self.operator_box or '',
            'timestamp': fields.Datetime.now().isoformat(),
        }
        self.env['bus.bus']._sendone('dgc_turn_display', 'dgc_display_update', payload)

    @api.model
    def _find_or_create_partner(self, dni, name, email):
        Partner = self.env["res.partner"].sudo()
        partner = Partner.search([("vat", "=", dni)], limit=1)
        result = {"partner_id": False, "email_conflict": False, "existing_email_masked": ""}
        if partner:
            result["partner_id"] = partner.id
            if email and partner.email and partner.email != email:
                result["email_conflict"] = True
                result["existing_email_masked"] = self._mask_email(partner.email)
            return result
        vals = {"name": name or dni, "vat": dni}
        if email:
            vals["email"] = email
        partner = Partner.create(vals)
        result["partner_id"] = partner.id
        return result

    @staticmethod
    def _mask_email(email):
        if not email or "@" not in email:
            return email or ""
        local, domain = email.split("@", 1)
        masked = local[:3] + "***" if len(local) > 3 else local[0] + "***"
        return f"{masked}@{domain}"

    @staticmethod
    def _mask_dni(dni):
        if not dni or len(dni) <= 3:
            return dni or ""
        return "*" * (len(dni) - 3) + dni[-3:]

    @api.model
    def _validate_dni(self, dni):
        if not dni or not re.match(r"^\d+$", dni):
            return False
        length = len(dni)
        if length in (7, 8):
            return True
        if length == 11:
            return self._validate_cuit(dni)
        return False

    @staticmethod
    def _validate_cuit(cuit):
        weights = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        digits = [int(d) for d in cuit]
        total = sum(d * w for d, w in zip(digits[:10], weights))
        remainder = total % 11
        if remainder == 0:
            expected = 0
        elif remainder == 1:
            expected = 9
        else:
            expected = 11 - remainder
        return digits[10] == expected

    @api.model
    def get_operator_dashboard_data(self):
        """Return all data needed for the operator dashboard in a single RPC call."""
        user = self.env.user
        area_ids = self.env['appointment.type']._get_dgc_areas_for_user(user).ids
        today = _today_tz(self.env)

        current = self.search_read(
            [
                ("operator_id", "=", user.id),
                ("state", "in", ("calling", "serving")),
                ("date", "=", today),
            ],
            fields=[
                "turn_number", "citizen_dni", "citizen_name", "citizen_email",
                "state", "area_id", "serve_date", "call_date", "call_count",
                "notes", "elapsed_time_display", "operator_box",
            ],
            limit=1,
        )
        # --- Single query for all pending turns (new, waiting, calling) ---
        # Replaces separate search_read(waiting) + search_count(pending)
        pending_all = self.search_read(
            [
                ("area_id", "in", area_ids),
                ("state", "in", ["new", "waiting", "calling"]),
                ("date", "=", today),
            ],
            fields=[
                "turn_number", "citizen_dni", "citizen_name", "area_id",
                "create_date", "operator_box", "state",
            ],
            order="create_date asc",
        )
        pending_count = len(pending_all)
        waiting = [t for t in pending_all if t["state"] == "waiting"]
        done = self.search_read(
            [
                ("area_id", "in", area_ids),
                ("state", "=", "done"),
                ("date", "=", today),
            ],
            fields=[
                "turn_number", "citizen_dni", "citizen_name", "area_id",
                "duration", "operator_id", "done_date", "operator_box",
            ],
            order="done_date desc",
            limit=50,
        )
        # --- KPIs: served_count + avg_duration in one _read_group ---
        avg_duration = 0.0
        served_count = 0
        duration_groups = self._read_group(
            domain=[
                ('state', '=', 'done'),
                ('date', '=', today),
                ('area_id', 'in', area_ids),
            ],
            groupby=[],
            aggregates=['duration:avg', '__count'],
        )
        if duration_groups:
            avg_val, count_val = duration_groups[0]
            if avg_val is not None:
                avg_duration = round(avg_val, 1)
            served_count = count_val or 0

        derivation_count = self.env['dgc.appointment.derivation'].search_count([
            ('from_area_id', 'in', area_ids),
            ('derivation_date', '>=', fields.Datetime.to_string(
                _dt.combine(today, _dt.min.time())
            )),
            ('derivation_date', '<', fields.Datetime.to_string(
                _dt.combine(today, _dt.max.time())
            )),
        ])

        return {
            "current_turn": current[0] if current else False,
            "waiting_turns": waiting,
            "done_turns": done,
            "area_ids": area_ids,
            "kpis": {
                "served_count": served_count,
                "avg_duration": avg_duration,
                "pending_count": pending_count,
                "derivation_count": derivation_count,
            },
        }

    @api.model
    def _cron_close_pending_turns(self):
        yesterday = fields.Date.subtract(_today_tz(self.env), days=1)
        pending_turns = self.search([
            ("date", "<=", yesterday),
            ("state", "in", list(PENDING_STATES)),
            ("call_count", ">", 0),
        ])
        if pending_turns:
            pending_turns.write({"state": "no_show"})
            _logger.info("Closed %d called-but-no-show turns from %s or earlier", len(pending_turns), yesterday)

    @api.model
    def _cron_cleanup_rate_limit_keys(self):
        """Remove expired rate-limit ICP keys (older than 24 hours)."""
        import json, time
        cutoff = time.time() - 86400
        icp = self.env["ir.config_parameter"].sudo()
        params = icp.search([("key", "like", "dgc_kiosk.rl.%")])
        expired = self.env["ir.config_parameter"]
        for param in params:
            try:
                state = json.loads(param.value)
                if state.get("ts", 0) < cutoff:
                    expired |= param
            except (ValueError, KeyError):
                expired |= param
        if expired:
            expired.unlink()
            _logger.info("DGC: cleaned up %d expired rate-limit keys", len(expired))
