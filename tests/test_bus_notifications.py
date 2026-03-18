from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestBusNotifications(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.area = cls.env["dgc.appointment.area"].create({
            "name": "Geografía",
            "code": "GEO",
        })
        cls.operator = cls.env["res.users"].create({
            "name": "Op Bus Test",
            "login": "op_bus_test",
            "groups_id": [(4, cls.env.ref("dgc_appointment_kiosk.group_dgc_operator").id)],
            "dgc_area_ids": [(4, cls.area.id)],
        })

    def test_call_sends_bus_notification(self):
        """Calling a turn sends a bus notification."""
        turn = self.env["dgc.appointment.turn"].create({
            "citizen_dni": "12345678",
            "area_id": self.area.id,
        })
        with patch.object(type(self.env["bus.bus"]), "_sendone") as mock_send:
            turn.with_user(self.operator).action_call()
            mock_send.assert_called_once()
            args = mock_send.call_args
            channel = args[0][0]
            notification_type = args[0][1]
            self.assertEqual(channel, f"dgc_turn_area_{self.area.id}")
            self.assertEqual(notification_type, "dgc_turn_update")

    def test_notification_payload_structure(self):
        """Bus notification payload has expected fields."""
        turn = self.env["dgc.appointment.turn"].create({
            "citizen_dni": "12345678",
            "area_id": self.area.id,
        })
        with patch.object(type(self.env["bus.bus"]), "_sendone") as mock_send:
            turn.with_user(self.operator).action_call()
            payload = mock_send.call_args[0][2]
            self.assertIn("action", payload)
            self.assertIn("turn_id", payload)
            self.assertIn("turn_number", payload)
            self.assertIn("state", payload)
            self.assertEqual(payload["action"], "call")

    def test_derivation_notifies_destination_area(self):
        """Derivation sends notification to destination area channel."""
        area_cat = self.env["dgc.appointment.area"].create({
            "name": "Catastro",
            "code": "CAT",
        })
        self.operator.dgc_area_ids = [(4, area_cat.id)]
        turn = self.env["dgc.appointment.turn"].create({
            "citizen_dni": "12345678",
            "area_id": self.area.id,
        })
        wizard = self.env["dgc.turn.derive.wizard"].with_user(self.operator).create({
            "turn_id": turn.id,
            "to_area_id": area_cat.id,
            "reason": "Test derivation",
        })
        with patch.object(type(self.env["bus.bus"]), "_sendone") as mock_send:
            wizard.action_derive()
            # Check that at least one call was to the destination area channel
            channels = [call[0][0] for call in mock_send.call_args_list]
            self.assertIn(f"dgc_turn_area_{area_cat.id}", channels)
