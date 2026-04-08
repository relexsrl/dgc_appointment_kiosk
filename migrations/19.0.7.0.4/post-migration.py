from odoo.addons.dgc_appointment_kiosk import hooks


def migrate(cr, version):
    if not version:
        return
    hooks.patch_assign_method_templates(cr)
