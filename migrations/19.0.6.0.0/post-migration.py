"""
Migration: Remove root user from operator boxes.

The root user (administrator) should not be assigned as an operator
to any boxes. This migration removes any dgc_operator_box records
that reference the root user.
"""


def migrate(cr, version):
    """Remove operator boxes assigned to root user."""
    # Get root user ID (always 2 in Odoo)
    cr.execute("SELECT id FROM res_users WHERE login = 'root'")
    root_user = cr.fetchone()

    if root_user:
        root_user_id = root_user[0]
        # Delete operator boxes assigned to root user
        cr.execute(
            "DELETE FROM dgc_operator_box WHERE operator_id = %s",
            (root_user_id,)
        )
        if cr.rowcount > 0:
            print(f"Removed {cr.rowcount} operator box(es) assigned to root user")
