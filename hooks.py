import logging


_logger = logging.getLogger(__name__)

BROKEN_EXPR = "object.event_id.appointment_type_id.resource_manage_capacity"
SAFE_EXPR = (
    "object.event_id and object.event_id.appointment_type_id and "
    "(('manage_capacity' in object.event_id.appointment_type_id._fields and "
    "object.event_id.appointment_type_id.manage_capacity) or "
    "('resource_manage_capacity' in object.event_id.appointment_type_id._fields and "
    "getattr(object.event_id.appointment_type_id, 'resource_manage_capacity', False)))"
)


def patch_resource_manage_capacity_templates(cr):
    like_pattern = f"%{BROKEN_EXPR}%"

    cr.execute(
        """
        UPDATE mail_template
           SET body_html = REPLACE(body_html, %s, %s)
         WHERE body_html LIKE %s
        """,
        (BROKEN_EXPR, SAFE_EXPR, like_pattern),
    )
    templates_patched = cr.rowcount

    cr.execute(
        """
        UPDATE ir_translation
           SET value = REPLACE(value, %s, %s)
         WHERE name = 'mail.template,body_html'
           AND value LIKE %s
        """,
        (BROKEN_EXPR, SAFE_EXPR, like_pattern),
    )
    translations_value_patched = cr.rowcount

    cr.execute(
        """
        UPDATE ir_translation
           SET src = REPLACE(src, %s, %s)
         WHERE name = 'mail.template,body_html'
           AND src LIKE %s
        """,
        (BROKEN_EXPR, SAFE_EXPR, like_pattern),
    )
    translations_src_patched = cr.rowcount

    translations_patched = translations_value_patched + translations_src_patched
    _logger.info(
        "Patched mail templates for resource_manage_capacity fallback: templates=%s, translations=%s",
        templates_patched,
        translations_patched,
    )
    return templates_patched, translations_patched


def post_init_hook(cr, registry):
    del registry
    patch_resource_manage_capacity_templates(cr)
