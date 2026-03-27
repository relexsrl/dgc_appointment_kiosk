from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('standard', 'at_install')
class TestSecurityRules(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Area = cls.env["appointment.type"]
        cls.Turn = cls.env["dgc.appointment.turn"]

        cls.area_geo = cls.Area.create(
            {
                "name": "Geografía",
                "is_dgc_area": True,
                "dgc_code": "TS_GEO",
                "category": "recurring",
                "appointment_duration": 0.25,
                "appointment_tz": "America/Argentina/Buenos_Aires",
            }
        )
        cls.area_cat = cls.Area.create(
            {
                "name": "Catastro",
                "is_dgc_area": True,
                "dgc_code": "TS_CAT",
                "category": "recurring",
                "appointment_duration": 0.25,
                "appointment_tz": "America/Argentina/Buenos_Aires",
            }
        )

        # Operator assigned to GEO only (needs base.group_user for internal access)
        cls.operator_geo = cls.env["res.users"].create(
            {
                "name": "Op Geo",
                "login": "op_geo_sec",
                "group_ids": [
                    (4, cls.env.ref("base.group_user").id),
                    (4, cls.env.ref("dgc_appointment_kiosk.group_dgc_operator").id),
                ],
            }
        )
        cls.area_geo.staff_user_ids = [(4, cls.operator_geo.id)]

        # Admin (needs base.group_user for internal access)
        cls.admin_user = cls.env["res.users"].create(
            {
                "name": "Admin DGC",
                "login": "admin_dgc_sec",
                "group_ids": [
                    (4, cls.env.ref("base.group_user").id),
                    (4, cls.env.ref("dgc_appointment_kiosk.group_dgc_admin").id),
                ],
            }
        )
        cls.area_geo.staff_user_ids = [(4, cls.admin_user.id)]
        cls.area_cat.staff_user_ids = [(4, cls.admin_user.id)]

    def test_operator_sees_own_area_turns(self):
        """Operator only sees turns in their assigned areas."""
        turn_geo = self.Turn.create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        turn_cat = self.Turn.create(
            {
                "citizen_dni": "87654321",
                "area_id": self.area_cat.id,
            }
        )
        turns = self.Turn.with_user(self.operator_geo).search([])
        self.assertIn(turn_geo, turns)
        self.assertNotIn(turn_cat, turns)

    def test_admin_sees_all_turns(self):
        """Admin sees all turns regardless of area."""
        self.Turn.create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        self.Turn.create(
            {
                "citizen_dni": "87654321",
                "area_id": self.area_cat.id,
            }
        )
        turns = self.Turn.with_user(self.admin_user).search([])
        self.assertGreaterEqual(len(turns), 2)

    def test_operator_cannot_create_turn(self):
        """Operator does not have create permission on turns."""
        with self.assertRaises(AccessError):
            self.Turn.with_user(self.operator_geo).create(
                {
                    "citizen_dni": "11111111",
                    "area_id": self.area_geo.id,
                }
            )

    def test_operator_can_write_own_area_turn(self):
        """Operator can modify turns in their area."""
        turn = self.Turn.create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area_geo.id,
            }
        )
        turn.with_user(self.operator_geo).action_call()
        self.assertEqual(turn.state, "calling")

    def test_group_hierarchy(self):
        """Admin inherits area_manager which inherits operator."""
        # all_group_ids includes implied groups
        admin_groups = self.admin_user.all_group_ids
        self.assertIn(
            self.env.ref("dgc_appointment_kiosk.group_dgc_operator"),
            admin_groups,
        )
        self.assertIn(
            self.env.ref("dgc_appointment_kiosk.group_dgc_area_manager"),
            admin_groups,
        )

    def test_admin_can_create_turn(self):
        """Admin has full CRUD on turns."""
        turn = self.Turn.with_user(self.admin_user).create(
            {
                "citizen_dni": "22222222",
                "area_id": self.area_geo.id,
            }
        )
        self.assertTrue(turn.exists())
