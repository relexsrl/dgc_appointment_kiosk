from . import controllers
from . import models
from . import wizards


def post_init_hook(cr, registry):
    """Assign DGC admin group to root user (user 2) and remove operator role on module installation."""
    from odoo import api

    env = api.Environment(cr, 2, {})  # Environment for root user
    admin_group = env.ref("dgc_appointment_kiosk.group_dgc_admin")
    operator_group = env.ref("dgc_appointment_kiosk.group_dgc_operator")
    root_user = env.ref("base.user_root")

    if root_user:
        # Remove operator group (admin shouldn't see operator panel)
        if operator_group in root_user.groups_id:
            root_user.write({"groups_id": [(3, operator_group.id)]})  # Remove group
        # Add admin group (admin should see admin dashboard)
        if admin_group and admin_group not in root_user.groups_id:
            root_user.write({"groups_id": [(4, admin_group.id)]})  # Add group
