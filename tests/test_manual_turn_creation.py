from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase


class TestManualTurnCreation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.area_geo = cls.env["appointment.type"].create(
            {
                "name": "Geografía",
                "is_dgc_area": True,
                "dgc_code": "MC_GEO",
                "dgc_avg_service_time": 15,
                "dgc_max_counters": 2,
                "category": "recurring",
                "appointment_duration": 0.25,
                "appointment_tz": "America/Argentina/Buenos_Aires",
            }
        )
        cls.area_cat = cls.env["appointment.type"].create(
            {
                "name": "Catastro",
                "is_dgc_area": True,
                "dgc_code": "MC_CAT",
                "dgc_avg_service_time": 15,
                "dgc_max_counters": 1,
                "category": "recurring",
                "appointment_duration": 0.25,
                "appointment_tz": "America/Argentina/Buenos_Aires",
            }
        )
        cls.operator = cls.env["res.users"].create(
            {
                "name": "Op Manual Test",
                "login": "op_manual_test",
                "group_ids": [
                    (4, cls.env.ref("base.group_user").id),
                    (4, cls.env.ref("dgc_appointment_kiosk.group_dgc_operator").id),
                ],
                "dgc_area_ids": [(4, cls.area_geo.id)],
            }
        )

    def _create_wizard(self, user=None, **kwargs):
        vals = {
            "citizen_dni": "12345678",
            "citizen_name": "Test Citizen",
            "area_id": self.area_geo.id,
        }
        vals.update(kwargs)
        Wizard = self.env["dgc.turn.create.wizard"]
        if user:
            Wizard = Wizard.with_user(user)
        return Wizard.create(vals)

    def test_wizard_creates_turn(self):
        """Wizard creates a turn via sudo, operator sees it."""
        wizard = self._create_wizard(user=self.operator)
        result = wizard.action_create_turn()
        self.assertEqual(result["res_model"], "dgc.appointment.turn")
        turn = self.env["dgc.appointment.turn"].browse(result["res_id"])
        self.assertTrue(turn.exists())
        self.assertEqual(turn.state, "waiting")
        self.assertEqual(turn.citizen_dni, "12345678")
        self.assertEqual(turn.area_id, self.area_geo)

    def test_wizard_defaults_single_area(self):
        """Operator with one area gets it as default."""
        wizard = self.env["dgc.turn.create.wizard"].with_user(self.operator).default_get(["area_id", "citizen_dni"])
        self.assertEqual(wizard.get("area_id"), self.area_geo.id)

    def test_wizard_validates_dni(self):
        """Invalid DNI raises UserError."""
        wizard = self._create_wizard(user=self.operator, citizen_dni="123")
        with self.assertRaises(UserError):
            wizard.action_create_turn()

    def test_wizard_checks_duplicate(self):
        """Duplicate DNI+area+date raises error."""
        wizard1 = self._create_wizard(user=self.operator)
        wizard1.action_create_turn()
        wizard2 = self._create_wizard(user=self.operator)
        with self.assertRaises(Exception):
            wizard2.action_create_turn()

    def test_wizard_creates_partner(self):
        """Wizard links to existing or new partner."""
        wizard = self._create_wizard(
            user=self.operator,
            citizen_email="test@example.com",
        )
        result = wizard.action_create_turn()
        turn = self.env["dgc.appointment.turn"].browse(result["res_id"])
        self.assertTrue(turn.partner_id)
        self.assertEqual(turn.partner_id.vat, "12345678")

    def test_wizard_area_restricted(self):
        """Wizard rejects area not assigned to operator."""
        wizard = self._create_wizard(
            user=self.operator,
            area_id=self.area_cat.id,
        )
        with self.assertRaises(UserError):
            wizard.action_create_turn()

    def test_operator_still_cannot_create_turn_directly(self):
        """Operator cannot bypass wizard to create turns directly."""
        with self.assertRaises(AccessError):
            self.env["dgc.appointment.turn"].with_user(self.operator).create(
                {
                    "citizen_dni": "99999999",
                    "area_id": self.area_geo.id,
                }
            )

    def test_wizard_populates_turn_number(self):
        """Created turn gets a proper turn number."""
        wizard = self._create_wizard(user=self.operator)
        result = wizard.action_create_turn()
        turn = self.env["dgc.appointment.turn"].browse(result["res_id"])
        self.assertTrue(turn.turn_number.startswith("MC_GEO-"))
