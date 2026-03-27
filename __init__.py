from . import controllers
from . import models
from . import wizards


def post_init_hook(cr, registry):
    """Assign DGC admin group to root user (user 2) on module installation."""
    from odoo import api
    from odoo.tools import config

    env = api.Environment(cr, 2, {})  # Environment for root user
    admin_group = env.ref("dgc_appointment_kiosk.group_dgc_admin")
    root_user = env.ref("base.user_root")

    if root_user and admin_group:
        root_user.write({"groups_id": [(4, admin_group.id)]})  # Add group without removing others
