from odoo import http
from odoo.http import request


class DisplayController(http.Controller):

    @http.route("/display/queue", type="http", auth="public", website=False)
    def display_queue(self):
        icp = request.env["ir.config_parameter"].sudo()
        values = {
            "refresh_interval": int(icp.get_param("dgc_appointment_kiosk.display_refresh_interval", "30")),
            "brand_primary_color": icp.get_param("dgc_appointment_kiosk.brand_primary_color", "#1A237E"),
            "brand_logo_url": icp.get_param("dgc_appointment_kiosk.brand_logo_url", ""),
        }
        return request.render("dgc_appointment_kiosk.display_queue_view", values)

    @http.route("/display/api/turns", type="jsonrpc", auth="public")
    def display_turns(self, area_id=None):
        icp = request.env["ir.config_parameter"].sudo()
        calling_count = int(icp.get_param("dgc_appointment_kiosk.display_calling_count", "3"))
        waiting_count = int(icp.get_param("dgc_appointment_kiosk.display_waiting_count", "10"))

        Turn = request.env["dgc.appointment.turn"].sudo()
        today = request.env["dgc.appointment.turn"]._fields["date"].default(Turn)

        domain_base = [("date", "=", today)]
        if area_id:
            domain_base.append(("area_id", "=", int(area_id)))

        calling = Turn.search(
            domain_base + [("state", "=", "calling")],
            order="call_date desc",
            limit=calling_count,
        )
        waiting = Turn.search(
            domain_base + [("state", "=", "waiting")],
            order="create_date asc",
            limit=waiting_count,
        )

        # Scroll messages
        messages = []
        for i in range(1, 4):
            msg = icp.get_param(f"dgc_appointment_kiosk.scroll_message_{i}", "")
            if msg:
                messages.append(msg)

        return {
            "calling": [{
                "turn_number": t.turn_number,
                "citizen_name": t.citizen_name or "",
                "citizen_dni": t.citizen_dni or "",
                "area_name": t.area_id.name,
                "area_code": t.area_id.dgc_code,
                "area_color": t.area_id._get_display_hex_color(),
                "operator": t.operator_id.name or "",
                "operator_box": t.operator_box or "",
                "call_count": t.call_count,
            } for t in calling],
            "waiting": [{
                "turn_number": t.turn_number,
                "area_name": t.area_id.name,
                "area_code": t.area_id.dgc_code,
                "area_color": t.area_id._get_display_hex_color(),
            } for t in waiting],
            "scroll_messages": messages,
        }
