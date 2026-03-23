{
    "name": "DGC Turnero - Sistema de Turnos con Kiosco",
    "version": "19.0.4.0.0",
    "category": "Services",
    "summary": "Sistema de gestión de turnos con kiosco táctil para la DGC",
    "author": "Relex SRL",
    "website": "https://www.relex.com.ar",
    "license": "LGPL-3",
    "depends": [
        "base",
        "base_setup",
        "appointment",
        "mail",
        "bus",
        "web",
    ],
    "data": [
        # Security
        "security/security.xml",
        "security/ir.model.access.csv",
        # Data
        "data/ir_sequence_data.xml",
        "data/ir_cron_data.xml",
        "data/default_config_data.xml",
        # Wizards
        "wizards/dgc_turn_create_wizard_views.xml",
        "wizards/dgc_turn_derive_wizard_views.xml",
        # Views
        "views/dgc_appointment_area_views.xml",
        "views/dgc_appointment_turn_views.xml",
        "views/dgc_appointment_config_views.xml",
        "views/dgc_appointment_derivation_views.xml",
        "views/dgc_dashboard_views.xml",
        "views/menu_views.xml",
        # Templates
        "templates/kiosk_main_view.xml",
        "templates/display_queue_view.xml",
        # Reports
        "report/dgc_turn_report.xml",
        "report/dgc_turn_report_template.xml",
    ],
    "assets": {
        "dgc_appointment_kiosk.assets_kiosk": [
            "dgc_appointment_kiosk/static/lib/css/_tokens.scss",
            "dgc_appointment_kiosk/static/lib/css/kiosk.scss",
            "dgc_appointment_kiosk/static/lib/js/kiosk.js",
        ],
        "dgc_appointment_kiosk.assets_display": [
            "dgc_appointment_kiosk/static/lib/css/_tokens.scss",
            "dgc_appointment_kiosk/static/lib/css/display.scss",
            "dgc_appointment_kiosk/static/lib/js/display.js",
        ],
        "web.assets_backend": [
            "dgc_appointment_kiosk/static/src/css/_tokens.scss",
            "dgc_appointment_kiosk/static/src/js/backoffice.js",
            "dgc_appointment_kiosk/static/src/js/elapsed_timer.js",
            "dgc_appointment_kiosk/static/src/xml/elapsed_timer.xml",
            "dgc_appointment_kiosk/static/src/js/operator_dashboard.js",
            "dgc_appointment_kiosk/static/src/xml/operator_dashboard.xml",
            "dgc_appointment_kiosk/static/src/css/operator_dashboard.scss",
            "dgc_appointment_kiosk/static/src/js/token_field.js",
            "dgc_appointment_kiosk/static/src/xml/token_field.xml",
        ],
    },
    "demo": ["data/demo_data.xml"],
    "installable": True,
    "application": True,
    "auto_install": False,
}
