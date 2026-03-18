import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Migra asignaciones operador-area de la tabla custom a la nativa.

    Copia los registros de dgc_appointment_type_user_rel (campo custom
    dgc_area_ids) a appointment_type_res_users_rel (campo nativo
    staff_user_ids), evitando duplicados.

    La tabla custom tiene columnas: user_id, area_id
    La tabla nativa tiene columnas: appointment_type_id, res_users_id
    """
    if not version:
        return

    # Actualizar las record rules que están bajo noupdate="1" y cuyo
    # domain_force referenciaba user.dgc_area_ids.ids (campo eliminado).
    # Esto debe ejecutarse SIEMPRE, independientemente de si la tabla
    # custom existe, ya que las reglas pueden estar desactualizadas.
    _actualizar_record_rules(cr)

    # Migrar datos de la tabla custom a la nativa
    _migrar_asignaciones_operador_area(cr)


def _migrar_asignaciones_operador_area(cr):
    """Copia registros de dgc_appointment_type_user_rel a la tabla nativa."""
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'dgc_appointment_type_user_rel'
        )
    """)
    if not cr.fetchone()[0]:
        _logger.info(
            "Tabla dgc_appointment_type_user_rel no encontrada. "
            "Nada que migrar."
        )
        return

    cr.execute("SELECT COUNT(*) FROM dgc_appointment_type_user_rel")
    total = cr.fetchone()[0]
    _logger.info(
        "Migrando %d asignaciones operador-area de "
        "dgc_appointment_type_user_rel a appointment_type_res_users_rel",
        total,
    )

    cr.execute("""
        INSERT INTO appointment_type_res_users_rel
            (appointment_type_id, res_users_id)
        SELECT
            src.area_id,
            src.user_id
        FROM dgc_appointment_type_user_rel src
        WHERE NOT EXISTS (
            SELECT 1
            FROM appointment_type_res_users_rel dst
            WHERE dst.appointment_type_id = src.area_id
              AND dst.res_users_id = src.user_id
        )
    """)
    migrated = cr.rowcount
    _logger.info(
        "Migrados %d registros nuevos (%d ya existian).",
        migrated,
        total - migrated,
    )


def _actualizar_record_rules(cr):
    """Fuerza la actualización de los domain_force de las record rules
    marcadas como noupdate='1' en security.xml.

    Estas reglas referenciaban user.dgc_area_ids.ids (campo custom
    eliminado en esta versión). El nuevo dominio usa staff_user_ids,
    que es el campo nativo de Odoo al que se migró la relación.
    """
    reglas = [
        (
            "rule_turn_by_area",
            "[('area_id.staff_user_ids', 'in', [user.id])]",
        ),
        (
            "rule_call_log_by_area",
            "[('turn_id.area_id.staff_user_ids', 'in', [user.id])]",
        ),
        (
            "rule_derivation_by_area",
            "['|', ('from_area_id.staff_user_ids', 'in', [user.id]), "
            "('to_area_id.staff_user_ids', 'in', [user.id])]",
        ),
    ]

    for nombre_xml, nuevo_dominio in reglas:
        cr.execute(
            """
            UPDATE ir_rule
               SET domain_force = %s
             WHERE id = (
                 SELECT res_id
                   FROM ir_model_data
                  WHERE module = %s
                    AND name   = %s
                    AND model  = 'ir.rule'
             )
            """,
            (nuevo_dominio, "dgc_appointment_kiosk", nombre_xml),
        )
        if cr.rowcount:
            _logger.info(
                "Record rule '%s' actualizada con nuevo domain_force.",
                nombre_xml,
            )
        else:
            _logger.warning(
                "Record rule '%s' no encontrada en la BD. "
                "Verifique que el xml_id sea correcto.",
                nombre_xml,
            )
