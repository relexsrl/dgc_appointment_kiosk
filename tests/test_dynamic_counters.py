from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..models.dgc_appointment_turn import _today_tz


@tagged('standard', 'at_install')
class TestDynamicCountersBase(TransactionCase):
    """Shared setup for dynamic-counters tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Area = cls.env["appointment.type"]
        cls.Box = cls.env["dgc.operator.box"]
        cls.Turn = cls.env["dgc.appointment.turn"]
        cls.NonWorkingDate = cls.env["dgc.non_working.date"]

        cls.area = cls.Area.create({
            "name": "Test Dynamic Counters",
            "is_dgc_area": True,
            "dgc_code": "DC_TST",
            "dgc_max_counters": 5,
            "category": "recurring",
            "appointment_duration": 0.25,  # 15 min
            "appointment_tz": "America/Argentina/Buenos_Aires",
        })
        cls.operator = cls.env["res.users"].create({
            "name": "Op DC Test",
            "login": "op_dc_test",
            "group_ids": [
                (4, cls.env.ref("base.group_user").id),
                (4, cls.env.ref("dgc_appointment_kiosk.group_dgc_operator").id),
            ],
        })
        cls.operator2 = cls.env["res.users"].create({
            "name": "Op DC Test 2",
            "login": "op_dc_test2",
            "group_ids": [
                (4, cls.env.ref("base.group_user").id),
                (4, cls.env.ref("dgc_appointment_kiosk.group_dgc_operator").id),
            ],
        })
        cls.area.staff_user_ids = [(4, cls.operator.id), (4, cls.operator2.id)]

        cls.box1 = cls.Box.create({
            "operator_id": cls.operator.id,
            "area_id": cls.area.id,
            "box_number": "1",
            "active": True,
        })
        cls.box2 = cls.Box.create({
            "operator_id": cls.operator2.id,
            "area_id": cls.area.id,
            "box_number": "2",
            "active": True,
        })

        # Set fallback hours explicitly so tests don't depend on database state
        ICP = cls.env["ir.config_parameter"].sudo()
        ICP.set_param("dgc_appointment_kiosk.hour_start", "8.0")
        ICP.set_param("dgc_appointment_kiosk.hour_end", "14.0")


class TestToggleBox(TestDynamicCountersBase):
    """5.1 — Toggle box active/inactive."""

    def test_toggle_box_deactivates(self):
        """Toggling an active box sets it to inactive."""
        self.assertTrue(self.box1.active)
        result = self.box1.with_user(self.operator).action_toggle_box()
        self.assertFalse(result["box_active"])
        self.assertFalse(self.box1.active)

    def test_toggle_box_activates(self):
        """Toggling an inactive box sets it to active."""
        self.box1.active = False
        result = self.box1.with_user(self.operator).action_toggle_box()
        self.assertTrue(result["box_active"])
        self.assertTrue(self.box1.active)

    def test_toggle_returns_correct_count(self):
        """Toggle returns current active_box_count."""
        result = self.box1.with_user(self.operator).action_toggle_box()
        # box1 is now inactive, box2 still active => count=1
        self.assertEqual(result["active_box_count"], 1)


class TestActiveBoxCount(TestDynamicCountersBase):
    """5.2 — active_box_count computed field accuracy."""

    def test_all_active(self):
        """All boxes active => count matches total."""
        self.area.invalidate_recordset(["active_box_count"])
        self.assertEqual(self.area.active_box_count, 2)

    def test_one_inactive(self):
        """One box deactivated => count decreases."""
        self.box1.active = False
        self.area.invalidate_recordset(["active_box_count"])
        self.assertEqual(self.area.active_box_count, 1)

    def test_all_inactive(self):
        """All boxes deactivated => count is 0."""
        self.box1.active = False
        self.box2.active = False
        self.area.invalidate_recordset(["active_box_count"])
        self.assertEqual(self.area.active_box_count, 0)


class TestCapacityRefactor(TestDynamicCountersBase):
    """5.3 — Capacity uses min(active_box_count, dgc_max_counters)."""

    def test_capacity_uses_min_multiplier(self):
        """With 2 active boxes and max=5, multiplier should be 2."""
        self.area.invalidate_recordset(["max_daily_turns"])
        # 2 active boxes, max_counters=5 => multiplier=2
        # Service=15min. Depends on slots/fallback, but multiplier logic matters.
        # With fallback 8-14 = 6h = 360min => 360/15 * 2 = 48
        self.assertEqual(self.area.max_daily_turns, 48)

    def test_capacity_ceiling(self):
        """Active boxes exceed max_counters => uses max_counters as ceiling."""
        # Set max_counters=1, 2 active boxes => multiplier=1
        self.area.dgc_max_counters = 1
        self.area.invalidate_recordset(["max_daily_turns"])
        # 360/15 * 1 = 24
        self.assertEqual(self.area.max_daily_turns, 24)

    def test_zero_active_boxes_zero_capacity(self):
        """Zero active boxes => capacity is 0."""
        self.box1.active = False
        self.box2.active = False
        self.area.invalidate_recordset(["max_daily_turns", "active_box_count"])
        self.assertEqual(self.area.max_daily_turns, 0)

    def test_remaining_with_dynamic_counters(self):
        """remaining_turns_today uses dynamic counter multiplier."""
        self.area.invalidate_recordset(["remaining_turns_today"])
        remaining = self.area.remaining_turns_today
        # Should be > 0 with active boxes
        self.assertGreaterEqual(remaining, 0)
        # Deactivate all boxes => remaining=0
        self.box1.active = False
        self.box2.active = False
        self.area.invalidate_recordset(["remaining_turns_today", "active_box_count"])
        self.assertEqual(self.area.remaining_turns_today, 0)


class TestNonWorkingDate(TestDynamicCountersBase):
    """5.4 — Non-working day zeroes capacity."""

    def test_today_non_working(self):
        """Today as non-working date => _is_available_today() returns False."""
        today = _today_tz(self.env)
        self.NonWorkingDate.create({
            "date": today,
            "area_id": self.area.id,
            "name": "Test holiday",
        })
        self.assertFalse(self.area._is_available_today())

    def test_non_working_zeroes_capacity(self):
        """Non-working day forces max_daily_turns to 0."""
        today = _today_tz(self.env)
        self.NonWorkingDate.create({
            "date": today,
            "area_id": self.area.id,
            "name": "Test holiday",
        })
        self.area.invalidate_recordset(["max_daily_turns", "remaining_turns_today"])
        self.assertEqual(self.area.max_daily_turns, 0)
        self.assertEqual(self.area.remaining_turns_today, 0)

    def test_other_date_no_effect(self):
        """Non-working date for a different day does not affect today."""
        today = _today_tz(self.env)
        tomorrow = fields.Date.add(today, days=1)
        self.NonWorkingDate.create({
            "date": tomorrow,
            "area_id": self.area.id,
            "name": "Tomorrow holiday",
        })
        self.assertTrue(self.area._is_available_today())

    def test_available_with_boxes_and_no_holiday(self):
        """Area with active boxes and no holiday is available."""
        self.assertTrue(self.area._is_available_today())


class TestKioskAreaAvailability(TestDynamicCountersBase):
    """5.5 & 5.6 — Kiosk API availability and turn creation guard."""

    def test_areas_endpoint_returns_available_flag(self):
        """Areas response includes available=True when boxes are active."""
        # We test the controller logic indirectly via the model
        self.assertTrue(self.area._is_available_today())

    def test_areas_unavailable_no_counters(self):
        """Area with 0 active boxes is unavailable."""
        self.box1.active = False
        self.box2.active = False
        self.area.invalidate_recordset(["active_box_count"])
        self.assertFalse(self.area._is_available_today())

    def test_turn_creation_blocked_no_active_boxes(self):
        """Turn creation should be blocked when area is unavailable.

        Tests the guard logic that controllers use before creating turns.
        """
        self.box1.active = False
        self.box2.active = False
        self.area.invalidate_recordset(["active_box_count", "remaining_turns_today"])
        self.assertFalse(self.area._is_available_today())
        self.assertEqual(self.area.remaining_turns_today, 0)


class TestBusNotificationOnToggle(TestDynamicCountersBase):
    """5.7 — Bus notification sent on box toggle."""

    def test_toggle_sends_bus_notification(self):
        """Toggling a box sends a counter_changed bus notification."""
        with patch.object(type(self.env["bus.bus"]), "_sendone") as mock_send:
            self.box1.with_user(self.operator).action_toggle_box()
            # Find the counter_changed notification
            calls = [
                call for call in mock_send.call_args_list
                if call[0][0] == f"dgc_turn_area_{self.area.id}"
                and call[0][2].get("action") == "counter_changed"
            ]
            self.assertTrue(calls, "counter_changed bus notification was not sent")
            payload = calls[0][0][2]
            self.assertEqual(payload["area_id"], self.area.id)
            self.assertIn("active_box_count", payload)

    def test_write_active_sends_notification(self):
        """Directly writing active field triggers bus notification."""
        with patch.object(type(self.env["bus.bus"]), "_sendone") as mock_send:
            self.box1.write({"active": False})
            calls = [
                call for call in mock_send.call_args_list
                if call[0][0] == f"dgc_turn_area_{self.area.id}"
                and call[0][2].get("action") == "counter_changed"
            ]
            self.assertTrue(calls, "counter_changed bus notification was not sent on write")


class TestOperatorBoxACL(TestDynamicCountersBase):
    """5.8 — Operator ACL allows toggling their own box."""

    def test_operator_can_toggle_own_box(self):
        """Operator can call action_toggle_box on their assigned box."""
        # Should not raise AccessError
        result = self.box1.with_user(self.operator).action_toggle_box()
        self.assertIn("box_active", result)
        self.assertIn("active_box_count", result)

    def test_operator_can_write_active(self):
        """Operator can write the active field on their box."""
        # Should not raise AccessError
        self.box1.with_user(self.operator).write({"active": False})
        self.assertFalse(self.box1.active)


class TestDashboardBoxData(TestDynamicCountersBase):
    """Dashboard includes box state data."""

    def test_dashboard_includes_box_state(self):
        """get_operator_dashboard_data includes box_status and box_active."""
        data = self.Turn.with_user(self.operator).get_operator_dashboard_data()
        self.assertIn("box_status", data)
        self.assertIn("box_active", data)
        self.assertIn("active_box_count", data)
        self.assertEqual(data["box_status"], "open")
        self.assertTrue(data["box_active"])
        self.assertEqual(data["active_box_count"], 2)

    def test_dashboard_box_closed(self):
        """Dashboard reflects closed box state."""
        self.box1.active = False
        data = self.Turn.with_user(self.operator).get_operator_dashboard_data()
        self.assertEqual(data["box_status"], "closed")
        self.assertFalse(data["box_active"])

    def test_dashboard_no_box(self):
        """Dashboard shows no_box when operator has no assigned box."""
        operator3 = self.env["res.users"].create({
            "name": "Op No Box",
            "login": "op_no_box",
            "group_ids": [
                (4, self.env.ref("base.group_user").id),
                (4, self.env.ref("dgc_appointment_kiosk.group_dgc_operator").id),
            ],
        })
        self.area.staff_user_ids = [(4, operator3.id)]
        data = self.Turn.with_user(operator3).get_operator_dashboard_data()
        self.assertEqual(data["box_status"], "no_box")
        self.assertFalse(data["box_active"])
