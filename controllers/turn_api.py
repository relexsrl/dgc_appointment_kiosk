import logging

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class TurnAPIController(http.Controller):

    def _get_turn(self, turn_id):
        turn = request.env["dgc.appointment.turn"].browse(int(turn_id))
        if not turn.exists():
            return None
        return turn

    @http.route("/api/turn/call", type="jsonrpc", auth="user")
    def turn_call(self, turn_id):
        turn = self._get_turn(turn_id)
        if not turn:
            return {"success": False, "message": "Turno no encontrado."}
        try:
            turn.action_call()
            return {"success": True, "turn_number": turn.turn_number, "state": turn.state}
        except (UserError, ValidationError, AccessError) as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            _logger.exception("Error in turn_call: %s", e)
            return {"success": False, "message": "Error interno del servidor"}

    @http.route("/api/turn/serve", type="jsonrpc", auth="user")
    def turn_serve(self, turn_id):
        turn = self._get_turn(turn_id)
        if not turn:
            return {"success": False, "message": "Turno no encontrado."}
        try:
            turn.action_serve()
            return {"success": True, "turn_number": turn.turn_number, "state": turn.state}
        except (UserError, ValidationError, AccessError) as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            _logger.exception("Error in turn_serve: %s", e)
            return {"success": False, "message": "Error interno del servidor"}

    @http.route("/api/turn/done", type="jsonrpc", auth="user")
    def turn_done(self, turn_id):
        turn = self._get_turn(turn_id)
        if not turn:
            return {"success": False, "message": "Turno no encontrado."}
        try:
            turn.action_done()
            return {"success": True, "turn_number": turn.turn_number, "state": turn.state}
        except (UserError, ValidationError, AccessError) as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            _logger.exception("Error in turn_done: %s", e)
            return {"success": False, "message": "Error interno del servidor"}

    @http.route("/api/turn/noshow", type="jsonrpc", auth="user")
    def turn_noshow(self, turn_id):
        turn = self._get_turn(turn_id)
        if not turn:
            return {"success": False, "message": "Turno no encontrado."}
        try:
            turn.action_no_show()
            return {"success": True, "turn_number": turn.turn_number, "state": turn.state}
        except (UserError, ValidationError, AccessError) as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            _logger.exception("Error in turn_noshow: %s", e)
            return {"success": False, "message": "Error interno del servidor"}

    @http.route("/api/turn/derive", type="jsonrpc", auth="user")
    def turn_derive(self, turn_id, to_area_id, reason):
        turn = self._get_turn(turn_id)
        if not turn:
            return {"success": False, "message": "Turno no encontrado."}
        try:
            wizard = request.env["dgc.turn.derive.wizard"].create({
                "turn_id": turn.id,
                "to_area_id": int(to_area_id),
                "reason": reason,
            })
            wizard.action_derive()
            return {"success": True, "turn_number": turn.turn_number, "state": turn.state}
        except (UserError, ValidationError, AccessError) as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            _logger.exception("Error in turn_derive: %s", e)
            return {"success": False, "message": "Error interno del servidor"}
