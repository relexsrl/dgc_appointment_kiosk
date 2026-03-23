import json

from odoo.tests.common import HttpCase


class TestControllers(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.area = cls.env["appointment.type"].create(
            {
                "name": "Test Area",
                "is_dgc_area": True,
                "dgc_code": "HC_TST",
                "dgc_location": "Hall",
                "dgc_max_counters": 2,
                "category": "recurring",
                "appointment_duration": 0.25,
                "appointment_tz": "America/Argentina/Buenos_Aires",
            }
        )

    def setUp(self):
        super().setUp()
        # Set tokens for tests
        self.kiosk_token = "test-kiosk-token"
        self.display_token = "test-display-token"
        self.env["ir.config_parameter"].sudo().set_param("dgc_appointment_kiosk.kiosk_token", self.kiosk_token)
        self.env["ir.config_parameter"].sudo().set_param("dgc_appointment_kiosk.display_token", self.display_token)

    def _json_rpc(self, url, params=None):
        """Helper to make JSON-RPC calls."""
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
        # Check if response status is 200 (or if it's an error from the app)
        if response.status_code != 200:
            return {"error": f"Status {response.status_code}"}
        return response.json()

    def test_kiosk_page_loads(self):
        """Kiosk page returns 200."""
        response = self.url_open(f"/kiosk/{self.kiosk_token}/checkin")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Sistema de Turnos", response.text)

    def test_display_page_loads(self):
        """Display page returns 200."""
        response = self.url_open(f"/display/{self.display_token}/queue")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Turnero", response.text)

    def test_areas_api(self):
        """Areas API returns active areas."""
        result = self._json_rpc(f"/kiosk/{self.kiosk_token}/api/areas")
        areas = result.get("result", [])
        self.assertIsInstance(areas, list)
        codes = [a["code"] for a in areas]
        self.assertIn("HC_TST", codes)

    def test_create_turn_success(self):
        """Turn creation via API returns success."""
        result = self._json_rpc(
            f"/kiosk/{self.kiosk_token}/api/turn/create",
            {
                "dni": "12345678",
                "area_id": self.area.id,
            },
        )
        data = result.get("result", {})
        self.assertTrue(data.get("success"), f"Expected success, got: {data}")
        self.assertTrue(data.get("turn_number"))

    def test_create_turn_invalid_dni(self):
        """Invalid DNI returns INVALID_DNI error."""
        result = self._json_rpc(
            f"/kiosk/{self.kiosk_token}/api/turn/create",
            {
                "dni": "123",
                "area_id": self.area.id,
            },
        )
        data = result.get("result", {})
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("error_code"), "INVALID_DNI")

    def test_create_turn_duplicate(self):
        """Duplicate turn returns DUPLICATE_TURN error."""
        self._json_rpc(
            f"/kiosk/{self.kiosk_token}/api/turn/create",
            {
                "dni": "99999999",
                "area_id": self.area.id,
            },
        )
        
        result = self._json_rpc(
            f"/kiosk/{self.kiosk_token}/api/turn/create",
            {
                "dni": "99999999",
                "area_id": self.area.id,
            },
        )
        data = result.get("result", {})
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("error_code"), "DUPLICATE_TURN")

    def test_display_turns_api(self):
        """Display turns API returns structure with calling/waiting."""
        result = self._json_rpc(f"/display/{self.display_token}/api/turns")
        data = result.get("result", {})
        self.assertIn("calling", data)
        self.assertIn("waiting", data)
        self.assertIn("scroll_messages", data)

    def test_create_turn_invalid_area(self):
        """Invalid area returns INVALID_AREA error."""
        result = self._json_rpc(
            f"/kiosk/{self.kiosk_token}/api/turn/create",
            {
                "dni": "12345678",
                "area_id": 99999,
            },
        )
        data = result.get("result", {})
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("error_code"), "INVALID_AREA")

    def test_invalid_token_rejected(self):
        """Invalid token rejected."""
        # 1. Page test: check 404
        response = self.url_open(f"/kiosk/wrong-token/checkin")
        self.assertEqual(response.status_code, 404)
        
        # 2. JSON-RPC test: verify error response
        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {},
            }
        )
        response = self.url_open(
            f"/kiosk/wrong-token/api/areas",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        # Odoo's JSON-RPC endpoint returns status 200.
        # Since the controller returns a dict {"error": ...}, it is wrapped in "result".
        json_response = response.json()
        self.assertIn("error", json_response.get("result", {}))
        self.assertEqual(json_response["result"]["error"]["message"], "Invalid token")
