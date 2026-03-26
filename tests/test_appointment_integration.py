from datetime import datetime, timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('standard', 'at_install')
class TestAppointmentIntegration(TransactionCase):
    """Tests for the portal booking -> DGC turn bridge."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Turn = cls.env["dgc.appointment.turn"]
        cls.Event = cls.env["calendar.event"]
        cls.AppointmentType = cls.env["appointment.type"]

        # Create an appointment type that IS a DGC area
        cls.area_cat = cls.AppointmentType.create(
            {
                "name": "Turno Catastro Portal",
                "is_dgc_area": True,
                "dgc_code": "CATI",
                "dgc_max_counters": 2,
                "category": "recurring",
                "appointment_duration": 0.5,
                "appointment_tz": "America/Argentina/Buenos_Aires",
                "max_schedule_days": 30,
                "min_schedule_hours": 1.0,
            }
        )
        # Alias for tests that reference appt_type
        cls.appt_type = cls.area_cat

        # An appointment type NOT flagged as a DGC area
        cls.appt_type_other = cls.AppointmentType.create(
            {
                "name": "Consulta General",
                "category": "recurring",
                "appointment_duration": 1.0,
                "appointment_tz": "America/Argentina/Buenos_Aires",
            }
        )

        # A DGC area without portal booking (standalone kiosk area)
        cls.area_geo = cls.AppointmentType.create(
            {
                "name": "Geografía Int",
                "is_dgc_area": True,
                "dgc_code": "GEOI",
                "dgc_max_counters": 1,
                "category": "recurring",
                "appointment_duration": 0.25,
                "appointment_tz": "America/Argentina/Buenos_Aires",
            }
        )

        # Active operator boxes so capacity is non-zero
        op_group = cls.env.ref("dgc_appointment_kiosk.group_dgc_operator")
        base_group = cls.env.ref("base.group_user")
        Box = cls.env["dgc.operator.box"]

        cls.operator_cat1 = cls.env["res.users"].create({
            "name": "Op Cat 1", "login": "op_cat_integ1",
            "group_ids": [(4, base_group.id), (4, op_group.id)],
        })
        cls.operator_cat2 = cls.env["res.users"].create({
            "name": "Op Cat 2", "login": "op_cat_integ2",
            "group_ids": [(4, base_group.id), (4, op_group.id)],
        })
        cls.area_cat.staff_user_ids = [(4, cls.operator_cat1.id), (4, cls.operator_cat2.id)]
        Box.create({"operator_id": cls.operator_cat1.id, "area_id": cls.area_cat.id, "box_number": "1", "active": True})
        Box.create({"operator_id": cls.operator_cat2.id, "area_id": cls.area_cat.id, "box_number": "2", "active": True})

        cls.operator_geo = cls.env["res.users"].create({
            "name": "Op Geo", "login": "op_geo_integ",
            "group_ids": [(4, base_group.id), (4, op_group.id)],
        })
        cls.area_geo.staff_user_ids = [(4, cls.operator_geo.id)]
        Box.create({"operator_id": cls.operator_geo.id, "area_id": cls.area_geo.id, "box_number": "1", "active": True})

        # Set wide fallback hours so turn creation always has capacity
        ICP = cls.env["ir.config_parameter"].sudo()
        ICP.set_param("dgc_appointment_kiosk.hour_start", "0.0")
        ICP.set_param("dgc_appointment_kiosk.hour_end", "24.0")

        # Partner with VAT (DNI)
        cls.partner_with_vat = cls.env["res.partner"].create(
            {
                "name": "Juan Pérez",
                "email": "juan@example.com",
                "vat": "20345678901",
            }
        )

        # Partner without VAT
        cls.partner_no_vat = cls.env["res.partner"].create(
            {
                "name": "María García",
                "email": "maria@example.com",
            }
        )

        # Create appointment slots for the appointment type (Monday to Friday)
        cls.slots = cls.env["appointment.slot"]
        for weekday in ["1", "2", "3", "4", "5"]:
            cls.slots |= cls.env["appointment.slot"].create(
                {
                    "appointment_type_id": cls.appt_type.id,
                    "weekday": weekday,
                    "start_hour": 8.0,
                    "end_hour": 14.0,
                    "slot_type": "recurring",
                }
            )

    def _create_calendar_event(self, appointment_type=None, partner=None, **kwargs):
        """Helper to create a calendar.event simulating a portal booking."""
        partner = partner or self.partner_with_vat
        start = kwargs.pop("start", datetime.now() + timedelta(days=1))
        stop = kwargs.pop("stop", start + timedelta(hours=1))
        vals = {
            "name": "Portal Appointment",
            "start": start,
            "stop": stop,
            "partner_ids": [(4, partner.id)],
        }
        if appointment_type is not None:
            vals["appointment_type_id"] = appointment_type.id
            vals["appointment_booker_id"] = partner.id
        vals.update(kwargs)
        return self.Event.create(vals)

    def test_portal_booking_creates_turn(self):
        """Create a calendar.event with a DGC appointment type -> a turn is created."""
        event = self._create_calendar_event(appointment_type=self.appt_type)
        self.assertTrue(event.dgc_turn_id, "A DGC turn should have been created for the event")
        turn = event.dgc_turn_id
        self.assertEqual(turn.source, "portal")
        self.assertEqual(turn.area_id, self.area_cat)

    def test_portal_booking_ignored_for_other_types(self):
        """Calendar event with a non-DGC appointment type -> no turn created."""
        event = self._create_calendar_event(appointment_type=self.appt_type_other)
        self.assertFalse(event.dgc_turn_id, "No DGC turn should be created for non-DGC appointment types")

    def test_portal_booking_links_calendar_event(self):
        """Turn and event are bidirectionally linked."""
        event = self._create_calendar_event(appointment_type=self.appt_type)
        turn = event.dgc_turn_id
        self.assertTrue(turn)
        self.assertEqual(turn.calendar_event_id, event)
        self.assertEqual(event.dgc_turn_id, turn)

    def test_portal_booking_sets_partner(self):
        """Turn partner matches the event's booker."""
        event = self._create_calendar_event(
            appointment_type=self.appt_type,
            partner=self.partner_with_vat,
        )
        turn = event.dgc_turn_id
        self.assertEqual(turn.partner_id, self.partner_with_vat)
        self.assertEqual(turn.citizen_name, self.partner_with_vat.name)
        self.assertEqual(turn.citizen_email, self.partner_with_vat.email)

    def test_portal_booking_no_vat_uses_placeholder(self):
        """Partner without VAT -> turn.citizen_dni starts with 'PORTAL-'."""
        event = self._create_calendar_event(
            appointment_type=self.appt_type,
            partner=self.partner_no_vat,
        )
        turn = event.dgc_turn_id
        self.assertTrue(turn)
        self.assertTrue(
            turn.citizen_dni.startswith("PORTAL-"),
            f"Expected citizen_dni to start with 'PORTAL-', got '{turn.citizen_dni}'",
        )

    def test_portal_booking_sends_notification(self):
        """Bus notification is sent when a portal turn is created."""
        with patch.object(type(self.env["bus.bus"]), "_sendone") as mock_send:
            event = self._create_calendar_event(appointment_type=self.appt_type)
            turn = event.dgc_turn_id
            self.assertTrue(turn)
            # Find the portal_booking notification call
            portal_calls = [
                call
                for call in mock_send.call_args_list
                if len(call[0]) >= 3 and isinstance(call[0][2], dict) and call[0][2].get("action") == "portal_booking"
            ]
            self.assertTrue(portal_calls, "A bus notification with action='portal_booking' should have been sent")
            payload = portal_calls[0][0][2]
            self.assertEqual(payload["turn_id"], turn.id)
            self.assertEqual(payload["area_id"], self.area_cat.id)

    def test_appointment_type_without_dgc_flag_works(self):
        """Creating a turn via kiosk for a DGC area (no portal booking) still works normally."""
        turn = self.Turn.create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
                "source": "kiosk",
            }
        )
        self.assertTrue(turn.exists())
        self.assertEqual(turn.source, "kiosk")
        self.assertEqual(turn.state, "waiting")
        self.assertTrue(turn.turn_number.startswith("GEOI-"))

    def test_turn_source_tracking(self):
        """Verify source is set correctly for different turn origins."""
        # Kiosk turn
        turn_kiosk = self.Turn.create(
            {
                "citizen_dni": "11111111",
                "area_id": self.area_geo.id,
                "source": "kiosk",
            }
        )
        self.assertEqual(turn_kiosk.source, "kiosk")

        # Manual turn
        turn_manual = self.Turn.create(
            {
                "citizen_dni": "22222222",
                "area_id": self.area_geo.id,
                "source": "manual",
            }
        )
        self.assertEqual(turn_manual.source, "manual")

        # Portal turn (via calendar event bridge)
        event = self._create_calendar_event(appointment_type=self.appt_type)
        turn_portal = event.dgc_turn_id
        self.assertEqual(turn_portal.source, "portal")

    def test_slot_capacity_from_appointment_type(self):
        """Area with appointment slots -> max_daily_turns is computed from area config.

        The max_daily_turns for an area is computed from appointment_duration (hours)
        and dgc_max_counters, using slots or the global config hours as fallback.
        """
        self.env["ir.config_parameter"].set_param("dgc_appointment_kiosk.hour_start", "8.0")
        self.env["ir.config_parameter"].set_param("dgc_appointment_kiosk.hour_end", "14.0")
        self.area_cat.invalidate_recordset()
        # 6 hours * 60 min / (0.5 hrs * 60 = 30 min) * 2 counters = 24
        self.assertEqual(self.area_cat.max_daily_turns, 24)
        # Verify the appointment type has slots
        self.assertTrue(
            self.appt_type.slot_ids,
            "Appointment type should have slot records",
        )
        self.assertEqual(len(self.appt_type.slot_ids), 5, "Should have 5 weekday slots")

    def test_event_without_appointment_type_ignored(self):
        """Calendar event without any appointment_type_id -> no turn created."""
        event = self._create_calendar_event(appointment_type=None)
        self.assertFalse(event.dgc_turn_id)

    def test_event_without_partner_ignored(self):
        """Calendar event with DGC appointment type but no partners -> no turn created."""
        start = datetime.now() + timedelta(days=1)
        event = self.Event.create(
            {
                "name": "Empty Event",
                "start": start,
                "stop": start + timedelta(hours=1),
                "appointment_type_id": self.appt_type.id,
                "partner_ids": [],
            }
        )
        self.assertFalse(event.dgc_turn_id)

    def test_skip_turn_creation_context(self):
        """Context flag dgc_skip_turn_creation prevents turn auto-creation."""
        event = self.Event.with_context(dgc_skip_turn_creation=True).create(
            {
                "name": "Skipped Event",
                "start": datetime.now() + timedelta(days=1),
                "stop": datetime.now() + timedelta(days=1, hours=1),
                "appointment_type_id": self.appt_type.id,
                "appointment_booker_id": self.partner_with_vat.id,
                "partner_ids": [(4, self.partner_with_vat.id)],
            }
        )
        self.assertFalse(event.dgc_turn_id, "Turn creation should be skipped with context flag")

    def test_calendar_event_delete_cancels_turn(self):
        """Deleting a calendar event linked to a DGC turn cancels the turn (no_show)."""
        event = self._create_calendar_event(appointment_type=self.appt_type)
        turn = event.dgc_turn_id
        self.assertTrue(turn, "A turn should have been created")
        self.assertIn(turn.state, ("waiting", "calling", "new"), "Turn should be in a pending state")

        # Delete the event
        event.unlink()
        turn.invalidate_recordset()
        self.assertEqual(turn.state, "no_show", "Turn state should become no_show after event deletion")

    def test_calendar_event_archive_cancels_turn(self):
        """Archiving a calendar event (active=False) cancels the linked DGC turn."""
        event = self._create_calendar_event(appointment_type=self.appt_type)
        turn = event.dgc_turn_id
        self.assertTrue(turn, "A turn should have been created")
        self.assertIn(turn.state, ("waiting", "calling", "new"), "Turn should be in a pending state")

        # Archive the event
        event.write({"active": False})
        turn.invalidate_recordset()
        self.assertEqual(turn.state, "no_show", "Turn state should become no_show after event archival")

    def test_done_turn_not_affected_by_event_delete(self):
        """A completed turn is not affected by deleting its calendar event."""
        event = self._create_calendar_event(appointment_type=self.appt_type)
        turn = event.dgc_turn_id
        self.assertTrue(turn, "A turn should have been created")

        # Complete the turn through the full workflow
        turn.action_call()
        turn.action_serve()
        turn.action_done()
        self.assertEqual(turn.state, "done")

        # Delete the event — turn should remain done
        event.unlink()
        turn.invalidate_recordset()
        self.assertEqual(turn.state, "done", "Completed turn state should remain done after event deletion")
