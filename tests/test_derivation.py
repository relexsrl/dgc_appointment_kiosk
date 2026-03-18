from odoo.tests.common import TransactionCase


class TestDerivation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Area = cls.env["appointment.type"]
        cls.Turn = cls.env["dgc.appointment.turn"]

        cls.area_geo = cls.Area.create(
            {
                "name": "Geografía",
                "is_dgc_area": True,
                "dgc_code": "TD_GEO",
                "category": "recurring",
                "appointment_duration": 0.25,
                "appointment_tz": "America/Argentina/Buenos_Aires",
            }
        )
        cls.area_cat = cls.Area.create(
            {
                "name": "Catastro",
                "is_dgc_area": True,
                "dgc_code": "TD_CAT",
                "category": "recurring",
                "appointment_duration": 0.25,
                "appointment_tz": "America/Argentina/Buenos_Aires",
            }
        )
        cls.operator = cls.env["res.users"].create(
            {
                "name": "Operador Test",
                "login": "op_deriv_test",
                "group_ids": [
                    (4, cls.env.ref("base.group_user").id),
                    (4, cls.env.ref("dgc_appointment_kiosk.group_dgc_operator").id),
                ],
                "dgc_area_ids": [(4, cls.area_geo.id), (4, cls.area_cat.id)],
            }
        )

    def test_wizard_creates_derivation(self):
        """Derivation wizard creates a derivation record."""
        turn = self.Turn.create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        wizard = (
            self.env["dgc.turn.derive.wizard"]
            .with_user(self.operator)
            .create(
                {
                    "turn_id": turn.id,
                    "to_area_id": self.area_cat.id,
                    "reason": "Trámite de catastro",
                }
            )
        )
        wizard.action_derive()

        self.assertEqual(len(turn.derivation_ids), 1)
        derivation = turn.derivation_ids[0]
        self.assertEqual(derivation.from_area_id, self.area_geo)
        self.assertEqual(derivation.to_area_id, self.area_cat)
        self.assertEqual(derivation.reason, "Trámite de catastro")

    def test_derivation_changes_area(self):
        """After derivation, turn moves to destination area."""
        turn = self.Turn.create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        wizard = (
            self.env["dgc.turn.derive.wizard"]
            .with_user(self.operator)
            .create(
                {
                    "turn_id": turn.id,
                    "to_area_id": self.area_cat.id,
                    "reason": "Redireccionado",
                }
            )
        )
        wizard.action_derive()
        self.assertEqual(turn.area_id, self.area_cat)

    def test_derivation_resets_to_waiting(self):
        """Derived turn goes back to waiting state in new area."""
        turn = self.Turn.create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        turn.with_user(self.operator).action_call()
        wizard = (
            self.env["dgc.turn.derive.wizard"]
            .with_user(self.operator)
            .create(
                {
                    "turn_id": turn.id,
                    "to_area_id": self.area_cat.id,
                    "reason": "Redireccionado",
                }
            )
        )
        wizard.action_derive()
        self.assertEqual(turn.state, "waiting")

    def test_derivation_records_user(self):
        """Derivation records the user who performed it."""
        turn = self.Turn.create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        wizard = (
            self.env["dgc.turn.derive.wizard"]
            .with_user(self.operator)
            .create(
                {
                    "turn_id": turn.id,
                    "to_area_id": self.area_cat.id,
                    "reason": "Motivo test",
                }
            )
        )
        wizard.action_derive()
        self.assertEqual(turn.derivation_ids[0].user_id, self.operator)

    def test_wizard_returns_close_action(self):
        """Wizard action_derive returns close action."""
        turn = self.Turn.create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        wizard = (
            self.env["dgc.turn.derive.wizard"]
            .with_user(self.operator)
            .create(
                {
                    "turn_id": turn.id,
                    "to_area_id": self.area_cat.id,
                    "reason": "Motivo",
                }
            )
        )
        result = wizard.action_derive()
        self.assertEqual(result["type"], "ir.actions.act_window_close")

    def test_multiple_derivations(self):
        """A turn can be derived multiple times."""
        turn = self.Turn.create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        # First derivation
        wizard1 = (
            self.env["dgc.turn.derive.wizard"]
            .with_user(self.operator)
            .create(
                {
                    "turn_id": turn.id,
                    "to_area_id": self.area_cat.id,
                    "reason": "Primera derivación",
                }
            )
        )
        wizard1.action_derive()
        self.assertEqual(turn.area_id, self.area_cat)

        # Second derivation back
        wizard2 = (
            self.env["dgc.turn.derive.wizard"]
            .with_user(self.operator)
            .create(
                {
                    "turn_id": turn.id,
                    "to_area_id": self.area_geo.id,
                    "reason": "Segunda derivación",
                }
            )
        )
        wizard2.action_derive()
        self.assertEqual(turn.area_id, self.area_geo)
        self.assertEqual(len(turn.derivation_ids), 2)
