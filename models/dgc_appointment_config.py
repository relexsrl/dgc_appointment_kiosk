import re
import uuid

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class DgcAppointmentConfig(models.TransientModel):
    _inherit = "res.config.settings"

    dgc_allow_multiple_turns = fields.Boolean(
        string="Permitir múltiples turnos por DNI",
        config_parameter="dgc_appointment_kiosk.allow_multiple_turns",
        default=True,
    )
    dgc_kiosk_timeout = fields.Integer(
        string="Timeout del kiosco (seg)",
        config_parameter="dgc_appointment_kiosk.kiosk_timeout",
        default=30,
    )
    dgc_kiosk_require_email = fields.Boolean(
        string="Email obligatorio en kiosco",
        config_parameter="dgc_appointment_kiosk.kiosk_require_email",
        default=False,
    )
    dgc_kiosk_show_notes = fields.Boolean(
        string="Mostrar campo notas en kiosco",
        config_parameter="dgc_appointment_kiosk.kiosk_show_notes",
        default=False,
    )
    dgc_display_refresh_interval = fields.Integer(
        string="Intervalo de refresco display (seg)",
        config_parameter="dgc_appointment_kiosk.display_refresh_interval",
        default=30,
    )
    dgc_display_calling_count = fields.Integer(
        string="Turnos llamando visibles",
        config_parameter="dgc_appointment_kiosk.display_calling_count",
        default=3,
    )
    dgc_display_waiting_count = fields.Integer(
        string="Turnos en espera visibles",
        config_parameter="dgc_appointment_kiosk.display_waiting_count",
        default=10,
    )
    dgc_scroll_message_1 = fields.Char(
        string="Mensaje rotativo 1",
        config_parameter="dgc_appointment_kiosk.scroll_message_1",
    )
    dgc_scroll_message_2 = fields.Char(
        string="Mensaje rotativo 2",
        config_parameter="dgc_appointment_kiosk.scroll_message_2",
    )
    dgc_scroll_message_3 = fields.Char(
        string="Mensaje rotativo 3",
        config_parameter="dgc_appointment_kiosk.scroll_message_3",
    )
    dgc_brand_primary_color = fields.Char(
        string="Color primario",
        config_parameter="dgc_appointment_kiosk.brand_primary_color",
        default="#1A237E",
    )
    dgc_rate_limit_seconds = fields.Integer(
        string="Rate limit (seg)",
        config_parameter="dgc_appointment_kiosk.rate_limit_seconds",
        default=5,
    )
    dgc_max_call_count = fields.Integer(
        string="Máx. llamadas antes de no_show",
        config_parameter="dgc_appointment_kiosk.max_call_count",
        default=3,
    )
    dgc_kiosk_token = fields.Char(
        string="Token del Kiosk",
        config_parameter="dgc_appointment_kiosk.kiosk_token",
    )
    dgc_display_token = fields.Char(
        string="Token del Display",
        config_parameter="dgc_appointment_kiosk.display_token",
    )
    dgc_kiosk_full_url = fields.Char(
        string="URL del Kiosco",
        compute="_compute_kiosk_urls",
    )
    dgc_display_full_url = fields.Char(
        string="URL del Display",
        compute="_compute_kiosk_urls",
    )

    @api.constrains("dgc_brand_primary_color")
    def _check_brand_primary_color(self):
        for rec in self:
            val = rec.dgc_brand_primary_color
            if val and not re.match(r'^#[0-9a-fA-F]{3,8}$', val):
                raise ValidationError(
                    "El color primario debe ser un color hexadecimal válido (ej: #1A237E)."
                )

    @api.depends("dgc_kiosk_token", "dgc_display_token")
    def _compute_kiosk_urls(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for rec in self:
            rec.dgc_kiosk_full_url = f"{base_url}/kiosk/{rec.dgc_kiosk_token}/checkin" if rec.dgc_kiosk_token else False
            rec.dgc_display_full_url = f"{base_url}/display/{rec.dgc_display_token}/queue" if rec.dgc_display_token else False

    def _regenerate_token(self, param_key, field_name):
        token = str(uuid.uuid4())
        self.env['ir.config_parameter'].sudo().set_param(param_key, token)
        self.env.registry.clear_cache()
        setattr(self, field_name, token)

    def action_regenerate_kiosk_token(self):
        self._regenerate_token("dgc_appointment_kiosk.kiosk_token", "dgc_kiosk_token")

    def action_regenerate_display_token(self):
        self._regenerate_token("dgc_appointment_kiosk.display_token", "dgc_display_token")
