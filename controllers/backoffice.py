from odoo import http
from odoo.http import request


class DgcBackofficeController(http.Controller):

    @http.route("/backoffice/api/my_area_ids", type="jsonrpc", auth="user", methods=["POST"])
    def my_area_ids(self):
        areas = request.env["appointment.type"]._get_dgc_areas_for_user()
        return {"area_ids": areas.ids}
