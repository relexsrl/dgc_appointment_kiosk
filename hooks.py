import logging


_logger = logging.getLogger(__name__)

BROKEN_EXPR = "object.event_id.appointment_type_id.resource_manage_capacity"
SAFE_EXPR = (
    "object.event_id and object.event_id.appointment_type_id and "
    "(('manage_capacity' in object.event_id.appointment_type_id._fields and "
    "object.event_id.appointment_type_id.manage_capacity) or "
    "('resource_manage_capacity' in object.event_id.appointment_type_id._fields and "
    "object.event_id.appointment_type_id.resource_manage_capacity))"
)

BROKEN_ASSIGN_EXPR = "object.event_id.appointment_type_id.assign_method != 'time_auto_assign'"
SAFE_ASSIGN_EXPR = (
    "object.event_id and object.event_id.appointment_type_id and "
    "('is_auto_assign' in object.event_id.appointment_type_id._fields and "
    "not object.event_id.appointment_type_id.is_auto_assign)"
)


def _patch_template_field(cr, broken, safe):
    """Replace broken expression with safe one in mail_template.body_html and ir_translation."""
    like_pattern = f"%{broken}%"

    cr.execute(
        """
        UPDATE mail_template
           SET body_html = REPLACE(body_html::text, %s, %s)::jsonb
         WHERE body_html IS NOT NULL
           AND body_html::text LIKE %s
        """,
        (broken, safe, like_pattern),
    )
    templates_patched = cr.rowcount

    cr.execute("SELECT to_regclass('ir_translation')")
    ir_translation_table = cr.fetchone()[0]
    translations_patched = 0

    if ir_translation_table:
        cr.execute(
            """
            UPDATE ir_translation
               SET value = REPLACE(value, %s, %s)
             WHERE name = 'mail.template,body_html'
               AND value LIKE %s
            """,
            (broken, safe, like_pattern),
        )
        translations_value_patched = cr.rowcount

        cr.execute(
            """
            UPDATE ir_translation
               SET src = REPLACE(src, %s, %s)
             WHERE name = 'mail.template,body_html'
               AND src LIKE %s
            """,
            (broken, safe, like_pattern),
        )
        translations_src_patched = cr.rowcount
        translations_patched = translations_value_patched + translations_src_patched
    else:
        _logger.info(
            "Skipping translation patch: table ir_translation does not exist in this Odoo version"
        )

    return templates_patched, translations_patched


def patch_resource_manage_capacity_templates(cr):
    templates_patched, translations_patched = _patch_template_field(cr, BROKEN_EXPR, SAFE_EXPR)
    _logger.info(
        "Patched mail templates for resource_manage_capacity fallback: templates=%s, translations=%s",
        templates_patched,
        translations_patched,
    )
    return templates_patched, translations_patched


def patch_assign_method_templates(cr):
    templates_patched, translations_patched = _patch_template_field(
        cr, BROKEN_ASSIGN_EXPR, SAFE_ASSIGN_EXPR
    )
    _logger.info(
        "Patched mail templates for assign_method → is_auto_assign: templates=%s, translations=%s",
        templates_patched,
        translations_patched,
    )
    return templates_patched, translations_patched


def post_init_hook(env):
    patch_resource_manage_capacity_templates(env.cr)
    patch_assign_method_templates(env.cr)
