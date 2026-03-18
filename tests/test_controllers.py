import json

from odoo.tests.common import HttpCase


class TestControllers(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.area = cls.env["dgc.appointment.area"].create({
            "name": "Test Area",
            "code": "TST",
            "location": "Hall",
            "avg_service_time": 15,
            "max_counters": 2,
        })

    def setUp(self):
        super().setUp()
        # Clear rate limiter between tests
        from odoo.addons.dgc_appointment_kiosk.controllers.kiosk import KioskController
        KioskController._rate_limits.clear()

    def _json_rpc(self, url, params=None):
        """Helper to make JSON-RPC calls."""
        payload = json.dumps({
            "jsonrpc": "2.0",
            "method": "call",
            "params": params or {},
        })
        response = self.url_open(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_kiosk_page_loads(self):
        """Kiosk page returns 200."""
        response = self.url_open("/kiosk/checkin")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Sistema de Turnos", response.text)

    def test_display_page_loads(self):
        """Display page returns 200."""
        response = self.url_open("/display/queue")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Turnero", response.text)

    def test_areas_api(self):
        """Areas API returns active areas."""
        result = self._json_rpc("/kiosk/api/areas")
        areas = result.get("result", [])
        self.assertIsInstance(areas, list)
        codes = [a["code"] for a in areas]
        self.assertIn("TST", codes)

    def test_create_turn_success(self):
        """Turn creation via API returns success."""
        result = self._json_rpc("/kiosk/api/turn/create", {
            "dni": "12345678",
            "area_id": self.area.id,
        })
        data = result.get("result", {})
        self.assertTrue(data.get("success"), f"Expected success, got: {data}")
        self.assertTrue(data.get("turn_number"))

    def test_create_turn_invalid_dni(self):
        """Invalid DNI returns INVALID_DNI error."""
        result = self._json_rpc("/kiosk/api/turn/create", {
            "dni": "123",
            "area_id": self.area.id,
        })
        data = result.get("result", {})
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("error_code"), "INVALID_DNI")

    def test_create_turn_duplicate(self):
        """Duplicate turn returns DUPLICATE_TURN error."""
        self._json_rpc("/kiosk/api/turn/create", {
            "dni": "99999999",
            "area_id": self.area.id,
        })
        # Clear rate limit so second call goes through
        from odoo.addons.dgc_appointment_kiosk.controllers.kiosk import KioskController
        KioskController._rate_limits.clear()

        result = self._json_rpc("/kiosk/api/turn/create", {
            "dni": "99999999",
            "area_id": self.area.id,
        })
        data = result.get("result", {})
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("error_code"), "DUPLICATE_TURN")

    def test_display_turns_api(self):
        """Display turns API returns structure with calling/waiting."""
        result = self._json_rpc("/display/api/turns")
        data = result.get("result", {})
        self.assertIn("calling", data)
        self.assertIn("waiting", data)
        self.assertIn("scroll_messages", data)

    def test_create_turn_invalid_area(self):
        """Invalid area returns INVALID_AREA error."""
        result = self._json_rpc("/kiosk/api/turn/create", {
            "dni": "12345678",
            "area_id": 99999,
        })
        data = result.get("result", {})
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("error_code"), "INVALID_AREA")

    def test_auth_required_endpoints(self):
        """Authenticated endpoints reject anonymous access."""
        result = self._json_rpc("/api/turn/call", {"turn_id": 1})
        # Should get an error (not logged in)
        self.assertTrue(
            result.get("error") or not result.get("result", {}).get("success")
        )

    def test_areas_api_returns_capacity(self):
        """Areas API includes capacity information."""
        result = self._json_rpc("/kiosk/api/areas")
        areas = result.get("result", [])
        test_area = next((a for a in areas if a["code"] == "TST"), None)
        self.assertIsNotNone(test_area)
        self.assertIn("remaining_turns_today", test_area)
        self.assertIn("max_daily_turns", test_area)
