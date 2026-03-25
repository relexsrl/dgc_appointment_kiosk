import hashlib
import logging
import threading
import time

from odoo import http
from odoo.http import request

from ..models.dgc_appointment_turn import _today_tz
from ..utils import sanitize_hex_color

_logger = logging.getLogger(__name__)

_rate_limit_store = {}
_rate_limit_lock = threading.Lock()


class KioskController(http.Controller):

    @classmethod
    def _verify_token(cls, token):
        icp = request.env["ir.config_parameter"].sudo()
        valid_token = icp.get_param("dgc_appointment_kiosk.kiosk_token")
        return valid_token and token == valid_token

    @classmethod
    def _check_rate_limit(cls, ip, window=60, max_hits=5):
        ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
        now = time.time()
        with _rate_limit_lock:
            state = _rate_limit_store.get(ip_hash)
            if state and now - state["ts"] < window:
                if state["count"] >= max_hits:
                    return True
                state["count"] += 1
            else:
                _rate_limit_store[ip_hash] = {"ts": now, "count": 1}
            # Cleanup if store grows too large
            if len(_rate_limit_store) > 1000:
                cutoff = now - (window * 2)
                expired = [k for k, v in _rate_limit_store.items() if v["ts"] < cutoff]
                for k in expired:
                    del _rate_limit_store[k]
        return False

    @http.route("/kiosk/<string:token>/checkin", type="http", auth="public", website=False)
    def kiosk_main(self, token):
        if not self._verify_token(token):
            return request.not_found()
        icp = request.env["ir.config_parameter"].sudo()
        company = request.env.company
        values = {
            "token": token,
            "timeout": int(icp.get_param("dgc_appointment_kiosk.kiosk_timeout", "30")),
            "require_email": icp.get_param("dgc_appointment_kiosk.kiosk_require_email", "False") in ("True", "true", "1"),
            "show_notes": icp.get_param("dgc_appointment_kiosk.kiosk_show_notes", "False") in ("True", "true", "1"),
            "brand_primary_color": sanitize_hex_color(icp.get_param("dgc_appointment_kiosk.brand_primary_color", "#1A237E")),
            "brand_logo_url": f"/web/image/res.company/{company.id}/logo",
        }
        return request.render("dgc_appointment_kiosk.kiosk_main_view", values)

    @http.route("/kiosk/<string:token>/api/areas", type="jsonrpc", auth="public")
    def kiosk_areas(self, token):
        if not self._verify_token(token):
            return {"error": {"message": "Invalid token", "code": 403}}
        areas = request.env["appointment.type"].sudo().search([
            ("is_dgc_area", "=", True),
            ("active", "=", True),
        ])

        # Single query to get queue counts per area
        today = _today_tz(request.env)
        Turn = request.env["dgc.appointment.turn"].sudo()
        area_ids = areas.ids
        queue_data = Turn._read_group(
            [("date", "=", today), ("state", "in", ["new", "waiting", "calling"]), ("area_id", "in", area_ids)],
            groupby=["area_id"],
            aggregates=["__count"],
        )
        queue_counts = {area.id: count for area, count in queue_data}

        result = []
        for area in areas:
            turns_in_queue = queue_counts.get(area.id, 0)
            service_minutes = int(area.appointment_duration * 60) if area.appointment_duration > 0 else 15
            estimated_wait_minutes = turns_in_queue * service_minutes
            result.append({
                "id": area.id,
                "name": area.name,
                "code": area.dgc_code,
                "location": area.dgc_location or "",
                "welcome_message": area.dgc_welcome_message or "",
                "remaining_turns_today": area.remaining_turns_today,
                "max_daily_turns": area.max_daily_turns,
                "estimated_wait_minutes": estimated_wait_minutes,
                "turns_in_queue": turns_in_queue,
            })
        return result

    @http.route("/kiosk/<string:token>/api/turn/status", type="jsonrpc", auth="public")
    def kiosk_turn_status(self, token, dni):
        """Check active turn status for a given DNI."""
        if not self._verify_token(token):
            return {"error": {"message": "Invalid token", "code": 403}}
        ip = request.httprequest.remote_addr
        icp = request.env["ir.config_parameter"].sudo()
        window = int(icp.get_param("dgc_appointment_kiosk.rate_limit_seconds", "60"))
        max_hits = int(icp.get_param("dgc_appointment_kiosk.rate_limit_max_hits", "5"))

        if self._check_rate_limit(ip, window=window, max_hits=max_hits):
            return {
                "found": False,
                "error_code": "RATE_LIMIT",
                "message": "Demasiadas solicitudes. Espere unos segundos.",
            }

        Turn = request.env["dgc.appointment.turn"].sudo()

        # Validate DNI format
        if not Turn._validate_dni(dni):
            return {
                "found": False,
                "error_code": "INVALID_DNI",
                "message": "El DNI/CUIT ingresado no es válido.",
            }

        # Normalize: extract base DNI from CUIT
        dni = Turn._normalize_dni(dni)

        today = _today_tz(request.env)

        # Search for active turn: today, matching DNI, active states
        turn = Turn.search([
            ("citizen_dni", "=", dni),
            ("date", "=", today),
            ("state", "in", ["new", "waiting", "calling", "serving"]),
        ], order="create_date desc", limit=1)

        if not turn:
            return {"found": False}

        # Calculate position in queue (same area, same day, earlier ID, pending states)
        position = Turn.search_count([
            ("area_id", "=", turn.area_id.id),
            ("date", "=", turn.date),
            ("state", "in", ["new", "waiting"]),
            ("id", "<", turn.id),
        ]) + 1  # +1 for 1-based position

        # Estimate wait time
        area = turn.area_id
        service_minutes = int(area.appointment_duration * 60) if area.appointment_duration > 0 else 15
        estimated_wait_minutes = max(0, (position - 1) * service_minutes)

        return {
            "found": True,
            "turn_number": turn.turn_number,
            "area_name": area.name,
            "state": turn.state,
            "position": position,
            "estimated_wait_minutes": estimated_wait_minutes,
        }

    @http.route("/kiosk/<string:token>/api/turn/create", type="jsonrpc", auth="public")
    def kiosk_create_turn(self, token, dni, area_id, email=None, notes=None):
        if not self._verify_token(token):
            return {"error": {"message": "Invalid token", "code": 403}}
        ip = request.httprequest.remote_addr
        icp = request.env["ir.config_parameter"].sudo()
        window = int(icp.get_param("dgc_appointment_kiosk.rate_limit_seconds", "60"))
        max_hits = int(icp.get_param("dgc_appointment_kiosk.rate_limit_max_hits", "5"))

        if self._check_rate_limit(ip, window=window, max_hits=max_hits):
            return {
                "success": False,
                "error_code": "RATE_LIMIT",
                "message": "Demasiadas solicitudes. Espere unos segundos.",
            }

        Turn = request.env["dgc.appointment.turn"].sudo()

        # Validate DNI
        if not Turn._validate_dni(dni):
            return {
                "success": False,
                "error_code": "INVALID_DNI",
                "message": "El DNI/CUIT ingresado no es válido.",
            }

        # Normalize: extract base DNI from CUIT
        dni = Turn._normalize_dni(dni)

        # Validate area
        area = request.env["appointment.type"].sudo().browse(int(area_id))
        if not area.exists() or not area.active or not area.is_dgc_area:
            return {
                "success": False,
                "error_code": "INVALID_AREA",
                "message": "El área seleccionada no está disponible.",
            }

        # Check capacity
        if area.remaining_turns_today <= 0:
            return {
                "success": False,
                "error_code": "CAPACITY_FULL",
                "message": "No hay más turnos disponibles para esta área hoy.",
            }

        # Step 5: explicit duplicate check before partner creation
        allow_multiple = icp.get_param("dgc_appointment_kiosk.allow_multiple_turns", "True")
        allow_multiple_bool = str(allow_multiple).lower() not in ("false", "0", "")
        today = _today_tz(request.env)
        dup_domain = [
            ("citizen_dni", "=", dni),
            ("date", "=", today),
            ("state", "in", ["new", "waiting", "calling", "serving"]),
        ]
        if allow_multiple_bool:
            dup_domain.append(("area_id", "=", area.id))
        if request.env["dgc.appointment.turn"].sudo().search_count(dup_domain):
            return {
                "success": False,
                "error_code": "DUPLICATE_TURN",
                "message": "Ya existe un turno pendiente para este DNI/CUIT en la misma fecha y área.",
            }

        from odoo.exceptions import AccessError, UserError, ValidationError
        try:
            partner_result = Turn._find_or_create_partner(dni, None, email)

            vals = {
                "citizen_dni": dni,
                "citizen_name": "",
                "citizen_email": email or "",
                "notes": notes or "",
                "area_id": area.id,
                "partner_id": partner_result.get("partner_id"),
                "source": "kiosk",
            }
            turn = Turn.create(vals)
        except (UserError, ValidationError, AccessError) as e:
            return {
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": str(e),
            }
        except Exception:
            _logger.exception("Error creating turn")
            return {
                "success": False,
                "error_code": "SERVER_ERROR",
                "message": "Error interno. Intente nuevamente.",
            }

        # Count turns ahead in queue (same area, same day, earlier ID, pending states)
        turns_ahead = request.env["dgc.appointment.turn"].sudo().search_count([
            ("area_id", "=", area.id),
            ("date", "=", turn.date),
            ("state", "in", ["new", "waiting", "calling"]),
            ("id", "<", turn.id),
        ])
        service_minutes = int(area.appointment_duration * 60) if area.appointment_duration > 0 else 15
        estimated_wait_minutes = turns_ahead * service_minutes

        return {
            "success": True,
            "turn_number": turn.turn_number,
            "area_name": area.name,
            "area_location": area.dgc_location or "",
            "turns_ahead": turns_ahead,
            "estimated_wait_minutes": estimated_wait_minutes,
            "email_conflict": partner_result.get("email_conflict", False),
            "existing_email_masked": partner_result.get("existing_email_masked", ""),
        }
