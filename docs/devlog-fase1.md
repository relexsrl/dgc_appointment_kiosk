# Devlog - Fase 1: Implementación Inicial

## Fecha: 2026-03-18

## Decisiones Técnicas

### Modelos
- **5 modelos principales**: `dgc.appointment.area`, `dgc.appointment.turn`, `dgc.appointment.call.log`, `dgc.appointment.derivation`, `res.config.settings` (inherit)
- **res.users inherit**: campo `dgc_area_ids` M2M para asignación de operadores a áreas
- **Turno hereda mail.thread y mail.activity.mixin** para tracking completo
- **Número de turno**: `{area.code}-{NNN}` usando ir.sequence con reset diario
- **Constraint de duplicados**: `@api.constrains` verificando DNI+área+fecha en estados pendientes
- **CUIT validation**: Algoritmo mod-11 con pesos `[5,4,3,2,7,6,5,4,3,2]`

### Seguridad
- **Odoo 19 privilege system**: `ir.module.category` → `res.groups.privilege` → `res.groups` con `privilege_id`
- **4 grupos**: kiosk_public (sin privilege), operator, area_manager, admin
- **Record rules**: operador ve solo turnos de sus áreas, admin ve todo
- **ACL matrix**: público solo crea turnos, operador lee/escribe, admin CRUD completo

### Controllers
- **3 controladores**: kiosk (público), display (público), turn_api (autenticado)
- **Rate limiting**: dict en memoria con threading.Lock, limpieza automática > 1000 entries
- **JSON-RPC**: endpoints tipo `json` para APIs, tipo `http` para páginas

### Frontend
- **Kiosco y display**: Vanilla JS (NO OWL) - páginas públicas no cargan web client
- **Backoffice**: OWL service para bus notifications en el backend
- **Sonido**: Web Audio API con 3 tonos a 440Hz
- **CSS**: SCSS con custom properties para theming

### Configuración
- **16 parámetros** vía `res.config.settings` con `config_parameter`
- **Defaults** en `data/default_config_data.xml` con `noupdate=1`
- **Cron**: cierre automático de turnos pendientes a las 03:00

## Archivos Creados
- `__manifest__.py`, `__init__.py`
- `models/`: 6 archivos (area, turn, call_log, derivation, config, res_users)
- `wizards/`: wizard de derivación + vista
- `security/`: security.xml + ir.model.access.csv
- `data/`: secuencia, cron, config defaults
- `views/`: 6 archivos de vistas + menú
- `templates/`: kiosk + display (QWeb standalone)
- `controllers/`: 3 controladores
- `static/src/js/`: kiosk.js, display.js, backoffice.js
- `static/src/css/`: kiosk.scss, display.scss
- `report/`: report action + QWeb template
- `tests/`: 6 archivos de tests (~50 casos)

## Trabajo Diferido
- i18n/es.po: traducción a generar post-instalación
- Integración real con bus longpolling (requiere test con Odoo corriendo)
- Logo personalizado DGC (usando placeholder)
- Optimización de queries en computed fields con high traffic
