import json

from odoo.tests.common import HttpCase


class TestTurnAPI(HttpCase):
    """Tests for the /api/turn/* JSON-RPC endpoints (auth=user)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.area = cls.env["appointment.type"].create(
            {
                "name": "API Test Area",
                "is_dgc_area": True,
                "dgc_code": "TA_API",
                "dgc_max_counters": 2,
                "category": "recurring",
                "appointment_duration": 0.25,
                "appointment_tz": "America/Argentina/Buenos_Aires",
            }
        )

        cls.operator = cls.env["res.users"].create(
            {
                "name": "Operador API Test",
                "login": "op_api_test",
                "password": "op_api_test",
                "group_ids": [
                    (4, cls.env.ref("base.group_user").id),
                    (4, cls.env.ref("dgc_appointment_kiosk.group_dgc_operator").id),
                ],
            }
        )
        cls.area.staff_user_ids = [(4, cls.operator.id)]

    def _create_test_turn(self, dni="12345678"):
        """Helper to create a turn in waiting state."""
        return self.env["dgc.appointment.turn"].create(
            {
                "citizen_dni": dni,
                "area_id": self.area.id,
                "source": "kiosk",
            }
        )

    def _json_rpc(self, url, params=None):
        """Helper to make authenticated JSON-RPC calls."""
        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": params or {},
            }
        )
        response = self.url_open(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        if response.status_code != 200:
            return {"error": f"Status {response.status_code}"}
        return response.json()

    def test_turn_call_success(self):
        """POST /api/turn/call transitions turn to 'calling'."""
        turn = self._create_test_turn()
        self.authenticate("op_api_test", "op_api_test")
        result = self._json_rpc("/api/turn/call", {"turn_id": turn.id})
        data = result.get("result", {})
        self.assertTrue(data.get("success"), f"Expected success, got: {data}")
        self.assertEqual(data.get("state"), "calling")
        turn.invalidate_recordset()
        self.assertEqual(turn.state, "calling")

    def test_turn_serve_success(self):
        """POST /api/turn/serve transitions a called turn to 'serving'."""
        turn = self._create_test_turn()
        turn.with_user(self.operator).action_call()
        self.authenticate("op_api_test", "op_api_test")
        result = self._json_rpc("/api/turn/serve", {"turn_id": turn.id})
        data = result.get("result", {})
        self.assertTrue(data.get("success"), f"Expected success, got: {data}")
        self.assertEqual(data.get("state"), "serving")
        turn.invalidate_recordset()
        self.assertEqual(turn.state, "serving")

    def test_turn_done_success(self):
        """POST /api/turn/done transitions a serving turn to 'done'."""
        turn = self._create_test_turn()
        turn.with_user(self.operator).action_call()
        turn.with_user(self.operator).action_serve()
        self.authenticate("op_api_test", "op_api_test")
        result = self._json_rpc("/api/turn/done", {"turn_id": turn.id})
        data = result.get("result", {})
        self.assertTrue(data.get("success"), f"Expected success, got: {data}")
        self.assertEqual(data.get("state"), "done")
        turn.invalidate_recordset()
        self.assertEqual(turn.state, "done")

    def test_turn_noshow_success(self):
        """POST /api/turn/noshow transitions a called turn to 'no_show'."""
        turn = self._create_test_turn()
        turn.with_user(self.operator).action_call()
        self.authenticate("op_api_test", "op_api_test")
        result = self._json_rpc("/api/turn/noshow", {"turn_id": turn.id})
        data = result.get("result", {})
        self.assertTrue(data.get("success"), f"Expected success, got: {data}")
        self.assertEqual(data.get("state"), "no_show")
        turn.invalidate_recordset()
        self.assertEqual(turn.state, "no_show")

    def test_turn_not_found(self):
        """Calling an endpoint with an invalid turn_id returns an error."""
        self.authenticate("op_api_test", "op_api_test")
        result = self._json_rpc("/api/turn/call", {"turn_id": 999999})
        data = result.get("result", {})
        self.assertFalse(data.get("success"), "Expected failure for non-existent turn")
        self.assertIn("no encontrado", data.get("message", "").lower())
