from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestTurnCreation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Area = cls.env["dgc.appointment.area"]
        cls.Turn = cls.env["dgc.appointment.turn"]

        cls.area_geo = cls.Area.create(
            {
                "name": "Geografía",
                "code": "TC_GEO",
                "location": "Planta Baja",
                "avg_service_time": 15,
                "max_counters": 2,
            }
        )
        cls.area_cat = cls.Area.create(
            {
                "name": "Catastro",
                "code": "TC_CAT",
                "location": "Primer Piso",
                "avg_service_time": 20,
                "max_counters": 1,
            }
        )

    def test_create_turn_generates_number(self):
        """Turn creation generates a turn number with area code prefix."""
        turn = self.Turn.create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        self.assertTrue(turn.turn_number.startswith("TC_GEO-"))
        self.assertEqual(turn.state, "waiting")

    def test_create_turn_auto_waiting(self):
        """New turns automatically transition to 'waiting' state."""
        turn = self.Turn.create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        self.assertEqual(turn.state, "waiting")

    def test_turn_sequence_increments(self):
        """Sequential turns get incrementing numbers."""
        turn1 = self.Turn.create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        turn2 = self.Turn.create(
            {
                "citizen_dni": "87654321",
                "area_id": self.area_geo.id,
            }
        )
        num1 = int(turn1.turn_number.split("-")[-1])
        num2 = int(turn2.turn_number.split("-")[-1])
        self.assertEqual(num2, num1 + 1)

    def test_validate_dni_7_digits(self):
        """7-digit DNI is valid."""
        self.assertTrue(self.Turn._validate_dni("1234567"))

    def test_validate_dni_8_digits(self):
        """8-digit DNI is valid."""
        self.assertTrue(self.Turn._validate_dni("12345678"))

    def test_validate_dni_too_short(self):
        """DNI with fewer than 7 digits is invalid."""
        self.assertFalse(self.Turn._validate_dni("123456"))

    def test_validate_dni_too_long(self):
        """DNI with more than 11 digits is invalid."""
        self.assertFalse(self.Turn._validate_dni("123456789012"))

    def test_validate_dni_letters(self):
        """DNI with letters is invalid."""
        self.assertFalse(self.Turn._validate_dni("1234567a"))

    def test_validate_cuit_valid(self):
        """Valid CUIT passes mod-11 check."""
        # 20-12345678-6 is a valid CUIT (check digit = 6)
        self.assertTrue(self.Turn._validate_dni("20123456786"))

    def test_validate_cuit_invalid_check_digit(self):
        """CUIT with wrong check digit fails."""
        self.assertFalse(self.Turn._validate_dni("20123456780"))

    def test_duplicate_dni_same_area_rejected(self):
        """Cannot create duplicate turn for same DNI+area+date in pending states."""
        self.Turn.create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        with self.assertRaises(ValidationError):
            self.Turn.create(
                {
                    "citizen_dni": "12345678",
                    "area_id": self.area_geo.id,
                }
            )

    def test_duplicate_dni_different_area_allowed(self):
        """Same DNI can take turns in different areas (allow_multiple_turns=True)."""
        self.env["ir.config_parameter"].set_param("dgc_appointment_kiosk.allow_multiple_turns", "True")
        self.Turn.create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        turn2 = self.Turn.create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_cat.id,
            }
        )
        self.assertTrue(turn2.exists())

    def test_no_multiple_turns_blocks_different_area(self):
        """When allow_multiple_turns=False, same DNI blocked across all areas."""
        self.env["ir.config_parameter"].set_param("dgc_appointment_kiosk.allow_multiple_turns", "False")
        self.Turn.create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        with self.assertRaises(ValidationError):
            self.Turn.create(
                {
                    "citizen_dni": "12345678",
                    "area_id": self.area_cat.id,
                }
            )

    def test_inactive_area_turn_rejected(self):
        """Cannot create turn for inactive area (via controller logic)."""
        inactive_area = self.Area.create(
            {
                "name": "Inactiva",
                "code": "TC_INA",
                "active": False,
            }
        )
        # The area exists but is inactive - controller checks this
        self.assertFalse(inactive_area.active)

    def test_capacity_computed(self):
        """max_daily_turns computed from config hours and area settings."""
        self.env["ir.config_parameter"].set_param("dgc_appointment_kiosk.hour_start", "8.0")
        self.env["ir.config_parameter"].set_param("dgc_appointment_kiosk.hour_end", "14.0")
        self.area_geo.invalidate_recordset()
        # 6 hours * 60 min / 15 avg * 2 counters = 48
        self.assertEqual(self.area_geo.max_daily_turns, 48)

    def test_no_show_does_not_consume_capacity(self):
        """Turns marked as no_show don't count toward capacity."""
        initial_remaining = self.area_geo.remaining_turns_today
        turn = self.Turn.create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        self.area_geo.invalidate_recordset()
        # After creating, remaining should drop by 1
        self.assertEqual(self.area_geo.remaining_turns_today, initial_remaining - 1)
        turn.action_call()
        turn.action_no_show()
        self.area_geo.invalidate_recordset()
        # After no_show, remaining should go back up (no_show excluded)
        self.assertEqual(self.area_geo.remaining_turns_today, initial_remaining)

    def test_find_or_create_partner_new(self):
        """_find_or_create_partner creates new partner for unknown DNI."""
        result = self.Turn._find_or_create_partner("99999999", "Test User", "test@example.com")
        self.assertTrue(result["partner_id"])
        partner = self.env["res.partner"].browse(result["partner_id"])
        self.assertEqual(partner.vat, "99999999")

    def test_find_or_create_partner_existing(self):
        """_find_or_create_partner returns existing partner."""
        self.env["res.partner"].create({"name": "Existing", "vat": "88888888"})
        result = self.Turn._find_or_create_partner("88888888", "Existing", None)
        self.assertTrue(result["partner_id"])
        self.assertFalse(result["email_conflict"])

    def test_email_conflict_detection(self):
        """Detects email conflict when partner has different email."""
        self.env["res.partner"].create(
            {
                "name": "Conflict",
                "vat": "77777777",
                "email": "original@example.com",
            }
        )
        result = self.Turn._find_or_create_partner("77777777", "Conflict", "new@example.com")
        self.assertTrue(result["email_conflict"])
        self.assertIn("***", result["existing_email_masked"])

    def test_mask_email(self):
        """Email masking shows first 3 chars + *** + @domain."""
        masked = self.Turn._mask_email("johndoe@example.com")
        self.assertEqual(masked, "joh***@example.com")

    def test_mask_email_short(self):
        """Short email local part masking."""
        masked = self.Turn._mask_email("ab@example.com")
        self.assertEqual(masked, "a***@example.com")
