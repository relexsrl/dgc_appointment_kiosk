from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestTurnWorkflow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Area = cls.env["appointment.type"]
        cls.Turn = cls.env["dgc.appointment.turn"]

        cls.area = cls.Area.create(
            {
                "name": "Geografía",
                "is_dgc_area": True,
                "dgc_code": "TW_GEO",
                "dgc_max_counters": 2,
                "category": "recurring",
                "appointment_duration": 0.25,
                "appointment_tz": "America/Argentina/Buenos_Aires",
            }
        )

        cls.operator = cls.env["res.users"].create(
            {
                "name": "Operador Test",
                "login": "op_test_dgc",
                "group_ids": [
                    (4, cls.env.ref("base.group_user").id),
                    (4, cls.env.ref("dgc_appointment_kiosk.group_dgc_operator").id),
                ],
            }
        )
        cls.area.staff_user_ids = [(4, cls.operator.id)]

    def _create_turn(self, dni="12345678"):
        return self.Turn.create(
            {
                "citizen_dni": dni,
                "area_id": self.area.id,
            }
        )

    def test_call_sets_calling_state(self):
        """Calling a turn sets state to 'calling' and creates call log."""
        turn = self._create_turn()
        turn.with_user(self.operator).action_call()
        self.assertEqual(turn.state, "calling")
        self.assertTrue(turn.call_date)
        self.assertEqual(len(turn.call_log_ids), 1)
        self.assertEqual(turn.call_count, 1)

    def test_recall_increments_call_count(self):
        """Re-calling a turn increments call_count."""
        turn = self._create_turn()
        turn.with_user(self.operator).action_call()
        turn.with_user(self.operator).action_recall()
        self.assertEqual(turn.call_count, 2)
        self.assertEqual(len(turn.call_log_ids), 2)

    def test_serve_sets_serving_state(self):
        """Serving a called turn sets state and serve_date."""
        turn = self._create_turn()
        turn.with_user(self.operator).action_call()
        turn.with_user(self.operator).action_serve()
        self.assertEqual(turn.state, "serving")
        self.assertTrue(turn.serve_date)

    def test_done_sets_done_state(self):
        """Finishing a turn sets state, done_date, and computes duration."""
        turn = self._create_turn()
        turn.with_user(self.operator).action_call()
        turn.with_user(self.operator).action_serve()
        turn.with_user(self.operator).action_done()
        self.assertEqual(turn.state, "done")
        self.assertTrue(turn.done_date)

    def test_no_show_requires_call(self):
        """Cannot mark no_show without calling first."""
        turn = self._create_turn()
        with self.assertRaises(UserError):
            turn.with_user(self.operator).action_no_show()

    def test_no_show_from_calling(self):
        """Can mark no_show after calling."""
        turn = self._create_turn()
        turn.with_user(self.operator).action_call()
        turn.with_user(self.operator).action_no_show()
        self.assertEqual(turn.state, "no_show")

    def test_call_from_wrong_state_fails(self):
        """Cannot call a turn that is already serving."""
        turn = self._create_turn()
        turn.with_user(self.operator).action_call()
        turn.with_user(self.operator).action_serve()
        with self.assertRaises(UserError):
            turn.with_user(self.operator).action_call()

    def test_full_workflow(self):
        """Full turn lifecycle: waiting → calling → serving → done."""
        turn = self._create_turn()
        self.assertEqual(turn.state, "waiting")

        turn.with_user(self.operator).action_call()
        self.assertEqual(turn.state, "calling")
        self.assertTrue(turn.call_date)

        turn.with_user(self.operator).action_serve()
        self.assertEqual(turn.state, "serving")
        self.assertTrue(turn.serve_date)

        turn.with_user(self.operator).action_done()
        self.assertEqual(turn.state, "done")
        self.assertTrue(turn.done_date)

    def test_duration_computed(self):
        """Duration is computed from serve_date to done_date."""
        turn = self._create_turn()
        turn.with_user(self.operator).action_call()
        turn.with_user(self.operator).action_serve()
        # Manually set timestamps for predictable duration
        now = fields.Datetime.now()
        turn.write(
            {
                "serve_date": now - timedelta(minutes=10),
                "done_date": now,
            }
        )
        self.assertAlmostEqual(turn.duration, 10.0, places=0)

    def test_wait_time_computed(self):
        """Wait time is computed from create_date to call_date."""
        turn = self._create_turn()
        turn.with_user(self.operator).action_call()
        # wait_time should be approximately 0 (created and called nearly instantly)
        self.assertAlmostEqual(turn.wait_time, 0, delta=0.5)

    def test_cron_closes_pending_turns(self):
        """Cron marks yesterday's pending turns as no_show."""
        yesterday = fields.Date.subtract(fields.Date.context_today(self.env["dgc.appointment.turn"]), days=1)
        turn = self.Turn.create(
            {
                "citizen_dni": "11111111",
                "area_id": self.area.id,
                "date": yesterday,
            }
        )
        self.Turn._cron_close_pending_turns()
        turn.invalidate_recordset()
        self.assertEqual(turn.state, "no_show")
