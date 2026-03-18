from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestElapsedTimer(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.area = cls.env["dgc.appointment.area"].create(
            {
                "name": "Test",
                "code": "ET_TIM",
            }
        )

    def _create_turn(self):
        return self.env["dgc.appointment.turn"].create(
            {
                "citizen_dni": "12345678",
                "area_id": self.area.id,
            }
        )

    def test_elapsed_time_display_serving(self):
        """Serving turn shows elapsed time in HH:MM:SS format."""
        turn = self._create_turn()
        now = fields.Datetime.now()
        turn.write(
            {
                "state": "serving",
                "serve_date": now - timedelta(minutes=5, seconds=30),
            }
        )
        self.assertTrue(turn.elapsed_time_display)
        self.assertRegex(turn.elapsed_time_display, r"^\d{2}:\d{2}:\d{2}$")
        # Should be approximately 00:05:30
        self.assertTrue(turn.elapsed_time_display.startswith("00:05:"))

    def test_elapsed_time_display_not_serving(self):
        """Waiting turn returns empty string."""
        turn = self._create_turn()
        self.assertEqual(turn.elapsed_time_display, "")

    def test_elapsed_time_display_done(self):
        """Done turn returns empty string (timer only during serving)."""
        turn = self._create_turn()
        turn.write(
            {
                "state": "done",
                "serve_date": fields.Datetime.now() - timedelta(minutes=10),
                "done_date": fields.Datetime.now(),
            }
        )
        self.assertEqual(turn.elapsed_time_display, "")
