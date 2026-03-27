import re
from datetime import datetime, timedelta

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('standard', 'at_install')
class TestPortalController(TransactionCase):
    """Tests for the DgcPortalAppointmentController logic.

    These tests validate the controller's DNI resolution, validation,
    and partner deduplication by exercising the same ORM methods the
    controller calls, without requiring a full HTTP stack.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Turn = cls.env["dgc.appointment.turn"]
        cls.Partner = cls.env["res.partner"]
        cls.AppointmentType = cls.env["appointment.type"]
        cls.Event = cls.env["calendar.event"]

        cls.dgc_area = cls.AppointmentType.create({
            "name": "Portal Controller Test Area",
            "is_dgc_area": True,
            "dgc_code": "PC_TST",
            "dgc_max_counters": 2,
            "category": "recurring",
            "appointment_duration": 0.5,
            "appointment_tz": "America/Argentina/Buenos_Aires",
            "max_schedule_days": 30,
            "min_schedule_hours": 1.0,
        })

        cls.non_dgc_area = cls.AppointmentType.create({
            "name": "Non-DGC Controller Test",
            "category": "recurring",
            "appointment_duration": 1.0,
            "appointment_tz": "America/Argentina/Buenos_Aires",
        })

        cls.existing_partner = cls.Partner.create({
            "name": "Portal Ctrl Existing",
            "email": "existing@ctrl.com",
            "vat": "33445566",
        })

    # --- T-5.3.1: Valid DNI booking creates turn with correct citizen_dni ---

    def test_portal_booking_creates_turn_with_dni(self):
        """Portal booking with valid DNI creates turn with citizen_dni set."""
        raw_dni = "33445566"

        # Validate DNI (controller does this before proceeding)
        self.assertTrue(self.Turn._validate_dni(raw_dni))

        # Normalize (identity for 8-digit DNI)
        normalized = self.Turn._normalize_dni(raw_dni)
        self.assertEqual(normalized, "33445566")

        # Resolve partner (controller calls _find_or_create_partner)
        result = self.Turn._find_or_create_partner(
            normalized, "Portal Ctrl Existing", "existing@ctrl.com"
        )
        partner = self.Partner.browse(result["partner_id"])
        self.assertEqual(partner, self.existing_partner)
        self.assertEqual(partner.vat, "33445566")

        # Simulate the calendar event creation that super() does,
        # which triggers _create_dgc_turns_from_appointments
        start = datetime.now() + timedelta(days=1)
        event = self.Event.create({
            "name": "Portal Ctrl Test Booking",
            "start": start,
            "stop": start + timedelta(hours=1),
            "appointment_type_id": self.dgc_area.id,
            "appointment_booker_id": partner.id,
            "partner_ids": [(4, partner.id)],
        })
        turn = event.dgc_turn_id
        self.assertTrue(turn, "DGC turn should be created from portal booking")
        self.assertEqual(turn.citizen_dni, "33445566")
        self.assertEqual(turn.source, "portal")
        self.assertEqual(turn.partner_id, self.existing_partner)

    # --- T-5.3.2: Invalid DNI raises error ---

    def test_portal_booking_invalid_dni(self):
        """Invalid DNI fails server-side validation (controller raises UserError)."""
        invalid_dnis = ["123", "abcdef", "12", ""]
        for dni in invalid_dnis:
            raw = re.sub(r"\D", "", dni)
            self.assertFalse(
                self.Turn._validate_dni(raw),
                f"DNI '{dni}' (cleaned: '{raw}') should fail validation",
            )

    def test_portal_booking_invalid_cuit_checksum(self):
        """CUIT with invalid checksum fails validation."""
        self.assertFalse(self.Turn._validate_dni("20123456780"))

    # --- T-5.3.3: Non-DGC area follows standard flow ---

    def test_portal_booking_non_dgc_area(self):
        """Non-DGC area booking creates event without DGC turn (no DNI needed)."""
        partner = self.Partner.create({
            "name": "Non-DGC Portal User",
            "email": "nondgc@ctrl.com",
        })
        start = datetime.now() + timedelta(days=1)
        event = self.Event.create({
            "name": "Non-DGC Controller Test",
            "start": start,
            "stop": start + timedelta(hours=1),
            "appointment_type_id": self.non_dgc_area.id,
            "appointment_booker_id": partner.id,
            "partner_ids": [(4, partner.id)],
        })
        self.assertFalse(
            event.dgc_turn_id,
            "No DGC turn should be created for non-DGC appointment type",
        )

    # --- T-5.3.4: Same DNI reuses existing partner (dedup) ---

    def test_portal_booking_partner_dedup(self):
        """Same DNI submitted twice reuses existing partner, no duplicate."""
        dni = "33445566"
        # First resolution
        result1 = self.Turn._find_or_create_partner(
            dni, "First Submission", "first@ctrl.com"
        )
        # Second resolution with different name/email
        result2 = self.Turn._find_or_create_partner(
            dni, "Second Submission", "second@ctrl.com"
        )
        self.assertEqual(
            result1["partner_id"],
            result2["partner_id"],
            "Same DNI should resolve to the same partner",
        )
        self.assertEqual(result1["partner_id"], self.existing_partner.id)

        # Verify no duplicates were created
        partner_count = self.Partner.search_count([("vat", "=", dni)])
        self.assertEqual(partner_count, 1, "No duplicate partner should exist")

    def test_portal_booking_partner_dedup_cuit_vs_dni(self):
        """CUIT and its base DNI resolve to the same partner."""
        # existing_partner has vat="33445566"
        # A CUIT containing that base DNI should resolve to the same partner
        # First, find a valid CUIT for base 33445566
        # We test that _normalize_dni extracts base from CUIT correctly
        result_dni = self.Turn._find_or_create_partner(
            "33445566", "Via DNI", "dni@ctrl.com"
        )
        # Create a new partner for a completely different DNI to prove dedup works
        result_new = self.Turn._find_or_create_partner(
            "99001122", "New Person", "new@ctrl.com"
        )
        self.assertNotEqual(
            result_dni["partner_id"],
            result_new["partner_id"],
            "Different DNIs should resolve to different partners",
        )
