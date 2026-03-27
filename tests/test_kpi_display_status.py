import json
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import HttpCase, TransactionCase


# ── T-15: KPI & Display Bus Tests ──────────────────────────────────────────


@tagged('standard', 'at_install')
class TestKpiDashboard(TransactionCase):
    """Tests for the KPI section of get_operator_dashboard_data()."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Area = cls.env["appointment.type"]
        cls.Turn = cls.env["dgc.appointment.turn"]

        cls.area = cls.Area.create(
            {
                "name": "KPI Test Area",
                "is_dgc_area": True,
                "dgc_code": "TX_KPI",
                "category": "recurring",
                "appointment_duration": 0.25,
                "appointment_tz": "America/Argentina/Buenos_Aires",
            }
        )
        cls.area_other = cls.Area.create(
            {
                "name": "KPI Other Area",
                "is_dgc_area": True,
                "dgc_code": "TX_OTH",
                "category": "recurring",
                "appointment_duration": 0.25,
                "appointment_tz": "America/Argentina/Buenos_Aires",
            }
        )
        cls.operator = cls.env["res.users"].create(
            {
                "name": "Op KPI Test",
                "login": "op_kpi_test",
                "group_ids": [
                    (4, cls.env.ref("base.group_user").id),
                    (4, cls.env.ref("dgc_appointment_kiosk.group_dgc_operator").id),
                ],
            }
        )
        cls.area.staff_user_ids = [(4, cls.operator.id)]
        # operator is NOT assigned to area_other

    def _create_turn(self, dni="12345678", area=None, state=None):
        """Helper to create a turn, optionally forcing a state."""
        area = area or self.area
        turn = self.Turn.create(
            {
                "citizen_dni": dni,
                "area_id": area.id,
            }
        )
        if state and state != "waiting":
            # Force the state via write to bypass workflow constraints
            turn.write({"state": state})
        return turn

    def _get_kpis(self):
        data = self.Turn.with_user(self.operator).get_operator_dashboard_data()
        return data["kpis"]

    # 1. test_kpis_empty_day
    def test_kpis_empty_day(self):
        """No turns today → all KPIs are 0."""
        kpis = self._get_kpis()
        self.assertEqual(kpis["served_count"], 0)
        self.assertEqual(kpis["avg_duration"], 0.0)
        self.assertEqual(kpis["pending_count"], 0)
        self.assertEqual(kpis["derivation_count"], 0)

    # 2. test_kpis_served_count
    def test_kpis_served_count(self):
        """Create 3 turns, mark 2 as done → served_count = 2."""
        t1 = self._create_turn(dni="30000001")
        t2 = self._create_turn(dni="30000002")
        self._create_turn(dni="30000003")  # stays waiting

        for t in (t1, t2):
            t.with_user(self.operator).action_call()
            t.with_user(self.operator).action_serve()
            t.with_user(self.operator).action_done()

        kpis = self._get_kpis()
        self.assertEqual(kpis["served_count"], 2)

    # 3. test_kpis_avg_duration
    def test_kpis_avg_duration(self):
        """Create turns with known durations, verify average."""
        now = fields.Datetime.now()
        t1 = self._create_turn(dni="30000011")
        t1.with_user(self.operator).action_call()
        t1.with_user(self.operator).action_serve()
        t1.with_user(self.operator).action_done()
        # duration = 10 min
        t1.write({
            "serve_date": now - timedelta(minutes=10),
            "done_date": now,
        })

        t2 = self._create_turn(dni="30000012")
        t2.with_user(self.operator).action_call()
        t2.with_user(self.operator).action_serve()
        t2.with_user(self.operator).action_done()
        # duration = 20 min
        t2.write({
            "serve_date": now - timedelta(minutes=20),
            "done_date": now,
        })

        kpis = self._get_kpis()
        # avg should be (10 + 20) / 2 = 15.0
        self.assertAlmostEqual(kpis["avg_duration"], 15.0, places=0)

    # 4. test_kpis_pending_count
    def test_kpis_pending_count(self):
        """Create turns in new/waiting/calling states → correct count."""
        self._create_turn(dni="30000021")  # waiting
        self._create_turn(dni="30000022")  # waiting
        t3 = self._create_turn(dni="30000023")
        t3.with_user(self.operator).action_call()  # calling

        kpis = self._get_kpis()
        self.assertEqual(kpis["pending_count"], 3)

    # 5. test_kpis_derivation_count
    def test_kpis_derivation_count(self):
        """Create derivations → correct count."""
        self.area_other.staff_user_ids = [(4, self.operator.id)]
        t1 = self._create_turn(dni="30000031")
        wizard = (
            self.env["dgc.turn.derive.wizard"]
            .with_user(self.operator)
            .create(
                {
                    "turn_id": t1.id,
                    "to_area_id": self.area_other.id,
                    "reason": "Test derivation",
                }
            )
        )
        wizard.action_derive()

        kpis = self._get_kpis()
        self.assertEqual(kpis["derivation_count"], 1)

    # 6. test_kpis_filtered_by_area
    def test_kpis_filtered_by_area(self):
        """KPIs only count turns from operator's assigned areas."""
        # Turn in operator's area
        t1 = self._create_turn(dni="30000041", area=self.area)
        t1.with_user(self.operator).action_call()
        t1.with_user(self.operator).action_serve()
        t1.with_user(self.operator).action_done()

        # Turn in other area (operator is NOT assigned)
        self.Turn.create(
            {
                "citizen_dni": "30000042",
                "area_id": self.area_other.id,
            }
        )

        kpis = self._get_kpis()
        self.assertEqual(kpis["served_count"], 1)
        # pending should be 0 for the operator's area since t1 is done
        self.assertEqual(kpis["pending_count"], 0)


