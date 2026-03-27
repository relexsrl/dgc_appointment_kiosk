from . import controllers
from . import models
from . import wizards


def post_init_hook(cr, registry):
    """Configure DGC group hierarchy and assign admin group to root user on module installation."""
    from odoo import api

    env = api.Environment(cr, 2, {})  # Environment for root user

    # Get groups
    try:
        admin_group = env.ref("dgc_appointment_kiosk.group_dgc_admin")
        area_manager_group = env.ref("dgc_appointment_kiosk.group_dgc_area_manager")
        operator_group = env.ref("dgc_appointment_kiosk.group_dgc_operator")
    except ValueError:
        # Groups not found, skip
        return

    # Configure group hierarchy: Admin → Area Manager (but NOT Operator)
    # Area Manager can be separate role or inherit from Operator if desired
    if admin_group and area_manager_group and operator_group:
        # Admin implies Area Manager
        admin_group.write({"implied_ids": [(5, 0)]})  # Clear existing implications
        admin_group.write({"implied_ids": [(4, area_manager_group.id)]})  # Admin → Area Manager

        # Area Manager does NOT imply Operator (they are separate roles)
        area_manager_group.write({"implied_ids": [(5, 0)]})  # Clear existing implications

    # Assign admin group to root user and remove operator
    root_user = env.ref("base.user_root")
    if root_user:
        # Remove operator group (admin shouldn't see operator panel)
        if operator_group and operator_group in root_user.groups_id:
            root_user.write({"groups_id": [(3, operator_group.id)]})  # Remove group
        # Add admin group (admin should see admin dashboard)
        if admin_group and admin_group not in root_user.groups_id:
            root_user.write({"groups_id": [(4, admin_group.id)]})  # Add group
