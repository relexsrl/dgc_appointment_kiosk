import re
from datetime import datetime, timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("standard", "at_install")
class TestPortalBooking(TransactionCase):
    """Tests for the portal DNI/CUIT booking flow.

    These tests validate the server-side logic of:
    - Partner reuse by VAT (DNI/CUIT)
    - New partner creation with VAT
    - DNI validation (server-side)
    - Turn creation from portal bookings
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Turn = cls.env["dgc.appointment.turn"]
        cls.Event = cls.env["calendar.event"]
        cls.Partner = cls.env["res.partner"]
        cls.AppointmentType = cls.env["appointment.type"]

        # DGC area appointment type
        cls.dgc_area = cls.AppointmentType.create({
            "name": "Catastro Portal Test",
            "is_dgc_area": True,
            "dgc_code": "CPRT",
            "dgc_max_counters": 2,
            "category": "recurring",
            "appointment_duration": 0.5,
            "appointment_tz": "America/Argentina/Buenos_Aires",
            "max_schedule_days": 30,
            "min_schedule_hours": 1.0,
        })

        # Non-DGC appointment type
        cls.non_dgc_area = cls.AppointmentType.create({
            "name": "Consulta General Test",
            "category": "recurring",
            "appointment_duration": 1.0,
            "appointment_tz": "America/Argentina/Buenos_Aires",
        })

        # Existing partner with VAT (stored as normalized base DNI)
        cls.existing_partner = cls.Partner.create({
            "name": "Carlos Test",
            "email": "carlos@test.com",
            "vat": "12345678",
        })

    # --- Partner reuse by VAT ---

    def test_partner_reused_by_vat(self):
        """Submitting a DNI that matches an existing partner.vat reuses that partner."""
        result = self.Turn._find_or_create_partner(
            "12345678", "Carlos Otro Nombre", "otro@test.com"
        )
        self.assertEqual(
            result["partner_id"],
            self.existing_partner.id,
            "Should reuse existing partner with matching VAT",
        )
        # Should not create a new partner
        partner_count = self.Partner.search_count([("vat", "=", "12345678")])
        self.assertEqual(partner_count, 1, "No duplicate partner should be created")

    def test_partner_reuse_detects_email_conflict(self):
        """When partner is reused but email differs, email_conflict is flagged."""
        result = self.Turn._find_or_create_partner(
            "12345678", "Carlos Test", "different@test.com"
        )
        self.assertEqual(result["partner_id"], self.existing_partner.id)
        self.assertTrue(result["email_conflict"])

    # --- New partner creation ---

    def test_new_partner_created_with_vat(self):
        """When no partner has the given VAT, a new one is created."""
        result = self.Turn._find_or_create_partner(
            "99887766", "Nueva Persona", "nueva@test.com"
        )
        self.assertTrue(result["partner_id"], "A partner ID should be returned")
        new_partner = self.Partner.browse(result["partner_id"])
        self.assertEqual(new_partner.vat, "99887766")
        self.assertEqual(new_partner.name, "Nueva Persona")
        self.assertEqual(new_partner.email, "nueva@test.com")

    def test_new_partner_without_email(self):
        """Partner creation works without email."""
        result = self.Turn._find_or_create_partner(
            "11223344", "Sin Email", ""
        )
        new_partner = self.Partner.browse(result["partner_id"])
        self.assertEqual(new_partner.vat, "11223344")
        self.assertFalse(new_partner.email)

    # --- DNI validation (server-side) ---

    def test_validate_dni_7_digits(self):
        """7-digit DNI is valid."""
        self.assertTrue(self.Turn._validate_dni("1234567"))

    def test_validate_dni_8_digits(self):
        """8-digit DNI is valid."""
        self.assertTrue(self.Turn._validate_dni("12345678"))

    def test_validate_dni_invalid_short(self):
        """6-digit number is not a valid DNI."""
        self.assertFalse(self.Turn._validate_dni("123456"))

    def test_validate_dni_invalid_alpha(self):
        """Alphabetic characters are not valid."""
        self.assertFalse(self.Turn._validate_dni("abcdefgh"))

    def test_validate_dni_empty(self):
        """Empty string is not valid."""
        self.assertFalse(self.Turn._validate_dni(""))

    def test_validate_cuit_valid(self):
        """Valid 11-digit CUIT with correct checksum."""
        # CUIT 20-12345678-6 has digits 20123456786 (check digit = 6)
        self.assertTrue(self.Turn._validate_cuit("20123456786"))

    def test_validate_cuit_invalid_checksum(self):
        """Invalid CUIT checksum is rejected."""
        self.assertFalse(self.Turn._validate_cuit("20123456780"))

    def test_validate_dni_11_digits_valid_cuit(self):
        """11-digit input is validated as CUIT."""
        self.assertTrue(self.Turn._validate_dni("20123456786"))

    def test_validate_dni_11_digits_invalid_cuit(self):
        """11-digit input with bad checksum is rejected."""
        self.assertFalse(self.Turn._validate_dni("20123456780"))

    # --- Turn creation from portal booking ---

    def test_portal_booking_creates_turn_with_vat(self):
        """Calendar event for DGC area with partner having VAT creates turn with citizen_dni."""
        start = datetime.now() + timedelta(days=1)
        event = self.Event.create({
            "name": "Portal Booking Test",
            "start": start,
            "stop": start + timedelta(hours=1),
            "appointment_type_id": self.dgc_area.id,
            "appointment_booker_id": self.existing_partner.id,
            "partner_ids": [(4, self.existing_partner.id)],
        })
        turn = event.dgc_turn_id
        self.assertTrue(turn, "A DGC turn should be created")
        self.assertEqual(turn.source, "portal")
        self.assertEqual(turn.citizen_dni, "12345678")
        self.assertEqual(turn.partner_id, self.existing_partner)
        self.assertEqual(turn.area_id, self.dgc_area)
        self.assertEqual(turn.calendar_event_id, event)

    def test_portal_booking_no_turn_for_non_dgc(self):
        """Calendar event for non-DGC area does not create a turn."""
        partner = self.Partner.create({
            "name": "Test Non-DGC",
            "email": "nondgc@test.com",
            "vat": "55667788",
        })
        start = datetime.now() + timedelta(days=1)
        event = self.Event.create({
            "name": "Non-DGC Booking",
            "start": start,
            "stop": start + timedelta(hours=1),
            "appointment_type_id": self.non_dgc_area.id,
            "appointment_booker_id": partner.id,
            "partner_ids": [(4, partner.id)],
        })
        self.assertFalse(
            event.dgc_turn_id,
            "No DGC turn should be created for non-DGC appointment types",
        )

    def test_portal_booking_partner_without_vat_gets_placeholder(self):
        """Partner without VAT gets a PORTAL-{id} placeholder as citizen_dni."""
        partner = self.Partner.create({
            "name": "Sin DNI Portal",
            "email": "sindni@test.com",
        })
        start = datetime.now() + timedelta(days=1)
        event = self.Event.create({
            "name": "Portal No VAT",
            "start": start,
            "stop": start + timedelta(hours=1),
            "appointment_type_id": self.dgc_area.id,
            "appointment_booker_id": partner.id,
            "partner_ids": [(4, partner.id)],
        })
        turn = event.dgc_turn_id
        self.assertTrue(turn)
        self.assertTrue(
            turn.citizen_dni.startswith("PORTAL-"),
            f"Expected placeholder DNI, got '{turn.citizen_dni}'",
        )

    def test_portal_turn_sends_bus_notification(self):
        """Portal booking sends a bus notification with action='portal_booking'."""
        with patch.object(type(self.env["bus.bus"]), "_sendone") as mock_send:
            start = datetime.now() + timedelta(days=1)
            event = self.Event.create({
                "name": "Portal Notify Test",
                "start": start,
                "stop": start + timedelta(hours=1),
                "appointment_type_id": self.dgc_area.id,
                "appointment_booker_id": self.existing_partner.id,
                "partner_ids": [(4, self.existing_partner.id)],
            })
            turn = event.dgc_turn_id
            self.assertTrue(turn)
            portal_calls = [
                call for call in mock_send.call_args_list
                if len(call[0]) >= 3
                and isinstance(call[0][2], dict)
                and call[0][2].get("action") == "portal_booking"
            ]
            self.assertTrue(
                portal_calls,
                "A bus notification with action='portal_booking' should be sent",
            )

    # --- DNI/CUIT normalization ---

    def test_normalize_dni_7_digits(self):
        """7-digit DNI is returned unchanged."""
        self.assertEqual(self.Turn._normalize_dni("1234567"), "1234567")

    def test_normalize_dni_8_digits(self):
        """8-digit DNI is returned unchanged."""
        self.assertEqual(self.Turn._normalize_dni("12345678"), "12345678")

    def test_normalize_cuit_extracts_base_dni(self):
        """CUIT 20-12345678-6 normalizes to base DNI 12345678."""
        self.assertEqual(self.Turn._normalize_dni("20123456786"), "12345678")

    def test_normalize_cuit_with_hyphens(self):
        """CUIT with hyphens is stripped and normalized."""
        self.assertEqual(self.Turn._normalize_dni("20-12345678-6"), "12345678")

    def test_normalize_cuit_strips_leading_zeros(self):
        """CUIT with leading zeros in base DNI strips them."""
        # CUIT 27-00123456-X -> base = 00123456 -> stripped = 123456
        self.assertEqual(self.Turn._normalize_dni("27001234564"), "123456")

    def test_normalize_cuit_all_zeros_returns_zero(self):
        """CUIT where base is all zeros returns '0'."""
        # digits[2:10] = "00000000" -> lstrip("0") = "" -> "0"
        self.assertEqual(self.Turn._normalize_dni("20000000004"), "0")

    def test_normalize_empty_returns_empty(self):
        """Empty string returns empty."""
        self.assertEqual(self.Turn._normalize_dni(""), "")

    def test_normalize_none_returns_none(self):
        """None returns None."""
        self.assertIsNone(self.Turn._normalize_dni(None))

    def test_cuit_and_dni_resolve_to_same_partner(self):
        """CUIT 20-12345678-6 and DNI 12345678 resolve to same partner."""
        # existing_partner has vat="12345678"
        result_dni = self.Turn._find_or_create_partner(
            "12345678", "Test DNI", "test@test.com"
        )
        result_cuit = self.Turn._find_or_create_partner(
            "20123456786", "Test CUIT", "test2@test.com"
        )
        self.assertEqual(
            result_dni["partner_id"],
            result_cuit["partner_id"],
            "DNI and CUIT should resolve to the same partner",
        )
        self.assertEqual(result_dni["partner_id"], self.existing_partner.id)

    def test_turn_created_with_cuit_stores_normalized_dni(self):
        """Turn created with CUIT stores normalized base DNI in citizen_dni."""
        turn = self.Turn.create({
            "citizen_dni": "20123456786",
            "area_id": self.dgc_area.id,
            "source": "kiosk",
        })
        self.assertEqual(
            turn.citizen_dni, "12345678",
            "citizen_dni should be normalized to base DNI",
        )

    def test_search_by_dni_finds_turn_created_with_cuit(self):
        """Searching by DNI 12345678 finds a turn created with CUIT 20-12345678-6."""
        turn = self.Turn.create({
            "citizen_dni": "20123456786",
            "area_id": self.dgc_area.id,
            "source": "kiosk",
        })
        found = self.Turn.search([
            ("citizen_dni", "=", "12345678"),
            ("id", "=", turn.id),
        ])
        self.assertEqual(found.id, turn.id)

    def test_partner_created_via_cuit_has_normalized_vat(self):
        """Partner created via CUIT has vat set to normalized base DNI."""
        result = self.Turn._find_or_create_partner(
            "27287654321", "CUIT Partner", "cuit@test.com"
        )
        partner = self.Partner.browse(result["partner_id"])
        self.assertEqual(
            partner.vat, "28765432",
            "Partner VAT should be the normalized base DNI from the CUIT",
        )