@tagged('standard', 'at_install')
class TestDisplayBusNotifications(TransactionCase):
    """Tests for the display bus notification channel (dgc_turn_display)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.area = cls.env["appointment.type"].create(
            {
                "name": "Display Test Area",
                "is_dgc_area": True,
                "dgc_code": "TX_DIS",
                "dgc_color": 3,
                "category": "recurring",
                "appointment_duration": 0.25,
                "appointment_tz": "America/Argentina/Buenos_Aires",
            }
        )
        cls.operator = cls.env["res.users"].create(
            {
                "name": "Op Display Test",
                "login": "op_display_test",
                "group_ids": [
                    (4, cls.env.ref("base.group_user").id),
                    (4, cls.env.ref("dgc_appointment_kiosk.group_dgc_operator").id),
                ],
            }
        )
        cls.area.staff_user_ids = [(4, cls.operator.id)]

    # 7. test_display_notification_on_call
    def test_display_notification_on_call(self):
        """Call a turn → bus message sent to 'dgc_turn_display' channel."""
        turn = self.env["dgc.appointment.turn"].create(
            {
                "citizen_dni": "40000001",
                "area_id": self.area.id,
            }
        )
        with patch.object(type(self.env["bus.bus"]), "_sendone") as mock_send:
            turn.with_user(self.operator).action_call()
            # Collect all channels across all calls
            channels = [call[0][0] for call in mock_send.call_args_list]
            self.assertIn("dgc_turn_display", channels)

    # 8. test_display_notification_payload
    def test_display_notification_payload(self):
        """Verify payload contains expected fields."""
        turn = self.env["dgc.appointment.turn"].create(
            {
                "citizen_dni": "40000002",
                "area_id": self.area.id,
            }
        )
        with patch.object(type(self.env["bus.bus"]), "_sendone") as mock_send:
            turn.with_user(self.operator).action_call()
            # Find the display notification call
            display_calls = [
                call
                for call in mock_send.call_args_list
                if call[0][0] == "dgc_turn_display"
            ]
            self.assertTrue(display_calls, "Expected a display notification")
            payload = display_calls[0][0][2]
            self.assertIn("turn_number", payload)
            self.assertIn("area_name", payload)
            self.assertIn("area_color", payload)
            self.assertIn("state", payload)
            self.assertIn("operator_box", payload)
            self.assertIn("timestamp", payload)
            self.assertEqual(payload["action"], "call")
            self.assertEqual(payload["area_code"], "TX_DIS")
            self.assertEqual(payload["turn_number"], turn.turn_number)

    # 9. test_display_color_helper
    def test_display_color_helper(self):
        """_get_display_hex_color() returns correct hex for known color indices and default for unknown."""
        from odoo.addons.dgc_appointment_kiosk.models.appointment_type import DGC_COLOR_MAP

        # Known color index 3 -> '#6CC1ED'
        self.area.dgc_color = 3
        self.assertEqual(self.area._get_display_hex_color(), "#6CC1ED")

        # Known color index 0 -> '#F06050'
        self.area.dgc_color = 0
        self.assertEqual(self.area._get_display_hex_color(), "#F06050")

        # Unknown color index 99 -> default '#3498db'
        self.area.dgc_color = 99
        self.assertEqual(self.area._get_display_hex_color(), "#3498db")

        # Verify all known indices return a value from the map
        for idx, expected_hex in DGC_COLOR_MAP.items():
            self.area.dgc_color = idx
            self.assertEqual(
                self.area._get_display_hex_color(),
                expected_hex,
                f"Color index {idx} should map to {expected_hex}",
            )


# ── T-23: Turn Status Endpoint Tests ──────────────────────────────────────


@tagged('post_install', '-at_install')
class TestTurnStatusEndpoint(HttpCase):
    """Tests for the /kiosk/api/turn/status JSON-RPC endpoint."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.area = cls.env["appointment.type"].create(
            {
                "name": "Status Test Area",
                "is_dgc_area": True,
                "dgc_code": "TX_STA",
                "dgc_max_counters": 2,
                "category": "recurring",
                "appointment_duration": 0.25,
                "appointment_tz": "America/Argentina/Buenos_Aires",
            }
        )
        # Set a generous rate limit to avoid throttling during tests
        cls.env["ir.config_parameter"].sudo().set_param(
            "dgc_appointment_kiosk.rate_limit_max_hits", "100"
        )
        # Ensure capacity is available regardless of what time the tests run
        cls.env["ir.config_parameter"].sudo().set_param(
            "dgc_appointment_kiosk.hour_start", "0.0"
        )
        cls.env["ir.config_parameter"].sudo().set_param(
            "dgc_appointment_kiosk.hour_end", "24.0"
        )
        cls.kiosk_token = "test-kiosk-token"
        cls.env["ir.config_parameter"].sudo().set_param("dgc_appointment_kiosk.kiosk_token", cls.kiosk_token)

    def setUp(self):
        super().setUp()
        # Clear rate limiter between tests (matches existing test_controllers.py pattern)
        from odoo.addons.dgc_appointment_kiosk.controllers.kiosk import KioskController

        if hasattr(KioskController, "_rate_limits"):
            KioskController._rate_limits.clear()

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
        if response.status_code != 200:
            return {"error": f"Status {response.status_code}"}
        return response.json()

    def _clear_rate_limit(self):
        """Clear rate limit state between API calls within a single test."""
        from odoo.addons.dgc_appointment_kiosk.controllers.kiosk import KioskController

        if hasattr(KioskController, "_rate_limits"):
            KioskController._rate_limits.clear()
        # Also clear ICP-based rate limit keys
        icp = self.env["ir.config_parameter"].sudo()
        params = icp.search([("key", "like", "dgc_kiosk.rl.%")])
        if params:
            params.unlink()

    # 1. test_turn_status_found
    def test_turn_status_found(self):
        """Create active turn for a DNI -> endpoint returns found=True with correct details."""
        # Create a turn via the create endpoint
        result = self._json_rpc(
            f"/kiosk/{self.kiosk_token}/api/turn/create",
            {
                "dni": "50000001",
                "area_id": self.area.id,
            },
        )
        data = result.get("result", {})
        self.assertTrue(data.get("success"), f"Turn creation failed: {data}")
        turn_number = data["turn_number"]

        self._clear_rate_limit()

        # Now check status
        status = self._json_rpc(
            f"/kiosk/{self.kiosk_token}/api/turn/status",
            {"dni": "50000001"},
        )
        status_data = status.get("result", {})
        self.assertTrue(status_data.get("found"))
        self.assertEqual(status_data["turn_number"], turn_number)
        self.assertEqual(status_data["area_name"], "Status Test Area")
        self.assertEqual(status_data["state"], "waiting")
        self.assertIn("position", status_data)
        self.assertIn("estimated_wait_minutes", status_data)

    # 2. test_turn_status_not_found
    def test_turn_status_not_found(self):
        """Query a DNI with no active turn -> found=False."""
        result = self._json_rpc(
            f"/kiosk/{self.kiosk_token}/api/turn/status",
            {"dni": "59999999"},
        )
        data = result.get("result", {})
        self.assertFalse(data.get("found"))

    # 3. test_turn_status_position
    def test_turn_status_position(self):
        """Create multiple turns in area, check position is correct."""
        # Create 3 turns
        for dni in ("50000011", "50000012", "50000013"):
            self._clear_rate_limit()
            result = self._json_rpc(
                f"/kiosk/{self.kiosk_token}/api/turn/create",
                {
                    "dni": dni,
                    "area_id": self.area.id,
                },
            )
            self.assertTrue(
                result.get("result", {}).get("success"),
                f"Failed to create turn for {dni}: {result}",
            )

        self._clear_rate_limit()

        # Check position of the 3rd turn -- it should be position 3
        status = self._json_rpc(
            f"/kiosk/{self.kiosk_token}/api/turn/status",
            {"dni": "50000013"},
        )
        status_data = status.get("result", {})
        self.assertTrue(status_data.get("found"))
        self.assertEqual(status_data["position"], 3)

    # 4. test_turn_status_invalid_dni
    def test_turn_status_invalid_dni(self):
        """Invalid DNI format -> error response."""
        result = self._json_rpc(
            f"/kiosk/{self.kiosk_token}/api/turn/status",
            {"dni": "123"},
        )
        data = result.get("result", {})
        self.assertFalse(data.get("found"))
        self.assertEqual(data.get("error_code"), "INVALID_DNI")

    # 5. test_turn_status_done_turn_not_returned
    def test_turn_status_done_turn_not_returned(self):
        """Turn with state='done' should NOT appear."""
        # Create and complete a turn directly in the DB
        turn = self.env["dgc.appointment.turn"].create(
            {
                "citizen_dni": "50000021",
                "area_id": self.area.id,
            }
        )
        turn.action_call()
        turn.action_serve()
        turn.action_done()
        self.assertEqual(turn.state, "done")

        # Query the status endpoint
        result = self._json_rpc(
            f"/kiosk/{self.kiosk_token}/api/turn/status",
            {"dni": "50000021"},
        )
        data = result.get("result", {})
        self.assertFalse(data.get("found"))
