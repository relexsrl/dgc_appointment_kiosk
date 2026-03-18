from odoo import fields
from odoo.tests.common import TransactionCase


class TestOperatorDashboard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.area_geo = cls.env["appointment.type"].create(
            {
                "name": "Geografía",
                "is_dgc_area": True,
                "dgc_code": "OD_GEO",
                "category": "recurring",
                "appointment_duration": 0.25,
                "appointment_tz": "America/Argentina/Buenos_Aires",
            }
        )
        cls.area_cat = cls.env["appointment.type"].create(
            {
                "name": "Catastro",
                "is_dgc_area": True,
                "dgc_code": "OD_CAT",
                "category": "recurring",
                "appointment_duration": 0.25,
                "appointment_tz": "America/Argentina/Buenos_Aires",
            }
        )
        cls.operator = cls.env["res.users"].create(
            {
                "name": "Op Dashboard",
                "login": "op_dash_test",
                "group_ids": [
                    (4, cls.env.ref("base.group_user").id),
                    (4, cls.env.ref("dgc_appointment_kiosk.group_dgc_operator").id),
                ],
                "dgc_area_ids": [(4, cls.area_geo.id)],
            }
        )

    def test_dashboard_data_empty(self):
        """Dashboard returns empty lists when no turns exist."""
        data = self.env["dgc.appointment.turn"].with_user(self.operator).get_operator_dashboard_data()
        self.assertFalse(data["current_turn"])
        self.assertEqual(len(data["waiting_turns"]), 0)
        self.assertEqual(len(data["done_turns"]), 0)
        self.assertIn(self.area_geo.id, data["area_ids"])

    def test_dashboard_shows_waiting_turns(self):
        """Dashboard shows waiting turns for operator's areas."""
        self.env["dgc.appointment.turn"].create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        self.env["dgc.appointment.turn"].create(
            {
                "citizen_dni": "87654321",
                "area_id": self.area_geo.id,
            }
        )
        data = self.env["dgc.appointment.turn"].with_user(self.operator).get_operator_dashboard_data()
        self.assertEqual(len(data["waiting_turns"]), 2)

    def test_dashboard_filters_by_area(self):
        """Dashboard only shows turns from operator's assigned areas."""
        self.env["dgc.appointment.turn"].create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        self.env["dgc.appointment.turn"].create(
            {
                "citizen_dni": "87654321",
                "area_id": self.area_cat.id,
            }
        )
        data = self.env["dgc.appointment.turn"].with_user(self.operator).get_operator_dashboard_data()
        # Operator only assigned to GEO
        self.assertEqual(len(data["waiting_turns"]), 1)
        self.assertEqual(data["waiting_turns"][0]["citizen_dni"], "12345678")

    def test_dashboard_current_turn(self):
        """Dashboard shows current turn when operator is serving."""
        turn = self.env["dgc.appointment.turn"].create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        turn.with_user(self.operator).action_call()
        data = self.env["dgc.appointment.turn"].with_user(self.operator).get_operator_dashboard_data()
        self.assertTrue(data["current_turn"])
        self.assertEqual(data["current_turn"]["id"], turn.id)
        self.assertEqual(data["current_turn"]["state"], "calling")

    def test_dashboard_done_turns(self):
        """Dashboard shows today's completed turns."""
        turn = self.env["dgc.appointment.turn"].create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        turn.with_user(self.operator).action_call()
        turn.with_user(self.operator).action_serve()
        turn.with_user(self.operator).action_done()
        data = self.env["dgc.appointment.turn"].with_user(self.operator).get_operator_dashboard_data()
        self.assertEqual(len(data["done_turns"]), 1)
        self.assertEqual(data["done_turns"][0]["turn_number"], turn.turn_number)

    def test_dashboard_excludes_yesterday(self):
        """Dashboard only shows today's turns."""
        yesterday = fields.Date.subtract(fields.Date.context_today(self.env["dgc.appointment.turn"]), days=1)
        self.env["dgc.appointment.turn"].create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
                "date": yesterday,
            }
        )
        data = self.env["dgc.appointment.turn"].with_user(self.operator).get_operator_dashboard_data()
        self.assertEqual(len(data["waiting_turns"]), 0)
