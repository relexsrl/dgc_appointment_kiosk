import logging
import threading
import time

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class KioskController(http.Controller):
    _rate_limits = {}
    _rate_lock = threading.Lock()

    @classmethod
    def _check_rate_limit(cls, ip, seconds):
        now = time.time()
        with cls._rate_lock:
            last = cls._rate_limits.get(ip, 0)
            if now - last < seconds:
                return True
            cls._rate_limits[ip] = now
            # Clean old entries periodically
            if len(cls._rate_limits) > 1000:
                cutoff = now - 300
                cls._rate_limits = {
                    k: v for k, v in cls._rate_limits.items() if v > cutoff
                }
            return False

    @http.route("/kiosk/checkin", type="http", auth="public", website=False)
    def kiosk_main(self):
        icp = request.env["ir.config_parameter"].sudo()
        values = {
            "timeout": int(icp.get_param("dgc_appointment_kiosk.kiosk_timeout", "30")),
            "require_email": icp.get_param("dgc_appointment_kiosk.kiosk_require_email", "False") in ("True", "true", "1"),
            "show_notes": icp.get_param("dgc_appointment_kiosk.kiosk_show_notes", "False") in ("True", "true", "1"),
            "brand_primary_color": icp.get_param("dgc_appointment_kiosk.brand_primary_color", "#1A237E"),
            "brand_logo_url": icp.get_param("dgc_appointment_kiosk.brand_logo_url", ""),
        }
        return request.render("dgc_appointment_kiosk.kiosk_main_view", values)

    @http.route("/kiosk/api/areas", type="json", auth="public")
    def kiosk_areas(self):
        areas = request.env["dgc.appointment.area"].sudo().search([
            ("active", "=", True),
        ])
        return [{
            "id": area.id,
            "name": area.name,
            "code": area.code,
            "location": area.location or "",
            "welcome_message": area.welcome_message or "",
            "remaining_turns_today": area.remaining_turns_today,
            "max_daily_turns": area.max_daily_turns,
        } for area in areas]

    @http.route("/kiosk/api/turn/create", type="json", auth="public")
    def kiosk_create_turn(self, dni, area_id, email=None, notes=None):
        ip = request.httprequest.remote_addr
        icp = request.env["ir.config_parameter"].sudo()
        rate_seconds = int(icp.get_param("dgc_appointment_kiosk.rate_limit_seconds", "5"))

        if self._check_rate_limit(ip, rate_seconds):
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

        # Validate area
        area = request.env["dgc.appointment.area"].sudo().browse(int(area_id))
        if not area.exists() or not area.active:
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

        # Check duplicate
        from odoo.exceptions import ValidationError
        try:
            partner_result = Turn._find_or_create_partner(dni, None, email)

            vals = {
                "citizen_dni": dni,
                "citizen_name": "",
                "citizen_email": email or "",
                "notes": notes or "",
                "area_id": area.id,
                "partner_id": partner_result.get("partner_id"),
            }
            turn = Turn.create(vals)
        except ValidationError as e:
            return {
                "success": False,
                "error_code": "DUPLICATE_TURN",
                "message": str(e),
            }
        except Exception:
            _logger.exception("Error creating turn")
            return {
                "success": False,
                "error_code": "SERVER_ERROR",
                "message": "Error interno. Intente nuevamente.",
            }

        return {
            "success": True,
            "turn_number": turn.turn_number,
            "area_name": area.name,
            "area_location": area.location or "",
            "email_conflict": partner_result.get("email_conflict", False),
            "existing_email_masked": partner_result.get("existing_email_masked", ""),
        }
