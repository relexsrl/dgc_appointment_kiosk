from odoo import fields, models


class DgcAppointmentConfig(models.TransientModel):
    _inherit = "res.config.settings"

    dgc_hour_start = fields.Float(
        string="Hora de inicio",
        config_parameter="dgc_appointment_kiosk.hour_start",
        default=8.0,
    )
    dgc_hour_end = fields.Float(
        string="Hora de fin",
        config_parameter="dgc_appointment_kiosk.hour_end",
        default=14.0,
    )
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
    dgc_brand_logo_url = fields.Char(
        string="URL del logo",
        config_parameter="dgc_appointment_kiosk.brand_logo_url",
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
