from odoo.addons.dgc_appointment_kiosk import hooks


def migrate(cr, version):
    if not version:
        return
    hooks.patch_resource_manage_capacity_templates(cr)
