# PRD — Sistema de Turnos con Kiosco para Odoo 19
## Módulo `dgc_appointment_kiosk`

**Versión del documento**: 1.1.0  
**Fecha**: 18 de marzo de 2026  
**Autor**: Equipo de Producto — DGC (Dirección General de Catastro)  
**Estado**: Borrador para revisión  
**Plataforma objetivo**: Odoo 19 — Odoo.sh (Cloud)

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Declaración del Problema](#2-declaración-del-problema)
3. [Objetivos y Métricas de Éxito](#3-objetivos-y-métricas-de-éxito)
4. [User Personas](#4-user-personas)
5. [User Stories](#5-user-stories)
6. [Requisitos Funcionales](#6-requisitos-funcionales)
7. [Requisitos No Funcionales](#7-requisitos-no-funcionales)
8. [Arquitectura Técnica](#8-arquitectura-técnica)
9. [Modelo de Datos](#9-modelo-de-datos)
10. [Wireframes / Mockups](#10-wireframes--mockups)
11. [User Flows](#11-user-flows)
12. [Seguridad y Permisos](#12-seguridad-y-permisos)
13. [Especificación de API](#13-especificación-de-api)
14. [Dependencias e Integraciones](#14-dependencias-e-integraciones)
15. [Estrategia de Testing](#15-estrategia-de-testing)
16. [Plan de Despliegue](#16-plan-de-despliegue)
17. [Roadmap y Fases](#17-roadmap-y-fases)
18. [Preguntas Abiertas y Supuestos](#18-preguntas-abiertas-y-supuestos)
19. [Riesgos y Mitigaciones](#19-riesgos-y-mitigaciones)

---

## 1. Resumen Ejecutivo

La Dirección General de Catastro (DGC) opera actualmente un sistema de gestión de turnos presenciales desarrollado en PHP. Este sistema, aunque funcional (con más de 5.400 registros históricos), presenta limitaciones de mantenimiento, integración y escalabilidad. La institución ha decidido migrar sus operaciones al ecosistema Odoo 19, alojado en Odoo.sh.

Este documento define los requisitos para el módulo **`dgc_appointment_kiosk`**, un sistema completo de gestión de turnos presenciales que incluye: un kiosco touchscreen de auto-registro para ciudadanos, un panel de operarios para llamado y atención de turnos, una pantalla pública de visualización para sala de espera, y un backoffice completo de configuración, reportes y auditoría.

El sistema actual de PHP **no será migrado** — no se trasladarán datos históricos. El nuevo módulo arrancará limpio dentro de Odoo 19 y se comunicará con dispositivos locales (kioscos y pantallas) mediante conexión HTTPS a la instancia cloud de Odoo.sh.

La solución hereda y extiende el módulo nativo `appointment` de Odoo 19, reutilizando su infraestructura de citas donde sea posible y agregando las funcionalidades específicas de turnero presencial, segregación por área y visualización en tiempo real.

---

## 2. Declaración del Problema

### Situación Actual

La DGC gestiona la atención al público mediante un sistema de turnos PHP independiente que presenta las siguientes limitaciones:

- **Aislamiento tecnológico**: el sistema de turnos no se integra con los demás procesos administrativos de la DGC, que están migrando a Odoo 19.
- **Mantenimiento costoso**: al ser un desarrollo PHP a medida, requiere mantenimiento especializado fuera del ecosistema Odoo, duplicando esfuerzos de infraestructura.
- **Funcionalidades limitadas**: el sistema actual carece de reportes estadísticos avanzados, gestión granular de permisos por área, trazabilidad completa de derivaciones, y dashboards en tiempo real.
- **Escalabilidad reducida**: no está diseñado para soportar múltiples sucursales, áreas adicionales o integraciones futuras (WhatsApp, app móvil, citas previas).
- **Conectividad frágil**: la dependencia del servidor local limita la disponibilidad del servicio y dificulta la supervisión remota.

### Necesidad

Centralizar la gestión de turnos dentro de Odoo 19 (Odoo.sh) para unificar la atención al público con los procesos administrativos de la DGC, ganando en reportería, trazabilidad, seguridad por roles, mantenibilidad y capacidad de expansión futura.

---

## 3. Objetivos y Métricas de Éxito

### Objetivos Primarios

| # | Objetivo | Métrica | Meta |
|---|----------|---------|------|
| O1 | Centralizar turnos en Odoo 19 | % de atenciones registradas en Odoo | 100% a los 30 días del go-live |
| O2 | Reducir el tiempo promedio de espera | Minutos promedio desde generación hasta atención | Reducción del 15% respecto al primer mes de operación |
| O3 | Mantener la experiencia del ciudadano | Tasa de uso exitoso del kiosco (turnos generados sin asistencia) | ≥ 95% |
| O4 | Mejorar la visibilidad operativa | Dashboards y reportes disponibles en tiempo real | 100% de KPIs definidos visibles |
| O5 | Segregación efectiva por área | Incidentes de acceso a datos de área ajena | 0 incidentes |

### Objetivos Secundarios

| # | Objetivo | Métrica | Meta |
|---|----------|---------|------|
| O6 | Trazabilidad de derivaciones | % de derivaciones con motivo registrado | 100% |
| O7 | Reducir tasa de "no se presentó" | % de no-shows sobre turnos generados | Reducción del 10% en 3 meses |
| O8 | Habilitar supervisión remota | Administradores pueden consultar estado desde cualquier ubicación | Sí, vía Odoo.sh |

---

## 4. User Personas

### Persona 1: Ciudadano Contribuyente

- **Nombre**: María González, 58 años
- **Rol**: Contribuyente que acude presencialmente a la DGC
- **Contexto**: Necesita realizar un trámite catastral (consulta de plano, certificado de dominio, etc.). No tiene experiencia técnica avanzada. Puede tener dificultades de visión o motricidad fina.
- **Necesidades**: Sacar un turno rápidamente sin asistencia, saber cuánto falta para ser atendida, identificar claramente cuándo la llaman.
- **Frustraciones**: Interfaces confusas, letras pequeñas, tiempos de espera inciertos, no escuchar cuando la llaman.

### Persona 2: Operario de Atención al Público

- **Nombre**: Carlos Méndez, 35 años
- **Rol**: Empleado de ventanilla en el área de Geodesia y Cartografía
- **Contexto**: Atiende entre 20 y 40 personas por día. Usa una PC de escritorio con Odoo. Necesita eficiencia para avanzar en la cola.
- **Necesidades**: Ver solo los turnos de su área, llamar al siguiente turno con un clic, registrar observaciones, derivar cuando corresponda.
- **Frustraciones**: Ver turnos que no le corresponden, perder tiempo buscando el siguiente turno, no poder registrar por qué derivó a un ciudadano.

### Persona 3: Responsable de Área

- **Nombre**: Laura Ferreyra, 45 años
- **Rol**: Jefa del Departamento de Geodesia y Cartografía
- **Contexto**: Supervisa a 4 operarios. Necesita datos para tomar decisiones de asignación de personal y detección de cuellos de botella.
- **Necesidades**: Ver estadísticas de su área, monitorear tiempos de espera en tiempo real, identificar horas pico, revisar tasa de derivaciones.
- **Frustraciones**: No tener datos para justificar necesidades de personal, enterarse tarde de problemas operativos.

### Persona 4: Administrador del Sistema

- **Nombre**: Leandro Ruiz, 30 años
- **Rol**: Responsable de TI y administración del sistema Odoo
- **Contexto**: Configura el módulo, crea áreas, asigna usuarios, ajusta horarios. Tiene acceso total al sistema.
- **Necesidades**: Configuración flexible, auditoría completa, visión global de todas las áreas, reportes exportables.
- **Frustraciones**: Configuraciones rígidas que requieren modificar código, falta de logs para auditoría.

---

## 5. User Stories

### Prioridad: Must-Have (MVP)

| ID | Rol | Historia | Criterios de Aceptación |
|----|-----|----------|------------------------|
| US-01 | Ciudadano | Como ciudadano, quiero ingresar mi DNI en el kiosco para obtener un turno de atención | 1. El kiosco muestra teclado numérico virtual. 2. Acepta DNI (7-8 dígitos) y CUIT (11 dígitos). 3. Valida formato en tiempo real. 4. Muestra error claro si el formato es inválido. |
| US-02 | Ciudadano | Como ciudadano, quiero seleccionar el área donde necesito atención para dirigirme al lugar correcto | 1. Muestra solo áreas activas. 2. Cada área muestra nombre y ubicación física. 3. Al seleccionar, avanza al paso de confirmación. |
| US-03 | Ciudadano | Como ciudadano, quiero recibir confirmación de mi turno con número asignado para saber que estoy en la cola | 1. Muestra número de turno generado. 2. Muestra área y ubicación. 3. Muestra cantidad de turnos en espera. 4. Muestra tiempo estimado de espera. 5. El kiosco se reinicia automáticamente después del timeout configurado. |
| US-04 | Operario | Como operario, quiero ver la lista de turnos pendientes de mi área para saber a quién atender | 1. Lista ordenada por hora de ingreso (FIFO). 2. Solo muestra turnos del área del operario. 3. Muestra DNI, hora de ingreso y estado. 4. Se actualiza en tiempo real. |
| US-05 | Operario | Como operario, quiero llamar al siguiente turno para que el ciudadano se acerque al mostrador | 1. Botón "Llamar" cambia estado a "LLAMANDO". 2. Se envía notificación a pantalla pública. 3. La pantalla reproduce sonido y muestra parpadeo. 4. Se registra timestamp del llamado. |
| US-06 | Operario | Como operario, quiero marcar un turno como "Atendiendo" para indicar que el ciudadano llegó | 1. Botón "Atendiendo" cambia estado. 2. El turno desaparece de la pantalla pública. 3. Se registra hora de inicio de atención. |
| US-07 | Operario | Como operario, quiero finalizar un turno para liberar el mostrador y atender al siguiente | 1. Botón "Finalizar" cambia estado a "FINALIZADO". 2. Se calcula y registra duración real de atención. 3. El turno se mueve a historial. |
| US-08 | Operario | Como operario, quiero marcar "No se presentó" cuando un ciudadano no acude tras ser llamado | 1. Botón disponible después de al menos 1 llamado. 2. Cambia estado a "NO PRESENTADO". 3. Se registra cantidad de llamados realizados. |
| US-09 | Operario | Como operario, quiero derivar un turno a otra área con un motivo registrado | 1. Wizard de derivación solicita área destino y motivo (obligatorio). 2. El turno aparece en la cola del área destino. 3. Se mantiene historial completo (área origen, destino, motivo, usuario, timestamp). 4. El área receptora recibe notificación. |
| US-10 | Ciudadano (display) | Como ciudadano en sala de espera, quiero ver en una pantalla grande cuál turno están llamando | 1. Pantalla fullscreen sin menús de Odoo. 2. Turno llamado destacado con fondo verde y parpadeo. 3. Lista de turnos en espera debajo. 4. Sonido al llamar. 5. Actualización en tiempo real (< 3 segundos). |
| US-11 | Administrador | Como administrador, quiero configurar áreas de atención con nombre, ubicación y responsables | 1. CRUD de áreas con nombre, ubicación, abreviatura, color. 2. Asignación many2many de usuarios responsables. 3. Activar/desactivar áreas. |
| US-12 | Administrador | Como administrador, quiero configurar horarios de atención para controlar cuándo opera el sistema | 1. Hora inicio y fin por día de semana. 2. Tiempo promedio estimado por turno. 3. Configuración de feriados/horarios especiales. |
| US-13 | Administrador | Como administrador, quiero que los operarios solo vean los turnos de su área asignada | 1. Record rules filtran por `area_id` del usuario. 2. Operarios no pueden acceder a turnos de otras áreas. 3. Administradores ven todo sin filtro. |

### Prioridad: Should-Have

| ID | Rol | Historia | Criterios de Aceptación |
|----|-----|----------|------------------------|
| US-14 | Operario | Como operario, quiero llamar a un turno múltiples veces si el ciudadano no responde | 1. Botón "Volver a llamar" registra cada llamado con timestamp. 2. Intensidad visual aumenta en pantalla pública (parpadeo más rápido, color naranja). 3. Se registra conteo total de llamados. |
| US-15 | Operario | Como operario, quiero agregar observaciones durante la atención | 1. Campo de texto editable durante y después de la atención. 2. Las observaciones quedan registradas en el turno. |
| US-16 | Responsable | Como responsable de área, quiero ver un dashboard con KPIs en tiempo real de mi área | 1. Turnos generados hoy. 2. Turnos en espera ahora. 3. Turnos finalizados hoy. 4. Tiempo promedio de atención hoy. 5. Datos filtrados por área del usuario. |
| US-17 | Responsable | Como responsable, quiero reportes estadísticos de mi área | 1. Cantidad de atendidos por día/semana/mes. 2. Tiempo promedio de espera y atención. 3. Tasa de no-shows. 4. Ranking de demanda. 5. Exportable a Excel. |
| US-18 | Administrador | Como administrador, quiero configurar el kiosco (timeout, campos opcionales, mensajes) | 1. Timeout configurable (default 30s). 2. Email y observaciones como campos opcionales/obligatorios. 3. Mensaje de bienvenida personalizable. |
| US-19 | Administrador | Como administrador, quiero configurar la pantalla de visualización (sonidos, colores, mensajes) | 1. Subida de archivos MP3/WAV para sonido de llamada. 2. Velocidad de parpadeo configurable. 3. Mensajes rotativos informativos editables. 4. Logo y branding personalizable. |
| US-20 | Administrador | Como administrador, quiero ver el historial completo de turnos con filtros avanzados | 1. Filtro por rango de fechas, área, estado, DNI, operario. 2. Exportación a Excel. 3. Paginación para grandes volúmenes. |
| US-21 | Operario | Como operario, quiero ver el tiempo transcurrido desde la generación del turno y desde el último llamado | 1. Timer visible en la vista de turno activo. 2. Se actualiza en tiempo real. |

### Prioridad: Could-Have (Fase 2)

| ID | Rol | Historia | Criterios de Aceptación |
|----|-----|----------|------------------------|
| US-22 | Ciudadano | Como ciudadano, quiero recibir un ticket impreso con mi número de turno y código QR | 1. Impresora térmica genera ticket. 2. QR code para consulta de estado. |
| US-23 | Ciudadano | Como ciudadano, quiero recibir una notificación por WhatsApp cuando falten X turnos | 1. Integración con WhatsApp Business API. 2. Configurable cuántos turnos antes notificar. |
| US-24 | Administrador | Como administrador, quiero una API REST para consultar estado de turnos desde otros sistemas | 1. Endpoints documentados. 2. Autenticación por token. |
| US-25 | Administrador | Como administrador, quiero habilitar TTS (text-to-speech) para anunciar turnos por altavoz | 1. Mensaje de voz sintetizado: "Turno [número], [área]". 2. Configurable por área. |

### Prioridad: Won't-Have (Fase 3)

| ID | Rol | Historia |
|----|-----|----------|
| US-26 | Ciudadano | Como ciudadano, quiero agendar un turno con cita previa desde una app móvil |
| US-27 | Administrador | Como administrador, quiero gestionar turnos para múltiples sucursales desde una sola instancia |
| US-28 | Ciudadano | Como ciudadano, quiero confirmar mi asistencia respondiendo un SMS |

---

## 6. Requisitos Funcionales

### RF-01: Módulo Base

| ID | Requisito | Prioridad |
|----|-----------|-----------|
| RF-01.1 | El módulo se instala como addon de Odoo 19 con nombre técnico `dgc_appointment_kiosk` | Must |
| RF-01.2 | Depende de los módulos nativos `appointment`, `base`, `web`, `bus`, `mail` | Must |
| RF-01.3 | El módulo hereda funcionalidad de `appointment` y la extiende con gestión de turnos presenciales | Must |
| RF-01.4 | La versión del manifest sigue el formato `19.0.1.0.0` | Must |
| RF-01.5 | Licencia LGPL-3 | Must |

### RF-02: Kiosco de Auto-registro

| ID | Requisito | Prioridad |
|----|-----------|-----------|
| RF-02.1 | Interfaz fullscreen sin menú ni barra de navegación de Odoo | Must |
| RF-02.2 | Accesible vía URL pública `/kiosk/checkin` sin autenticación de usuario Odoo | Must |
| RF-02.3 | Pantalla de bienvenida con logo DGC y botón o detección de toque para iniciar | Must |
| RF-02.4 | Input de DNI/CUIT con teclado numérico virtual (botones grandes, mínimo 60x60px) | Must |
| RF-02.5 | Validación de formato argentino: DNI 7-8 dígitos, CUIT/CUIL 11 dígitos con dígito verificador | Must |
| RF-02.6 | Selección de área con lista de áreas activas mostrando nombre + ubicación física | Must |
| RF-02.7 | Generación de turno con número secuencial único por día (reinicio diario) | Must |
| RF-02.8 | Pantalla de confirmación con: número de turno, área, ubicación, turnos en espera, tiempo estimado | Must |
| RF-02.9 | Reinicio automático a pantalla de bienvenida tras timeout configurable (default: 30 segundos) | Must |
| RF-02.10 | Prevención de duplicados: mismo DNI no puede sacar turno en misma área si tiene uno pendiente | Must |
| RF-02.11 | Rate limiting: máximo 1 turno cada 30 segundos por IP | Must |
| RF-02.12 | Campo opcional para email del ciudadano | Should |
| RF-02.13 | Campo opcional para observaciones | Should |
| RF-02.14 | Cache local en navegador (localStorage) para áreas disponibles y configuración | Should |
| RF-02.15 | Mensaje de error amigable si no hay conexión a internet | Should |
| RF-02.16 | Búsqueda de datos del ciudadano en `res.partner` por DNI/CUIT para autocompletar nombre | Should |
| RF-02.17 | **Control de capacidad diaria por área**: el kiosco calcula el tope máximo de turnos como `(hora_fin - hora_inicio) / avg_service_time`. Ej: 240min / 15min = 16 turnos. Al alcanzar el tope, el área se muestra como "Cupos agotados" y no permite generar más turnos | Must |
| RF-02.18 | **Integración con `res.partner` sin duplicados**: al ingresar CUIT/DNI, buscar en `res.partner` por campo `vat`. Si existe, vincular y autocompletar. Si no existe, crear nuevo `res.partner`. Nunca duplicar por CUIT | Must |
| RF-02.19 | **Detección de email conflictivo**: si el CUIT ya existe en `res.partner` y el email ingresado difiere del registrado, mostrar el email existente (parcialmente oculto, ej: `ana***@hotmail.com`) y preguntar si desea actualizarlo por el nuevo. Si confirma, actualizar `res.partner.email` | Must |
| RF-02.20 | **Turnos múltiples (configurable)**: booleano `allow_multiple_turns` en configuración general. Si está activo, un mismo ciudadano puede sacar turnos en distintas áreas o en distintos horarios del mismo día. Si está inactivo, solo puede tener 1 turno pendiente global por día | Should |

### RF-03: Gestión de Permisos por Área

| ID | Requisito | Prioridad |
|----|-----------|-----------|
| RF-03.1 | Cada usuario operario tiene asignada una o más áreas (`area_ids` many2many en `res.users`) | Must |
| RF-03.2 | Record rules filtran automáticamente turnos por áreas asignadas al usuario | Must |
| RF-03.3 | Usuarios con grupo "Administrador de Turnos" ven todos los turnos sin filtro de área | Must |
| RF-03.4 | La derivación de turno cambia el `area_id` y crea registro en `dgc.appointment.derivation` | Must |
| RF-03.5 | Al derivar: motivo obligatorio, notificación al área receptora, historial completo | Must |
| RF-03.6 | Las vistas, reportes y dashboards respetan la segregación por área | Must |

### RF-04: Panel del Operario (Llamador)

| ID | Requisito | Prioridad |
|----|-----------|-----------|
| RF-04.1 | Lista de turnos del día filtrados por área del operario, ordenados FIFO | Must |
| RF-04.2 | Estados del turno: `new`, `waiting`, `calling`, `serving`, `done`, `derived`, `no_show` | Must |
| RF-04.3 | Botón "Llamar" → estado `calling`, notificación a pantalla, registro en `dgc.appointment.call.log` | Must |
| RF-04.4 | Botón "Atendiendo" → estado `serving`, registro de hora de inicio de atención real | Must |
| RF-04.5 | Botón "Finalizar" → estado `done`, cálculo de duración real (serving → done) | Must |
| RF-04.6 | Botón "No se presentó" → estado `no_show`, disponible tras al menos 1 llamado | Must |
| RF-04.7 | Botón "Derivar" → wizard con área destino (requerida) y motivo (requerido) | Must |
| RF-04.8 | Campo de observaciones editable durante y después de la atención | Should |
| RF-04.9 | Indicador de tiempo transcurrido desde generación del turno | Should |
| RF-04.10 | Indicador de tiempo desde último llamado | Should |
| RF-04.11 | Llamados múltiples: cada llamado se registra con timestamp, máximo 3 antes de permitir "No se presentó" (configurable) | Should |
| RF-04.12 | Filtros por estado, fecha, DNI | Should |
| RF-04.13 | Vista kanban por estado + vista lista, ambas configurables | Should |
| RF-04.14 | Contador de turnos pendientes por área visible en la interfaz | Should |

### RF-05: Pantalla Pública de Visualización

| ID | Requisito | Prioridad |
|----|-----------|-----------|
| RF-05.1 | Pantalla fullscreen sin elementos de navegación de Odoo | Must |
| RF-05.2 | Accesible vía URL pública `/display/queue` sin autenticación | Must |
| RF-05.3 | Sección superior destacada: turno actualmente llamado (fondo verde, texto grande, parpadeo) | Must |
| RF-05.4 | Información del turno llamado: número + DNI parcial + área/mostrador | Must |
| RF-05.5 | Sección inferior: lista de últimos 10-15 turnos en espera | Must |
| RF-05.6 | Sonido automático al llamar turno (3 pitidos o archivo MP3/WAV configurable) | Must |
| RF-05.7 | Actualización en tiempo real vía Odoo Bus (longpolling), latencia < 3 segundos | Must |
| RF-05.8 | Logo y branding institucional DGC | Must |
| RF-05.9 | Legible desde 5+ metros de distancia (fuentes ≥ 48px para turno llamado, ≥ 24px para cola) | Must |
| RF-05.10 | Parámetro URL para filtrar por área: `/display/queue?area_id=X` | Should |
| RF-05.11 | Intensidad visual creciente en llamados múltiples (parpadeo rápido, color naranja al 2do llamado, rojo al 3ro) | Should |
| RF-05.12 | Mensajes rotativos informativos en franja inferior (horarios, documentación requerida, etc.) | Should |
| RF-05.13 | TTS opcional: "Turno [número], [área]" | Could |

### RF-06: Configuración en Backoffice

| ID | Requisito | Prioridad |
|----|-----------|-----------|
| RF-06.1 | Configuración de horarios de atención: hora inicio, hora fin, por día de semana | Must |
| RF-06.2 | CRUD de áreas: nombre, ubicación, abreviatura, color, usuarios responsables (m2m) | Must |
| RF-06.3 | Activar/desactivar áreas en tiempo real (campo `active` booleano) | Must |
| RF-06.4 | Tiempo promedio estimado por turno (para cálculo de estimaciones en kiosco) | Should |
| RF-06.5 | Configuración de kiosco: timeout, campos obligatorios/opcionales, mensaje de bienvenida | Should |
| RF-06.6 | Configuración de pantalla: sonidos, velocidad de parpadeo, mensajes rotativos | Should |
| RF-06.7 | Formato de número de turno: secuencial por día, por área, con prefijo | Should |
| RF-06.8 | Configuración de feriados y horarios especiales | Could |
| RF-06.9 | Número de mostradores/boxes por área | Could |

### RF-07: Reportes e Historial

| ID | Requisito | Prioridad |
|----|-----------|-----------|
| RF-07.1 | Historial de turnos con filtros: rango de fechas, área, estado, DNI, operario | Must |
| RF-07.2 | Exportación a Excel de registros filtrados | Must |
| RF-07.3 | Dashboard con KPIs: turnos generados hoy, en espera ahora, finalizados hoy, tiempo promedio | Should |
| RF-07.4 | Reporte de atendidos por día/semana/mes (graph view) | Should |
| RF-07.5 | Reporte de tiempo promedio de espera y atención por área | Should |
| RF-07.6 | Reporte de tasa de no-shows | Should |
| RF-07.7 | Reporte de derivaciones (origen → destino, motivos frecuentes) | Should |
| RF-07.8 | Reporte de horas pico de mayor afluencia | Could |
| RF-07.9 | Ranking de áreas con más demanda | Could |
| RF-07.10 | Gráfico de evolución temporal del día (graph view) | Could |
| RF-07.11 | Pivot views para análisis multidimensional | Could |

---

## 7. Requisitos No Funcionales

### Performance

| ID | Requisito | Criterio |
|----|-----------|----------|
| RNF-01 | Tiempo de respuesta del kiosco (generación de turno) | < 2 segundos |
| RNF-02 | Tiempo de propagación de llamado a pantalla pública | < 3 segundos |
| RNF-03 | Carga de interfaz del kiosco desde cero | < 5 segundos con conexión estable |
| RNF-04 | Soporte de turnos simultáneos en backoffice | ≥ 50 operarios concurrentes |
| RNF-05 | Generación simultánea de turnos desde múltiples kioscos | ≥ 10 kioscos concurrentes |
| RNF-06 | Índices de base de datos en: `create_date`, `area_id`, `state`, `citizen_dni`, `date` | Obligatorio |

### Seguridad

| ID | Requisito |
|----|-----------|
| RNF-07 | Toda comunicación vía HTTPS (garantizado por Odoo.sh) |
| RNF-08 | Endpoints públicos (`/kiosk/*`, `/display/*`) con rate limiting por IP |
| RNF-09 | Segregación de datos por área mediante record rules de Odoo (enforced a nivel SQL) |
| RNF-10 | Sin exposición de datos sensibles en endpoints públicos (DNI parcialmente oculto en pantalla) |
| RNF-11 | Validación server-side de todos los inputs (DNI/CUIT formato, área activa, duplicados) |
| RNF-12 | Logs de auditoría para toda acción crítica (generación, llamado, derivación, finalización) |

### Usabilidad

| ID | Requisito |
|----|-----------|
| RNF-13 | Kiosco operable por adultos mayores: botones ≥ 60x60px, fuentes ≥ 18px, alto contraste |
| RNF-14 | Teclado numérico con spacing amplio y feedback visual al presionar |
| RNF-15 | Mensajes de error claros en español, sin jerga técnica |
| RNF-16 | Confirmaciones visuales en cada paso (cambio de color, ícono check, transición suave) |
| RNF-17 | Pantalla de visualización legible a 5+ metros: turno llamado ≥ 72px, cola ≥ 32px |
| RNF-18 | Colores con contraste WCAG 2.1 AA: ratio ≥ 4.5:1 para texto, ≥ 3:1 para elementos grandes |

### Accesibilidad

| ID | Requisito |
|----|-----------|
| RNF-19 | Cumplimiento WCAG 2.1 nivel AA para interfaces principales |
| RNF-20 | Soporte para lectores de pantalla en kiosco (aria-labels) |
| RNF-21 | Modo de alto contraste activable |
| RNF-22 | Textos escalables sin pérdida de layout |

### Escalabilidad

| ID | Requisito |
|----|-----------|
| RNF-23 | Arquitectura preparada para múltiples sucursales (campo `branch_id` futuro) |
| RNF-24 | Modelo de datos extensible para agregar campos sin migración destructiva |
| RNF-25 | Controladores con versionado de API implícito (rutas organizadas por función) |

### Compatibilidad de Hardware

| ID | Requisito |
|----|-----------|
| RNF-26 | Kiosco compatible con navegadores Chrome 90+, Firefox 90+, Edge 90+ |
| RNF-27 | Pantallas táctiles resistivas y capacitivas (Windows/Linux/Android) |
| RNF-28 | Pantalla de visualización compatible con cualquier navegador en modo fullscreen |
| RNF-29 | Audio vía parlantes USB o integrados (Web Audio API) |
| RNF-30 | (Opcional) Impresora térmica ESC/POS vía USB o red |

---

## 8. Arquitectura Técnica

### 8.1 Diagrama de Arquitectura Cloud

```
┌──────────────────────────────────────────────────────────────────────┐
│                          INTERNET (HTTPS)                            │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         ODOO.SH (Cloud)                              │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Odoo 19 Instance                                              │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌────────────────────────┐ │  │
│  │  │  Web Server   │ │  Bus/Longpoll│ │  PostgreSQL DB         │ │  │
│  │  │  (HTTP/JSON)  │ │  (Realtime)  │ │  (Managed by Odoo.sh) │ │  │
│  │  └──────┬───────┘ └──────┬───────┘ └────────────────────────┘ │  │
│  │         │                │                                     │  │
│  │  ┌──────┴────────────────┴─────────────────────────────────┐  │  │
│  │  │           dgc_appointment_kiosk module                   │  │  │
│  │  │  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌─────────────┐  │  │  │
│  │  │  │ Models  │ │ Control-│ │ QWeb     │ │ JS/OWL      │  │  │  │
│  │  │  │ (ORM)   │ │ lers    │ │ Templates│ │ Components  │  │  │  │
│  │  │  └─────────┘ └─────────┘ └──────────┘ └─────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
        │                    │                       │
        ▼                    ▼                       ▼
┌──────────────┐  ┌───────────────────┐  ┌──────────────────────┐
│   KIOSCOS    │  │  PANTALLAS DISPLAY │  │  PCs OPERARIOS       │
│  Touchscreen │  │  TV Sala Espera    │  │  Backoffice Odoo     │
│  /kiosk/     │  │  /display/queue    │  │  Sesión autenticada  │
│  checkin     │  │  (Bus Longpolling) │  │  (Bus Longpolling)   │
│  (Público)   │  │  (Público)         │  │                      │
└──────────────┘  └───────────────────┘  └──────────────────────┘
```

### 8.2 Diagrama de Componentes del Módulo

```
dgc_appointment_kiosk/
│
├── MODELOS (Python ORM)
│   ├── dgc.appointment.area ──────── Áreas de atención
│   ├── dgc.appointment.turn ──────── Turno (modelo principal)
│   ├── dgc.appointment.config ────── Configuración global (singleton)
│   ├── dgc.appointment.derivation ── Registro de derivaciones
│   ├── dgc.appointment.call.log ──── Log de cada llamado
│   └── res.users (inherit) ───────── Campo area_ids en usuarios
│
├── CONTROLADORES HTTP
│   ├── KioskController ─── /kiosk/checkin (público)
│   │                   └── /kiosk/api/turn/create (JSON, público)
│   ├── DisplayController ─ /display/queue (público)
│   │                   └── /display/api/turns (JSON, público)
│   └── TurnAPIController ─ /api/turn/call (JSON, auth=user)
│                       └── /api/turn/status (JSON, auth=user)
│
├── VISTAS XML (Backoffice)
│   ├── Turn: tree, form, kanban, calendar, pivot, graph
│   ├── Area: tree, form
│   ├── Config: form (settings)
│   ├── Dashboard: action + QWeb template
│   └── Menú principal + submenús
│
├── PLANTILLAS QWEB (Públicas)
│   ├── kiosk_main_view.xml ──── Interfaz kiosco multi-paso
│   └── display_queue_view.xml ── Pantalla sala de espera
│
├── ASSETS (Static)
│   ├── src/js/kiosk.js ──────── Lógica kiosco (vanilla JS o OWL)
│   ├── src/js/display.js ────── Lógica pantalla (Bus listener + audio)
│   ├── src/js/backoffice.js ──── Actualización tiempo real operarios
│   ├── src/css/kiosk.scss ────── Estilos kiosco (alto contraste, touch)
│   ├── src/css/display.scss ──── Estilos pantalla (fuentes grandes)
│   └── src/audio/ ────────────── Sonidos default de llamada
│
├── SEGURIDAD
│   ├── security.xml ──────────── Grupos + record rules
│   └── ir.model.access.csv ──── Permisos CRUD
│
├── DATA
│   ├── ir_sequence_data.xml ──── Secuencia de turnos
│   ├── ir_cron_data.xml ──────── Cron de cierre de turnos al final del día
│   └── default_config_data.xml ─ Configuración por defecto
│
└── TESTS
    ├── test_turn_creation.py
    ├── test_turn_workflow.py
    ├── test_derivation.py
    ├── test_security_rules.py
    └── test_controllers.py
```

### 8.3 Estructura de Directorios del Módulo

```
dgc_appointment_kiosk/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── dgc_appointment_area.py
│   ├── dgc_appointment_turn.py
│   ├── dgc_appointment_config.py
│   ├── dgc_appointment_derivation.py
│   ├── dgc_appointment_call_log.py
│   └── res_users.py
├── wizards/
│   ├── __init__.py
│   └── dgc_turn_derive_wizard.py
├── controllers/
│   ├── __init__.py
│   ├── kiosk.py
│   ├── display.py
│   └── turn_api.py
├── views/
│   ├── dgc_appointment_turn_views.xml
│   ├── dgc_appointment_area_views.xml
│   ├── dgc_appointment_config_views.xml
│   ├── dgc_appointment_derivation_views.xml
│   ├── dgc_dashboard_views.xml
│   └── menu_views.xml
├── security/
│   ├── security.xml
│   └── ir.model.access.csv
├── data/
│   ├── ir_sequence_data.xml
│   ├── ir_cron_data.xml
│   └── default_config_data.xml
├── report/
│   ├── dgc_turn_report.xml
│   └── dgc_turn_report_template.xml
├── static/
│   ├── description/
│   │   └── icon.png
│   └── src/
│       ├── js/
│       │   ├── kiosk.js
│       │   ├── display.js
│       │   └── backoffice.js
│       ├── css/
│       │   ├── kiosk.scss
│       │   └── display.scss
│       ├── xml/
│       │   ├── kiosk_templates.xml
│       │   └── display_templates.xml
│       └── audio/
│           └── turn_call_default.mp3
├── templates/
│   ├── kiosk_main_view.xml
│   └── display_queue_view.xml
└── tests/
    ├── __init__.py
    ├── test_turn_creation.py
    ├── test_turn_workflow.py
    ├── test_derivation.py
    ├── test_security_rules.py
    └── test_controllers.py
```

### 8.4 Flujo de Datos: Kiosco → Odoo.sh → Display

```
KIOSCO                        ODOO.SH                         DISPLAY
  │                              │                                │
  │  POST /kiosk/api/turn/create │                                │
  │  {dni, area_id}              │                                │
  │─────────────────────────────►│                                │
  │                              │ 1. Validar DNI formato         │
  │                              │ 2. Verificar área activa       │
  │                              │ 3. Check capacidad diaria área │
  │                              │ 4. Check duplicados (configur.)│
  │                              │ 5. Buscar/crear res.partner    │
  │                              │    (dedup por CUIT/DNI)        │
  │                              │ 6. Crear dgc.appointment.turn  │
  │                              │ 7. Asignar número secuencial   │
  │  200 OK                      │                                │
  │  {turn_number, area_name,    │                                │
  │   queue_position, est_wait}  │                                │
  │◄─────────────────────────────│                                │
  │                              │                                │
  │                              │  ── Operario: "Llamar" ──     │
  │                              │                                │
  │                              │ 1. Cambiar estado → calling    │
  │                              │ 2. Crear call.log              │
  │                              │ 3. Bus notification:           │
  │                              │    channel: dgc_turn_area_{id} │
  │                              │    channel: dgc_turn_global    │
  │                              │    payload: {action: 'call',   │
  │                              │     turn_number, citizen,      │
  │                              │     area, call_count}          │
  │                              │─────────────────────────────►  │
  │                              │                                │
  │                              │                   Bus listener │
  │                              │                   receives msg │
  │                              │                   → Show turn  │
  │                              │                   → Play sound │
  │                              │                   → Animate    │
  │                              │                                │
```

---

## 9. Modelo de Datos

### 9.1 Diagrama ERD

```
┌─────────────────────────┐     ┌──────────────────────────────────────┐
│  dgc.appointment.area   │     │      dgc.appointment.turn            │
├─────────────────────────┤     ├──────────────────────────────────────┤
│ id (PK)                 │◄──┐ │ id (PK)                              │
│ name: Char              │   │ │ name: Char (computed display_name)   │
│ code: Char (abreviatura)│   │ │ turn_number: Char (secuencial/día)  │
│ location: Char          │   ├─│ area_id: Many2one → area (FK)       │
│ color: Integer          │   │ │ citizen_dni: Char                    │
│ active: Boolean         │   │ │ citizen_name: Char                   │
│ avg_service_time: Int   │   │ │ citizen_email: Char                  │
│ max_counters: Integer   │   │ │ notes: Text (observaciones)         │
│ welcome_message: Text   │   │ │ state: Selection                     │
│ sequence: Integer       │   │ │ date: Date                           │
│ user_ids: M2M → users   │   │ │ create_date: Datetime               │
│ company_id: M2O         │   │ │ call_date: Datetime (último llamado)│
└─────────────────────────┘   │ │ serve_date: Datetime (inicio atenc.)│
        ▲                     │ │ done_date: Datetime (finalización)  │
        │                     │ │ duration: Float (minutos, computed) │
        │                     │ │ call_count: Integer (computed)      │
        │ M2M                 │ │ operator_id: M2O → res.users        │
┌───────┴─────────────────┐   │ │ partner_id: M2O → res.partner      │
│     res.users            │   │ │ company_id: M2O                     │
│ (inherit)                │   │ └──────────────────────────────────────┘
├──────────────────────────┤   │          │               │
│ dgc_area_ids: M2M → area │   │          │1              │1
└──────────────────────────┘   │          │               │
                               │          ▼ *             ▼ *
                               │  ┌──────────────┐ ┌─────────────────────┐
                               │  │ dgc.appoint- │ │ dgc.appointment.    │
                               │  │ ment.call.log│ │ derivation          │
                               │  ├──────────────┤ ├─────────────────────┤
                               │  │ id (PK)      │ │ id (PK)             │
                               │  │ turn_id (FK) │ │ turn_id (FK)        │
                               │  │ call_datetime│ │ from_area_id (FK)───┘
                               │  │ operator_id  │ │ to_area_id (FK)─────┘
                               │  │ call_number  │ │ reason: Text        │
                               │  └──────────────┘ │ user_id: M2O        │
                               │                   │ derivation_date     │
                               │                   └─────────────────────┘

┌─────────────────────────────────┐
│  dgc.appointment.config         │
│  (Singleton — res.config.settings│
│   inherit)                       │
├─────────────────────────────────┤
│ kiosk_timeout: Integer (seg)    │
│ kiosk_email_required: Boolean   │
│ kiosk_notes_required: Boolean   │
│ kiosk_welcome_text: Html        │
│ display_sound: Binary (mp3/wav) │
│ display_sound_filename: Char    │
│ display_blink_speed: Selection  │
│ display_scroll_messages: Text   │
│ display_logo: Binary            │
│ turn_prefix: Char               │
│ turn_reset_frequency: Selection │
│ max_calls_before_noshow: Integer│
│ office_hour_start: Float        │
│ office_hour_end: Float          │
│ avg_turn_duration: Integer (min)│
│ allow_multiple_turns: Boolean   │
│ branding_logo: Binary           │
│ branding_name: Char             │
│ branding_primary_color: Char    │
│ branding_bg_color: Char         │
└─────────────────────────────────┘
```

### 9.2 Especificación Detallada de Modelos

#### `dgc.appointment.area` — Áreas de Atención

```python
class DgcAppointmentArea(models.Model):
    _name = 'dgc.appointment.area'
    _description = 'Área de Atención DGC'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre', required=True)                           # "Geodesia y Cartografía"
    code = fields.Char(string='Abreviatura', required=True, size=10)             # "GEO"
    location = fields.Char(string='Ubicación Física')                            # "2do Piso"
    color = fields.Integer(string='Color')                                        # Para vista kanban
    active = fields.Boolean(string='Activa', default=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    avg_service_time = fields.Integer(string='Tiempo Promedio Atención (min)', default=15)
    max_counters = fields.Integer(string='Mostradores Disponibles', default=1)
    welcome_message = fields.Text(string='Mensaje Bienvenida Kiosco')
    user_ids = fields.Many2many(
        'res.users',
        'dgc_area_user_rel',
        'area_id', 'user_id',
        string='Usuarios Responsables'
    )
    turn_ids = fields.One2many('dgc.appointment.turn', 'area_id', string='Turnos')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    # Computed
    pending_turn_count = fields.Integer(compute='_compute_pending_count', string='Pendientes Hoy')
    max_daily_turns = fields.Integer(compute='_compute_max_daily_turns', string='Máx. Turnos/Día')
    remaining_turns_today = fields.Integer(compute='_compute_remaining_turns', string='Cupos Restantes Hoy')

    @api.depends('avg_service_time')
    def _compute_max_daily_turns(self):
        """Calcula tope diario: (hora_fin - hora_inicio) / avg_service_time.
        Ej: (11:30 - 7:30) = 240min / 15min = 16 turnos máx.
        Usa horarios de config global. Multiplica por max_counters si hay boxes paralelos.
        """
        ICP = self.env['ir.config_parameter'].sudo()
        hour_start = float(ICP.get_param('dgc_appointment_kiosk.office_hour_start', 7.5))
        hour_end = float(ICP.get_param('dgc_appointment_kiosk.office_hour_end', 11.5))
        total_minutes = (hour_end - hour_start) * 60
        for area in self:
            if area.avg_service_time > 0:
                area.max_daily_turns = int(total_minutes / area.avg_service_time) * area.max_counters
            else:
                area.max_daily_turns = 0

    def _compute_remaining_turns(self):
        """Cupos restantes = max_daily_turns - turnos generados hoy en esta área."""
        today = fields.Date.today()
        for area in self:
            today_count = self.env['dgc.appointment.turn'].search_count([
                ('area_id', '=', area.id),
                ('date', '=', today),
                ('state', 'not in', ['no_show']),  # no-shows no consumen cupo
            ])
            area.remaining_turns_today = max(0, area.max_daily_turns - today_count)
```

#### `dgc.appointment.turn` — Turno Principal

```python
class DgcAppointmentTurn(models.Model):
    _name = 'dgc.appointment.turn'
    _description = 'Turno de Atención DGC'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date asc'
    _rec_name = 'display_name'

    turn_number = fields.Char(string='Número de Turno', readonly=True, copy=False, index=True)
    area_id = fields.Many2one('dgc.appointment.area', string='Área', required=True, index=True, tracking=True)
    citizen_dni = fields.Char(string='DNI/CUIT', required=True, index=True)
    citizen_name = fields.Char(string='Nombre Completo')
    citizen_email = fields.Char(string='Email')
    partner_id = fields.Many2one('res.partner', string='Contacto Asociado')
    notes = fields.Text(string='Observaciones')
    state = fields.Selection([
        ('new', 'Nuevo'),
        ('waiting', 'En Espera'),
        ('calling', 'Llamando'),
        ('serving', 'Atendiendo'),
        ('done', 'Finalizado'),
        ('derived', 'Derivado'),
        ('no_show', 'No se Presentó'),
    ], default='new', required=True, tracking=True, index=True)

    date = fields.Date(string='Fecha', default=fields.Date.today, index=True)
    call_date = fields.Datetime(string='Último Llamado')
    serve_date = fields.Datetime(string='Inicio Atención')
    done_date = fields.Datetime(string='Fin Atención')

    # Computed
    duration = fields.Float(string='Duración Atención (min)', compute='_compute_duration', store=True)
    wait_time = fields.Float(string='Tiempo Espera (min)', compute='_compute_wait_time', store=True)
    call_count = fields.Integer(string='Llamados Realizados', compute='_compute_call_count', store=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)

    # Relaciones
    operator_id = fields.Many2one('res.users', string='Operario', tracking=True)
    call_log_ids = fields.One2many('dgc.appointment.call.log', 'turn_id', string='Historial Llamados')
    derivation_ids = fields.One2many('dgc.appointment.derivation', 'turn_id', string='Derivaciones')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    # SQL Constraints
    _sql_constraints = [
        ('unique_dni_area_pending', 
         "EXCLUDE USING gist (citizen_dni WITH =, area_id WITH =, date WITH =) WHERE (state IN ('new','waiting','calling'))",
         'El ciudadano ya tiene un turno pendiente en esta área para hoy.')
    ]

    # Métodos de acción
    def action_call_turn(self): ...
    def action_recall_turn(self): ...
    def action_serve_turn(self): ...
    def action_done_turn(self): ...
    def action_no_show(self): ...
    def action_derive(self): ...       # Abre wizard de derivación

    @api.model
    def _find_or_create_partner(self, dni, name=None, email=None):
        """Busca res.partner por vat (CUIT/DNI). Si no existe, lo crea.
        Si existe y el email difiere, retorna flag para preguntar al ciudadano.
        
        Returns:
            dict: {
                'partner_id': int,
                'partner_name': str or None,
                'email_conflict': bool,
                'existing_email_masked': str or None,  # "ana***@hotmail.com"
            }
        """
        Partner = self.env['res.partner'].sudo()
        partner = Partner.search([('vat', '=', dni)], limit=1)
        
        if partner:
            result = {
                'partner_id': partner.id,
                'partner_name': partner.name,
                'email_conflict': False,
                'existing_email_masked': None,
            }
            # Detectar conflicto de email
            if email and partner.email and email.lower() != partner.email.lower():
                result['email_conflict'] = True
                result['existing_email_masked'] = self._mask_email(partner.email)
            return result
        
        # Crear nuevo partner
        vals = {'vat': dni, 'name': name or dni}
        if email:
            vals['email'] = email
        new_partner = Partner.create(vals)
        return {
            'partner_id': new_partner.id,
            'partner_name': new_partner.name,
            'email_conflict': False,
            'existing_email_masked': None,
        }

    @staticmethod
    def _mask_email(email):
        """Enmascara email: 'anabuzyn66@hotmail.com' → 'ana***@hotmail.com'"""
        local, domain = email.split('@')
        masked = local[:3] + '***' if len(local) > 3 else local[0] + '***'
        return f"{masked}@{domain}"
```

> **Nota sobre constraint de duplicados**: Se recomienda usar una constraint Python `@api.constrains` como alternativa si la base de datos no soporta `EXCLUDE USING gist`, verificando manualmente la unicidad de DNI + área + fecha para turnos en estados pendientes.

#### `dgc.appointment.call.log` — Log de Llamados

```python
class DgcAppointmentCallLog(models.Model):
    _name = 'dgc.appointment.call.log'
    _description = 'Log de Llamados de Turno'
    _order = 'call_datetime desc'

    turn_id = fields.Many2one('dgc.appointment.turn', required=True, ondelete='cascade', index=True)
    call_datetime = fields.Datetime(string='Fecha/Hora Llamado', default=fields.Datetime.now, required=True)
    operator_id = fields.Many2one('res.users', string='Operario', default=lambda self: self.env.user)
    call_number = fields.Integer(string='Llamado N°')
```

#### `dgc.appointment.derivation` — Registro de Derivaciones

```python
class DgcAppointmentDerivation(models.Model):
    _name = 'dgc.appointment.derivation'
    _description = 'Derivación de Turno entre Áreas'
    _order = 'derivation_date desc'

    turn_id = fields.Many2one('dgc.appointment.turn', required=True, ondelete='cascade', index=True)
    from_area_id = fields.Many2one('dgc.appointment.area', string='Área Origen', required=True)
    to_area_id = fields.Many2one('dgc.appointment.area', string='Área Destino', required=True)
    reason = fields.Text(string='Motivo de Derivación', required=True)
    user_id = fields.Many2one('res.users', string='Derivado por', default=lambda self: self.env.user)
    derivation_date = fields.Datetime(string='Fecha Derivación', default=fields.Datetime.now)
```

#### `dgc.appointment.config` — Configuración Global

```python
class DgcAppointmentConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    dgc_kiosk_timeout = fields.Integer(string='Timeout Kiosco (seg)', default=30,
        config_parameter='dgc_appointment_kiosk.kiosk_timeout')
    dgc_kiosk_email_required = fields.Boolean(string='Email Obligatorio',
        config_parameter='dgc_appointment_kiosk.kiosk_email_required')
    dgc_kiosk_notes_required = fields.Boolean(string='Observaciones Obligatorias',
        config_parameter='dgc_appointment_kiosk.kiosk_notes_required')
    dgc_kiosk_welcome_text = fields.Html(string='Mensaje de Bienvenida',
        config_parameter='dgc_appointment_kiosk.kiosk_welcome_text')
    dgc_display_blink_speed = fields.Selection([
        ('slow', 'Lento (2s)'),
        ('normal', 'Normal (1s)'),
        ('fast', 'Rápido (0.5s)'),
    ], default='normal', config_parameter='dgc_appointment_kiosk.display_blink_speed')
    dgc_display_scroll_messages = fields.Text(string='Mensajes Rotativos',
        config_parameter='dgc_appointment_kiosk.display_scroll_messages')
    dgc_max_calls_before_noshow = fields.Integer(string='Máx. Llamados antes de No Show', default=3,
        config_parameter='dgc_appointment_kiosk.max_calls_before_noshow')
    dgc_office_hour_start = fields.Float(string='Hora Inicio Atención', default=7.5,
        config_parameter='dgc_appointment_kiosk.office_hour_start')
    dgc_office_hour_end = fields.Float(string='Hora Fin Atención', default=11.5,
        config_parameter='dgc_appointment_kiosk.office_hour_end')
    dgc_avg_turn_duration = fields.Integer(string='Duración Promedio Turno (min)', default=15,
        config_parameter='dgc_appointment_kiosk.avg_turn_duration')
    dgc_turn_prefix = fields.Char(string='Prefijo Numeración',
        config_parameter='dgc_appointment_kiosk.turn_prefix')

    # --- Control de capacidad y turnos múltiples ---
    dgc_allow_multiple_turns = fields.Boolean(
        string='Permitir Turnos Múltiples por Ciudadano',
        default=False,
        config_parameter='dgc_appointment_kiosk.allow_multiple_turns',
        help='Si está activo, un mismo ciudadano puede sacar turnos en distintas áreas '
             'o en distintos horarios del mismo día. Si está inactivo, solo 1 turno pendiente global/día.')

    # --- Branding parametrizable ---
    dgc_branding_logo = fields.Binary(string='Logo de la Organización',
        config_parameter='dgc_appointment_kiosk.branding_logo')
    dgc_branding_name = fields.Char(string='Nombre de la Organización',
        default='Dirección General de Catastro',
        config_parameter='dgc_appointment_kiosk.branding_name')
    dgc_branding_primary_color = fields.Char(string='Color Primario (hex)',
        default='#003B7A',
        config_parameter='dgc_appointment_kiosk.branding_primary_color',
        help='Color principal para kiosco y display. Ej: #003B7A (azul DGC)')
    dgc_branding_bg_color = fields.Char(string='Color de Fondo (hex)',
        default='#1A237E',
        config_parameter='dgc_appointment_kiosk.branding_bg_color',
        help='Color de fondo de pantallas públicas. Ej: #1A237E (azul oscuro)')
```

#### `res.users` — Extensión con Áreas

```python
class ResUsers(models.Model):
    _inherit = 'res.users'

    dgc_area_ids = fields.Many2many(
        'dgc.appointment.area',
        'dgc_area_user_rel',
        'user_id', 'area_id',
        string='Áreas de Atención Asignadas'
    )
```

---

## 10. Wireframes / Mockups

### 10.1 Kiosco — Paso 1: Bienvenida

```
┌────────────────────────────────────────────┐
│                                            │
│              ╔═══════════╗                 │
│              ║  DGC Logo ║                 │
│              ╚═══════════╝                 │
│       Dirección General de Catastro        │
│                                            │
│            ═══════════════════              │
│                                            │
│              B I E N V E N I D O           │
│                                            │
│     Ingrese su DNI para continuar          │
│                                            │
│    ┌──────────────────────────────┐        │
│    │  Ejemplo: 44999666           │        │
│    └──────────────────────────────┘        │
│                                            │
│                      ┌──────────────┐      │
│                      │ Siguiente >  │      │
│                      └──────────────┘      │
│                                            │
│    ┌──────┐ ┌──────┐ ┌──────┐              │
│    │  1   │ │  2   │ │  3   │              │
│    ├──────┤ ├──────┤ ├──────┤              │
│    │  4   │ │  5   │ │  6   │              │
│    ├──────┤ ├──────┤ ├──────┤              │
│    │  7   │ │  8   │ │  9   │              │
│    ├──────┤ ├──────┤ ├──────┤              │
│    │      │ │  0   │ │Limpiar│             │
│    └──────┘ └──────┘ └──────┘              │
│                                            │
│    ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─         │
│    DGC | Dirección General de Catastro     │
└────────────────────────────────────────────┘
```

**UX Notes**: Botones del teclado mínimo 60x60px con spacing 8px. Fuente del input ≥ 24px. Color de fondo azul institucional (#003B7A). Texto blanco. Botones del teclado en tono claro con texto oscuro para contraste.

### 10.2 Kiosco — Paso 2: Selección de Área

```
┌────────────────────────────────────────────┐
│              ╔═══════════╗                 │
│              ║  DGC Logo ║                 │
│              ╚═══════════╝                 │
│                                            │
│      DNI: 11561033                         │
│                                            │
│     Seleccione el área de atención:        │
│                                            │
│    ┌──────────────────────────────────┐    │
│    │ 📐  Geodesia y Cartografía       │    │
│    │     2do Piso    [11 cupos disp.] │    │
│    └──────────────────────────────────┘    │
│                                            │
│    ┌──────────────────────────────────┐    │
│    │ 🏠  Catastro Urbano              │    │
│    │     Planta Baja [14 cupos disp.] │    │
│    └──────────────────────────────────┘    │
│                                            │
│    ┌──────────────────────────────────┐    │
│    │ 🌾  Catastro Rural               │    │
│    │     1er Piso    [CUPOS AGOTADOS] │    │
│    └──────────────────────────────────┘    │
│                                            │
│    ┌────────┐                              │
│    │< Volver│                              │
│    └────────┘                              │
│                                            │
└────────────────────────────────────────────┘
```

**UX Notes**: Cada área es un botón de tamaño completo (mínimo 80px alto). Áreas desactivadas no se muestran. Feedback visual al tocar (cambio de color). Scroll si hay más de 5 áreas.

### 10.3 Kiosco — Paso 3: Confirmación

```
┌────────────────────────────────────────────┐
│              ╔═══════════╗                 │
│              ║  DGC Logo ║                 │
│              ╚═══════════╝                 │
│                                            │
│          AGUARDE A SER ATENDIDO            │
│                                            │
│    ┌──────────────────────────────────┐    │
│    │                                  │    │
│    │  DNI          ÁREA               │    │
│    │ ┌────────┐  ┌─────────────────┐  │    │
│    │ │11561033│  │ Geodesia y      │  │    │
│    │ │ (verde)│  │ Cartografía     │  │    │
│    │ └────────┘  │ 2do Piso        │  │    │
│    │             └─────────────────┘  │    │
│    │                                  │    │
│    └──────────────────────────────────┘    │
│                                            │
│         TURNOS EN ESPERA: 5                │
│    Tiempo estimado: ~45 minutos            │
│                                            │
│      Pantalla se reinicia en 20s...        │
│                                            │
│    ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─         │
│    DGC | Dirección General de Catastro     │
└────────────────────────────────────────────┘
```

**UX Notes**: El fondo del turno generado es verde brillante (#00E676) para confirmar éxito visual. Countdown visible para el reinicio. El ciudadano tiene suficiente tiempo para leer y recordar el dato.

### 10.4 Pantalla Pública de Visualización

```
┌─────────────────────────────────────────────────────────────────┐
│  DGC Logo                              Geodesia y Cartografía   │
│═════════════════════════════════════════════════════════════════ │
│                                                                  │
│  ╔══════════════════════════════════════════════════════════╗    │
│  ║             TURNO ACTUAL  (fondo verde, parpadea)       ║    │
│  ║                                                          ║    │
│  ║    DNI: 11561033          Geodesia y Cartografía         ║    │
│  ║                           2do Piso                       ║    │
│  ║         (fuente 72px, negrita, alto contraste)           ║    │
│  ╚══════════════════════════════════════════════════════════╝    │
│                                                                  │
│  ─────── TURNOS EN ESPERA ────────                               │
│                                                                  │
│  │ #    │ DNI        │ Área                    │ Hora    │       │
│  │──────│────────────│─────────────────────────│─────────│       │
│  │  002 │ 3456****   │ Geodesia y Cartografía  │  08:15  │       │
│  │  003 │ 2789****   │ Geodesia y Cartografía  │  08:22  │       │
│  │  004 │ 1234****   │ Geodesia y Cartografía  │  08:30  │       │
│  │  005 │ 9876****   │ Geodesia y Cartografía  │  08:35  │       │
│  │  006 │ 5432****   │ Geodesia y Cartografía  │  08:41  │       │
│  │  ... │            │                         │         │       │
│                                                                  │
│ ═══════════════════════════════════════════════════════════════  │
│  >>> Recuerde traer DNI original y fotocopia. Horario: 7:30-11:30│
└─────────────────────────────────────────────────────────────────┘
```

**UX Notes**: Turno llamado ocupa ~30% superior de la pantalla. Fuente turno llamado: 72px bold. Fuente cola: 32px. Fondo del turno llamado: verde (#00C853) con animación CSS `@keyframes blink`. DNI parcialmente oculto en cola (últimos 4 dígitos con asteriscos). Franja inferior con marquee/scroll de mensajes informativos. Alto contraste: fondo oscuro (#1A237E), texto blanco.

### 10.5 Vista del Operario (Backoffice)

```
┌──────────────────────────────────────────────────────────────────┐
│  ® Turnero          Geodesia y Cartografía            👤 OPERARIO│
│                                                                   │
│  ┌─────────────────────────────────────────────────┐             │
│  │ Turno Actual: 11561033                          │             │
│  │ Tiempo transcurrido: 00:02 ⏱                   │             │
│  │                                                  │  [Nuevo    │
│  │ Nombre Completo: Gildi ricardo                   │   turno 📋]│
│  │ Email: anabuzyn66@hotmail.com.ar                 │             │
│  │                                                  │  [Derivar  │
│  │ Observación:                                     │      ➕]    │
│  │ ┌──────────────────────────────────────────┐    │             │
│  │ │                                          │    │  [Finalizar │
│  │ └──────────────────────────────────────────┘    │      ✔️]    │
│  └─────────────────────────────────────────────────┘             │
│                                                                   │
│  ┌─────────────────────────────────────────────────┐             │
│  │ Por Atender                         Total: 3    │             │
│  │ Nombre          │ Hora  │ Observación │ Estado  │             │
│  │─────────────────│───────│─────────────│─────────│             │
│  │ López Juan      │ 08:15 │             │ ESPERA  │ [Llamar]   │
│  │ Pérez María     │ 08:22 │             │ ESPERA  │ [Llamar]   │
│  │ García Carlos   │ 08:30 │ Derivado GC │ DERIVADO│ [Llamar]   │
│  └─────────────────────────────────────────────────┘             │
│                                                                   │
│  ┌─────────────────────────────────────────────────┐             │
│  │ Atendidos Hoy                                    │             │
│  │ Fecha-Hora        │ Nombre           │ Duración │ Estado     │             
│  │ 2026-03-17 11:16  │ Vadillo alejandro│ 03:21    │ FINALIZADO│             
│  │ 2026-03-17 11:13  │ Lezcano victor   │ 00:05    │ FINALIZADO│             
│  │ 2026-03-17 11:13  │ Hennig cristian  │ 01:00    │ FINALIZADO│             
│  └─────────────────────────────────────────────────┘             │
└──────────────────────────────────────────────────────────────────┘
```

**UX Notes**: Basado en la interfaz existente del sistema PHP (ver capturas). El turno activo se destaca en la parte superior. Los botones de acción son grandes y coloridos: "Nuevo turno" (outline), "Derivar" (azul), "Finalizar" (verde). Estados con badges coloreados: ESPERA (amarillo), LLAMANDO (azul), FINALIZADO (rojo/verde). Timer de tiempo transcurrido se actualiza en tiempo real vía JS.

### 10.6 Configuración en Backoffice (Ajustes)

```
┌──────────────────────────────────────────────────────────────────┐
│  Ajustes > DGC Turnero                                           │
│                                                                   │
│  ═══ Horarios de Atención ═══                                    │
│                                                                   │
│  Hora de inicio    Hora de fin     Tiempo de atención (min)      │
│  ┌──────────┐     ┌──────────┐    ┌──────────┐                  │
│  │  07:30   │     │  11:30   │    │    15    │    [✏️ Editar]    │
│  └──────────┘     └──────────┘    └──────────┘                  │
│                                                                   │
│  ═══ Áreas de Gestión ═══                                        │
│                                                                   │
│  Descripción        Ubicación       Abreviatura                   │
│  ┌──────────────┐  ┌────────────┐  ┌──────────┐  [+ Agregar]    │
│  │              │  │            │  │          │                   │
│  └──────────────┘  └────────────┘  └──────────┘                  │
│                                                                   │
│  - Geodesia y Cartografía - 2do Piso - GEO      [🗑 Eliminar]   │
│  - Catastro Urbano - Planta Baja - CU           [🗑 Eliminar]   │
│                                                                   │
│  ═══ Configuración de Kiosco ═══                                 │
│                                                                   │
│  Timeout reinicio (seg)    Email obligatorio    Obs. obligatorias │
│  ┌──────────┐              ☐                    ☐                │
│  │    30    │                                                     │
│  └──────────┘                                                     │
│                                                                   │
│  ☐ Permitir turnos múltiples por ciudadano en el mismo día       │
│    (Si se activa, un mismo DNI puede sacar turnos en distintas   │
│     áreas o en distintos horarios)                                │
│                                                                   │
│  ═══ Branding / Identidad Visual ═══                             │
│                                                                   │
│  Logo:  [📁 Subir imagen]     Nombre organización:               │
│                                ┌──────────────────────────────┐  │
│                                │ Dirección General de Catastro│  │
│                                └──────────────────────────────┘  │
│  Color primario:  ┌──────────┐  Color de fondo:  ┌──────────┐   │
│                   │ #003B7A  │                    │ #1A237E  │   │
│                   └──────────┘                    └──────────┘   │
│                                                                   │
│  ═══ Configuración de Pantalla ═══                               │
│                                                                   │
│  Sonido de llamada: [📁 Subir archivo]                           │
│  Velocidad parpadeo: ○ Lento  ● Normal  ○ Rápido                │
│  Mensajes rotativos:                                              │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ Recuerde traer DNI original y fotocopia...               │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                   │
│                                            [💾 Guardar]          │
└──────────────────────────────────────────────────────────────────┘
```

---

## 11. User Flows

### 11.1 Flujo Completo: Generación → Atención → Finalización

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│  Ciudadano   │     │   Kiosco     │     │   Odoo.sh     │
│  llega       │────►│  Bienvenida  │────►│               │
└─────────────┘     └──────┬───────┘     │               │
                           │              │               │
                    Ingresa DNI           │               │
                           │              │               │
                    Selecciona área       │               │
                           │              │               │
                    Confirma ─────────────►  Validar DNI  │
                           │              │  Check capac. │
                           │              │  Check duplic.│
                           │              │  Find/create  │
                           │              │  res.partner  │
                           │              │  Crear turno  │
                           │              │  Asignar N°   │
                    ◄──────────────────────  Respuesta    │
                    Muestra turno N°      │               │
                    Reinicio auto         │               │
                           │              │               │
                           ▼              │               │
                    ┌──────────────┐      │               │
                    │  Ciudadano   │      │               │
                    │  espera en   │      │               │
                    │  sala        │      │               │
                    └──────────────┘      │               │
                                          │               │
┌─────────────┐                           │               │
│  Operario   │──── Ve turno en lista ◄───│  Turno state: │
│  en su PC   │                           │  'waiting'    │
│             │──── Clic "Llamar" ────────►  state →      │
│             │                           │  'calling'    │
│             │                           │  Bus notify   │
│             │                           │       │       │
│             │                           │       ▼       │
│             │                    ┌──────────────────┐   │
│             │                    │  Pantalla Display │   │
│             │                    │  Muestra turno    │   │
│             │                    │  🔊 Sonido        │   │
│             │                    │  💚 Parpadeo      │   │
│             │                    └──────────────────┘   │
│             │                                           │
│  Ciudadano se presenta                                  │
│             │──── Clic "Atendiendo" ───►  state →       │
│             │                           │  'serving'    │
│             │                           │  serve_date   │
│  Atiende...│                           │               │
│             │                           │               │
│             │──── Clic "Finalizar" ────►  state →       │
│             │                           │  'done'       │
│             │                           │  done_date    │
│             │                           │  duration =   │
│             │                           │  done - serve │
└─────────────┘                           └───────────────┘
```

### 11.2 Flujo de Derivación entre Áreas

```
┌──────────────────┐      ┌───────────────┐      ┌──────────────────┐
│  Operario Área A │      │   Odoo.sh     │      │  Operario Área B │
│  (Geodesia)      │      │               │      │  (Catastro)      │
└────────┬─────────┘      └───────┬───────┘      └────────┬─────────┘
         │                        │                        │
  Tiene turno T001                │                        │
  en estado 'serving'             │                        │
         │                        │                        │
  Clic "Derivar"                  │                        │
         │                        │                        │
  ┌──────────────────┐            │                        │
  │ Wizard Derivación│            │                        │
  │ Área destino: [B]│            │                        │
  │ Motivo: [______] │            │                        │
  │ [Confirmar]      │            │                        │
  └──────┬───────────┘            │                        │
         │                        │                        │
  Confirma ───────────────────►   │                        │
         │                  Crear derivation record         │
         │                  T001.area_id = B               │
         │                  T001.state = 'derived'         │
         │                  → luego 'waiting' en area B    │
         │                  Bus notify area B              │
         │                        │                        │
         │                        │─────────────────────►  │
         │                        │                  Turno T001 aparece
         │                        │                  en lista de Área B
         │                        │                  con badge "DERIVADO"
         │                        │                        │
         │                        │                  Operario B puede
         │                        │                  ver historial:
         │                        │                  "Derivado desde
         │                        │                   Geodesia por [user]
         │                        │                   Motivo: [texto]"
```

### 11.3 Flujo de Llamados Múltiples y No Se Presentó

```
Estado inicial: Turno T001 en 'waiting'

Operario                    Sistema                     Display
   │                           │                           │
   │── Llamar (1er vez) ──────►│                           │
   │                     state → 'calling'                 │
   │                     call_log #1                       │
   │                           │── Bus notify ────────────►│
   │                           │                     Turno verde
   │                           │                     Parpadeo normal
   │                           │                     🔊 Sonido
   │                           │                           │
   │   (espera ~30 seg)        │                           │
   │                           │                           │
   │── Volver a llamar ───────►│                           │
   │                     call_log #2                       │
   │                           │── Bus notify ────────────►│
   │                           │                     Turno naranja
   │                           │                     Parpadeo rápido
   │                           │                     🔊 Sonido x2
   │                           │                           │
   │   (espera ~30 seg)        │                           │
   │                           │                           │
   │── Volver a llamar ───────►│                           │
   │                     call_log #3                       │
   │                           │── Bus notify ────────────►│
   │                           │                     Turno ROJO
   │                           │                     Parpadeo urgente
   │                           │                     🔊 Sonido x3
   │                           │                           │
   │   (ciudadano no viene)    │                           │
   │                           │                           │
   │── "No se presentó" ─────►│                           │
   │                     state → 'no_show'                 │
   │                     Registra 3 llamados               │
   │                           │── Bus notify ────────────►│
   │                           │                     Turno desaparece
   │                           │                           │
   │── Puede llamar siguiente  │                           │
```

---

## 12. Seguridad y Permisos

### 12.1 Grupos de Usuarios

```xml
<!-- security/security.xml -->
<record id="module_category_dgc_turnero" model="ir.module.category">
    <field name="name">DGC Turnero</field>
    <field name="sequence">200</field>
</record>

<record id="group_dgc_kiosk_public" model="res.groups">
    <field name="name">Usuario Público Kiosco</field>
    <field name="category_id" ref="module_category_dgc_turnero"/>
    <field name="comment">Acceso anónimo a endpoints públicos de kiosco y display</field>
</record>

<record id="group_dgc_operator" model="res.groups">
    <field name="name">Operario de Turnos</field>
    <field name="category_id" ref="module_category_dgc_turnero"/>
    <field name="comment">Lee/escribe turnos de su área, puede llamar/finalizar/derivar</field>
</record>

<record id="group_dgc_area_manager" model="res.groups">
    <field name="name">Responsable de Área</field>
    <field name="category_id" ref="module_category_dgc_turnero"/>
    <field name="implied_ids" eval="[(4, ref('group_dgc_operator'))]"/>
    <field name="comment">Permisos de operario + config de su área + reportes</field>
</record>

<record id="group_dgc_admin" model="res.groups">
    <field name="name">Administrador de Turnos</field>
    <field name="category_id" ref="module_category_dgc_turnero"/>
    <field name="implied_ids" eval="[(4, ref('group_dgc_area_manager'))]"/>
    <field name="comment">Acceso total, ve todos los turnos, configura sistema</field>
</record>
```

### 12.2 Matriz de Permisos CRUD

| Modelo | Público Kiosco | Operario | Resp. Área | Admin |
|--------|:-:|:-:|:-:|:-:|
| `dgc.appointment.area` | R | R | R/W | R/W/C/D |
| `dgc.appointment.turn` | C (vía endpoint) | R/W | R/W | R/W/C/D |
| `dgc.appointment.call.log` | — | R/C | R/C | R/W/C/D |
| `dgc.appointment.derivation` | — | R/C | R/C | R/W/C/D |
| `dgc.appointment.config` | — | — | R | R/W |

**Leyenda**: R=Read, W=Write, C=Create, D=Delete

### 12.3 Record Rules

```xml
<!-- Operarios y responsables solo ven turnos de sus áreas -->
<record id="rule_turn_by_area" model="ir.rule">
    <field name="name">Turnos: solo áreas asignadas</field>
    <field name="model_id" ref="model_dgc_appointment_turn"/>
    <field name="groups" eval="[(4, ref('group_dgc_operator'))]"/>
    <field name="domain_force">[('area_id', 'in', user.dgc_area_ids.ids)]</field>
</record>

<!-- Administradores ven todos los turnos -->
<record id="rule_turn_admin_all" model="ir.rule">
    <field name="name">Turnos: admin ve todo</field>
    <field name="model_id" ref="model_dgc_appointment_turn"/>
    <field name="groups" eval="[(4, ref('group_dgc_admin'))]"/>
    <field name="domain_force">[(1, '=', 1)]</field>
</record>

<!-- Call logs siguen la misma lógica que turnos -->
<record id="rule_call_log_by_area" model="ir.rule">
    <field name="name">Call Logs: solo áreas asignadas</field>
    <field name="model_id" ref="model_dgc_appointment_call_log"/>
    <field name="groups" eval="[(4, ref('group_dgc_operator'))]"/>
    <field name="domain_force">[('turn_id.area_id', 'in', user.dgc_area_ids.ids)]</field>
</record>

<!-- Derivaciones: operarios ven las de sus áreas (origen o destino) -->
<record id="rule_derivation_by_area" model="ir.rule">
    <field name="name">Derivaciones: áreas asignadas</field>
    <field name="model_id" ref="model_dgc_appointment_derivation"/>
    <field name="groups" eval="[(4, ref('group_dgc_operator'))]"/>
    <field name="domain_force">['|',
        ('from_area_id', 'in', user.dgc_area_ids.ids),
        ('to_area_id', 'in', user.dgc_area_ids.ids)
    ]</field>
</record>
```

### 12.4 Endpoints Públicos y Privados

| Endpoint | Tipo | Auth | Rate Limit | Descripción |
|----------|------|------|------------|-------------|
| `/kiosk/checkin` | HTTP | `public` | — | Página del kiosco (QWeb template) |
| `/kiosk/api/turn/create` | JSON | `public` | 1/30s por IP | Crear turno |
| `/kiosk/api/areas` | JSON | `public` | 10/min por IP | Listar áreas activas |
| `/display/queue` | HTTP | `public` | — | Página de pantalla (QWeb template) |
| `/display/api/turns` | JSON | `public` | 20/min por IP | Turnos actuales para display |
| `/api/turn/call` | JSON | `user` | — | Llamar turno (requiere sesión) |
| `/api/turn/serve` | JSON | `user` | — | Marcar atendiendo |
| `/api/turn/done` | JSON | `user` | — | Finalizar turno |
| `/api/turn/noshow` | JSON | `user` | — | Marcar no se presentó |
| `/api/turn/derive` | JSON | `user` | — | Derivar turno |

---

## 13. Especificación de API

### 13.1 Crear Turno (Kiosco)

**`POST /kiosk/api/turn/create`** — `type='json'`, `auth='public'`

**Request**:
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "dni": "11561033",
        "area_id": 1,
        "email": "ciudadano@email.com",
        "notes": "Consulta sobre plano",
        "update_email": false
    }
}
```

> Nota: `update_email` solo se envía como `true` en un segundo intento, cuando el ciudadano confirmó que desea actualizar el email registrado en `res.partner`.

**Response (éxito)**:
```json
{
    "jsonrpc": "2.0",
    "result": {
        "success": true,
        "turn_id": 142,
        "turn_number": "GEO-001",
        "area_name": "Geodesia y Cartografía",
        "area_location": "2do Piso",
        "queue_position": 5,
        "estimated_wait_minutes": 45,
        "remaining_capacity": 11,
        "citizen_name": "Gildi Ricardo",
        "partner_id": 58
    }
}
```

**Response (conflicto de email — requiere confirmación del ciudadano)**:
```json
{
    "jsonrpc": "2.0",
    "result": {
        "success": false,
        "error_code": "EMAIL_CONFLICT",
        "error_message": "Este CUIT ya tiene un email registrado.",
        "existing_email_masked": "ana***@hotmail.com",
        "prompt": "¿Desea reemplazar el email registrado por el nuevo?"
    }
}
```

> El kiosco muestra un diálogo con el email enmascarado y dos botones: "Sí, actualizar" (reenvía con `update_email: true`) y "No, mantener" (reenvía sin campo `email`).

**Response (error genérico)**:
```json
{
    "jsonrpc": "2.0",
    "result": {
        "success": false,
        "error_code": "DUPLICATE_TURN",
        "error_message": "Ya tiene un turno pendiente en esta área para hoy."
    }
}
```

**Errores posibles**:

| Código | Descripción |
|--------|-------------|
| `INVALID_DNI` | DNI/CUIT con formato inválido |
| `AREA_INACTIVE` | El área seleccionada no está activa |
| `AREA_NOT_FOUND` | ID de área no existe |
| `DUPLICATE_TURN` | Ya existe turno pendiente para ese DNI en esa área hoy (o global si `allow_multiple_turns=False`) |
| `CAPACITY_FULL` | El área alcanzó el tope diario de turnos (ej: 16/16 cupos utilizados) |
| `EMAIL_CONFLICT` | El CUIT ya tiene un email distinto registrado — requiere confirmación del ciudadano |
| `RATE_LIMITED` | Demasiados intentos desde esta IP |
| `OUTSIDE_HOURS` | Fuera del horario de atención |

### 13.2 Listar Áreas Activas (Kiosco)

**`POST /kiosk/api/areas`** — `type='json'`, `auth='public'`

**Response**:
```json
{
    "jsonrpc": "2.0",
    "result": {
        "areas": [
            {
                "id": 1,
                "name": "Geodesia y Cartografía",
                "code": "GEO",
                "location": "2do Piso",
                "pending_count": 5,
                "estimated_wait": 45,
                "max_daily_turns": 16,
                "remaining_capacity": 11,
                "is_full": false
            },
            {
                "id": 2,
                "name": "Catastro Urbano",
                "code": "CU",
                "location": "Planta Baja",
                "pending_count": 2,
                "estimated_wait": 20,
                "max_daily_turns": 16,
                "remaining_capacity": 14,
                "is_full": false
            }
        ]
    }
}
```

### 13.3 Obtener Turnos para Display

**`POST /display/api/turns`** — `type='json'`, `auth='public'`

**Request**:
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "area_id": 1
    }
}
```

**Response**:
```json
{
    "jsonrpc": "2.0",
    "result": {
        "calling": {
            "turn_id": 142,
            "turn_number": "GEO-001",
            "citizen_dni_masked": "1156****",
            "citizen_name": "Gildi Ricardo",
            "area_name": "Geodesia y Cartografía",
            "area_location": "2do Piso",
            "call_count": 2,
            "last_call_time": "2026-03-17T11:15:00"
        },
        "waiting": [
            {
                "turn_number": "GEO-002",
                "citizen_dni_masked": "3456****",
                "area_name": "Geodesia y Cartografía",
                "create_time": "2026-03-17T08:15:00"
            }
        ],
        "scroll_messages": [
            "Recuerde traer DNI original y fotocopia.",
            "Horario de atención: 7:30 a 11:30 hs."
        ]
    }
}
```

### 13.4 Llamar Turno (Operario)

**`POST /api/turn/call`** — `type='json'`, `auth='user'`

**Request**:
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "turn_id": 142
    }
}
```

**Response**:
```json
{
    "jsonrpc": "2.0",
    "result": {
        "success": true,
        "turn_number": "GEO-001",
        "call_count": 1,
        "state": "calling"
    }
}
```

### 13.5 Estructura de Payloads de Bus Notifications

**Canal por área**: `dgc_turn_area_{area_id}`  
**Canal global**: `dgc_turn_global`

**Payload para llamado**:
```json
{
    "type": "dgc_turn_call",
    "payload": {
        "turn_id": 142,
        "turn_number": "GEO-001",
        "citizen_name": "Gildi Ricardo",
        "citizen_dni_masked": "1156****",
        "area_id": 1,
        "area_name": "Geodesia y Cartografía",
        "area_location": "2do Piso",
        "action": "call",
        "call_count": 1,
        "operator_name": "Carlos Méndez"
    }
}
```

**Payload para actualización de estado**:
```json
{
    "type": "dgc_turn_update",
    "payload": {
        "turn_id": 142,
        "turn_number": "GEO-001",
        "action": "serve",
        "new_state": "serving"
    }
}
```

**Payload para nuevo turno generado**:
```json
{
    "type": "dgc_turn_new",
    "payload": {
        "turn_id": 143,
        "turn_number": "GEO-002",
        "area_id": 1,
        "queue_position": 6
    }
}
```

---

## 14. Dependencias e Integraciones

### 14.1 Módulos Odoo Nativos Requeridos

| Módulo | Propósito |
|--------|-----------|
| `base` | Modelos base (`res.users`, `res.partner`, `res.company`) |
| `mail` | Chatter, tracking de cambios, actividades |
| `bus` | Sistema de notificaciones en tiempo real (longpolling) |
| `web` | Framework web, assets, controladores HTTP |
| `appointment` | Base de funcionalidad de citas (herencia del modelo) |

### 14.2 Librerías Python Externas

No se requieren librerías Python externas adicionales. Todo se resuelve con el stack estándar de Odoo 19 (Python 3.12+, PostgreSQL, Werkzeug).

### 14.3 Librerías JavaScript / Frontend

| Librería | Propósito | Origen |
|----------|-----------|--------|
| OWL 2.x | Componentes frontend (nativo Odoo 19) | Incluida en Odoo |
| Web Audio API | Reproducción de sonidos en display | API nativa del navegador |
| SpeechSynthesis API | TTS opcional para anuncio de turnos | API nativa del navegador |
| localStorage | Cache de configuración en kiosco | API nativa del navegador |

### 14.4 Hardware Compatible

| Dispositivo | Especificación Mínima | Notas |
|-------------|----------------------|-------|
| Kiosco touchscreen | Pantalla 15"+, resolución 1080p, Chrome 90+, conexión internet estable | Windows, Linux o Android |
| Pantalla display | TV/monitor 40"+, resolución 1080p, navegador fullscreen | Puede usar Raspberry Pi, Android TV, mini-PC |
| Parlantes | USB o integrados, volumen audible en sala de espera | Conectados al dispositivo del display |
| Impresora térmica (opc.) | 80mm, interfaz ESC/POS, USB o red | Fase 2 |

### 14.5 Integraciones Futuras (Fase 2+)

| Integración | Descripción | Fase |
|-------------|-------------|------|
| WhatsApp Business API | Notificaciones de proximidad de turno | Fase 2 |
| SMS Gateway | Alternativa a WhatsApp para notificaciones | Fase 2 |
| API REST externa | Consulta de estado de turnos desde sistemas terceros | Fase 2 |
| Impresora térmica ESC/POS | Impresión de tickets con QR code | Fase 2 |
| App móvil ciudadano | Turno con cita previa, consulta de estado | Fase 3 |

---

## 15. Estrategia de Testing

### 15.1 Unit Tests

| Test | Modelo/Método | Descripción |
|------|---------------|-------------|
| `test_create_turn` | `dgc.appointment.turn.create()` | Crear turno válido, verificar secuencia, estado inicial `new` |
| `test_create_turn_invalid_dni` | `dgc.appointment.turn.create()` | DNI inválido lanza `ValidationError` |
| `test_create_turn_duplicate` | `dgc.appointment.turn.create()` | Mismo DNI + área + fecha → error de duplicado |
| `test_create_turn_inactive_area` | `dgc.appointment.turn.create()` | Área inactiva → error |
| `test_action_call_turn` | `action_call_turn()` | Estado cambia a `calling`, crea `call.log`, actualiza `call_date` |
| `test_action_serve_turn` | `action_serve_turn()` | Estado cambia a `serving`, registra `serve_date` |
| `test_action_done_turn` | `action_done_turn()` | Estado cambia a `done`, calcula `duration` |
| `test_action_no_show` | `action_no_show()` | Estado cambia a `no_show`, solo si `call_count >= 1` |
| `test_derive_turn` | Wizard derivación | Crea `derivation` record, cambia `area_id`, estado `derived` → `waiting` |
| `test_compute_duration` | `_compute_duration()` | Duración correcta entre `serve_date` y `done_date` |
| `test_compute_wait_time` | `_compute_wait_time()` | Espera correcta entre `create_date` y `serve_date` |
| `test_sequence_reset_daily` | Secuencia de turno | Números se reinician cada día |
| `test_cuit_validation` | `_check_dni_format()` | CUIT 11 dígitos con dígito verificador correcto |
| `test_capacity_limit` | `dgc.appointment.area` | Al alcanzar `max_daily_turns`, el kiosco rechaza nuevos turnos con error `CAPACITY_FULL` |
| `test_capacity_with_counters` | `dgc.appointment.area` | Área con `max_counters=3` tiene tope diario 3x (ej: 48 en vez de 16) |
| `test_capacity_noshow_frees_slot` | `dgc.appointment.area` | Turnos en `no_show` no consumen cupo — `remaining_turns` se recalcula |
| `test_find_or_create_partner_new` | `_find_or_create_partner()` | DNI nuevo crea `res.partner` con `vat` = DNI |
| `test_find_or_create_partner_exists` | `_find_or_create_partner()` | DNI existente retorna partner_id sin crear duplicado |
| `test_partner_email_conflict` | `_find_or_create_partner()` | Partner existe con email distinto → retorna `email_conflict=True` + email enmascarado |
| `test_partner_email_update` | Endpoint `/kiosk/api/turn/create` | Con `update_email=True`, se actualiza `res.partner.email` |
| `test_partner_no_duplicate_vat` | `res.partner` | Dos turnos con mismo CUIT apuntan al mismo `partner_id` |
| `test_multiple_turns_disabled` | Configuración + turno | Con `allow_multiple_turns=False`, mismo DNI no puede sacar 2do turno global |
| `test_multiple_turns_enabled` | Configuración + turno | Con `allow_multiple_turns=True`, mismo DNI puede sacar turno en otra área |

### 15.2 Integration Tests

| Test | Componentes | Descripción |
|------|-------------|-------------|
| `test_call_sends_bus_notification` | `action_call_turn()` → Bus | Llamar turno envía mensaje al canal correcto con payload esperado |
| `test_derive_notifies_target_area` | Wizard → Bus | Derivación envía notificación al canal del área destino |
| `test_kiosk_endpoint_creates_turn` | Controller `/kiosk/api/turn/create` → ORM | Endpoint crea turno correctamente |
| `test_kiosk_endpoint_rate_limit` | Controller → rate limiter | Más de 1 request/30s desde misma IP → error |
| `test_display_endpoint_returns_turns` | Controller `/display/api/turns` → ORM | Endpoint retorna turnos llamados y en espera |
| `test_full_workflow` | Crear → Llamar → Servir → Finalizar | Flujo completo de un turno con estados y timestamps correctos |

### 15.3 Security Tests

| Test | Descripción |
|------|-------------|
| `test_operator_sees_only_own_area` | Operario de Geodesia no ve turnos de Catastro |
| `test_admin_sees_all_turns` | Admin ve turnos de todas las áreas |
| `test_operator_cannot_delete_turn` | Operario no tiene permiso de eliminación |
| `test_public_cannot_access_backoffice` | Request sin auth a endpoints privados retorna 403 |
| `test_kiosk_endpoint_accessible_without_auth` | Endpoints `/kiosk/*` accesibles sin sesión |

### 15.4 UI Tests (Selenium/Playwright)

| Test | Interfaz | Pasos |
|------|----------|-------|
| `test_kiosk_full_flow` | Kiosco | Navegar a `/kiosk/checkin` → Ingresar DNI → Seleccionar área → Confirmar → Verificar pantalla de confirmación |
| `test_kiosk_invalid_dni` | Kiosco | Ingresar DNI inválido → Verificar mensaje de error |
| `test_kiosk_auto_reset` | Kiosco | Completar turno → Esperar timeout → Verificar regreso a bienvenida |
| `test_display_shows_called_turn` | Display | Llamar turno desde backoffice → Verificar que aparece en pantalla |
| `test_display_plays_sound` | Display | Llamar turno → Verificar reproducción de audio |

### 15.5 Load Testing

| Escenario | Herramienta | Criterio de Éxito |
|-----------|-------------|-------------------|
| 100 turnos generados en 1 minuto | Locust / k6 | Todos creados sin error, tiempo respuesta < 2s |
| 10 kioscos concurrentes generando turnos | Locust / k6 | Sin colisiones de secuencia, sin errores 500 |
| 50 operarios consultando turnos simultáneamente | Locust / k6 | Tiempo respuesta < 3s |
| 20 pantallas display con longpolling activo | Locust / k6 | Notificaciones recibidas en < 3s |

---

## 16. Plan de Despliegue

### 16.1 Instalación del Módulo en Odoo.sh

1. **Preparar repositorio**: Crear branch `feature/dgc-turnero` en el repositorio Git vinculado a Odoo.sh.
2. **Subir código**: Push del módulo `dgc_appointment_kiosk` al repositorio.
3. **Instalar en staging**: Odoo.sh detecta el módulo automáticamente. Instalar desde Apps.
4. **Ejecutar tests**: `odoo-bin --test-enable --stop-after-init -i dgc_appointment_kiosk`.
5. **Merge a producción**: Merge del branch a `main`/`production` tras validación.

### 16.2 Configuración Inicial Post-Instalación

1. **Crear áreas de atención**: Geodesia y Cartografía (GEO, 2do Piso), y las que apliquen.
2. **Crear/asignar usuarios**: Asignar grupo "Operario" o "Responsable" a cada usuario, asignar áreas.
3. **Configurar horarios**: Hora inicio 07:30, hora fin 11:30, tiempo promedio 15 min.
4. **Configurar kiosco**: Timeout 30s, mensaje de bienvenida, campos opcionales.
5. **Configurar display**: Sonido de llamada, velocidad de parpadeo, mensajes rotativos.
6. **Probar URLs públicas**: Verificar acceso a `/kiosk/checkin` y `/display/queue` sin sesión.

### 16.3 Configuración de Dispositivos Locales

1. **Kioscos**: Abrir Chrome en modo kiosco (`--kiosk`) apuntando a `https://[instancia].odoo.com/kiosk/checkin`. Deshabilitar barra de direcciones y teclas de escape.
2. **Pantallas display**: Abrir navegador en fullscreen apuntando a `https://[instancia].odoo.com/display/queue` o con `?area_id=X` para filtrar.
3. **Parlantes**: Verificar que el navegador tiene permisos de audio (requiere interacción inicial del usuario en algunos navegadores).

### 16.4 Plan de Rollout

| Fase | Duración | Alcance |
|------|----------|---------|
| Piloto | 2 semanas | Un área (Geodesia y Cartografía), 1 kiosco, 1 display, 2-3 operarios |
| Expansión 1 | 2 semanas | Todas las áreas activas, todos los kioscos y displays |
| Estabilización | 4 semanas | Monitoreo, ajustes de configuración, resolución de incidencias |
| Operación plena | Continua | Sistema en producción con soporte de primer nivel |

### 16.5 Capacitación

| Audiencia | Contenido | Duración | Formato |
|-----------|-----------|----------|---------|
| Operarios | Uso del panel de turnos: llamar, servir, finalizar, derivar, no-show | 2 horas | Presencial + guía rápida impresa |
| Responsables de área | Todo lo anterior + reportes, dashboard, configuración de su área | 3 horas | Presencial |
| Administradores TI | Configuración global, gestión de usuarios, troubleshooting, logs | 4 horas | Presencial + documentación técnica |
| Ciudadanos | Cartelería instructiva junto al kiosco + asistente los primeros días | Continuo | Señalética + personal de apoyo |

---

## 17. Roadmap y Fases

### Fase 1 — MVP (Estimación: 6-8 semanas de desarrollo)

| Componente | Incluye |
|------------|---------|
| **Kiosco** | Input DNI, selección de área, generación de turno, confirmación, reinicio automático |
| **Panel Operario** | Lista de turnos por área, botones Llamar/Atendiendo/Finalizar/No se presentó/Derivar |
| **Pantalla Display** | Turno llamado destacado, cola de espera, sonido de llamada, actualización en tiempo real |
| **Backoffice** | CRUD de áreas, asignación de usuarios, configuración de horarios |
| **Seguridad** | Grupos, permisos CRUD, record rules por área |
| **Historial** | Vista list con filtros básicos, exportación a Excel |

### Fase 2 — Reportes y Notificaciones (Estimación: 4-6 semanas)

| Componente | Incluye |
|------------|---------|
| **Dashboard KPIs** | Turnos hoy, en espera, finalizados, tiempo promedio, gráficos |
| **Reportes avanzados** | Atendidos por período, tiempos promedio por área, tasa de no-shows, derivaciones |
| **Impresión de tickets** | Integración impresora térmica ESC/POS con QR code |
| **Notificaciones** | WhatsApp/SMS para aviso de proximidad de turno |
| **API REST externa** | Endpoints para consulta de estado desde sistemas terceros |
| **TTS** | Anuncio de voz sintetizado en pantalla de display |

### Fase 3 — App Móvil y Citas Previas (Estimación: 8-12 semanas)

| Componente | Incluye |
|------------|---------|
| **App móvil ciudadano** | Solicitar turno remoto, ver estado, recibir notificaciones push |
| **Turnos con cita previa** | Agenda por día/hora, integración con calendario de Odoo |
| **Multi-sucursal** | Campo `branch_id`, configuración independiente por sede |
| **Integración sistemas externos** | Conexión con sistemas catastrales para pre-carga de datos del trámite |

### Timeline Visual

```
Mes 1        Mes 2        Mes 3        Mes 4        Mes 5        Mes 6+
├────────────┼────────────┼────────────┼────────────┼────────────┼──────
│            │            │            │            │            │
│◄── Fase 1: MVP ──────►│            │            │            │
│  Kiosco + Llamador +   │            │            │            │
│  Display + Backoffice  │            │            │            │
│            │            │◄── Fase 2: Reportes ──►│            │
│            │            │  Dashboard + Stats +    │            │
│            │            │  Tickets + WhatsApp     │            │
│            │            │            │            │◄── Fase 3 ─┤
│            │            │            │            │  App Móvil │
│            │            │            │            │  Citas     │
│       ┌────┤            │            │            │            │
│  Piloto    │  Rollout   │            │            │            │
│  (1 área)  │  (todas)   │            │            │            │
```

---

## 18. Preguntas Abiertas y Supuestos

### Preguntas Abiertas

| # | Pregunta | Impacto | Estado |
|---|----------|---------|--------|
| Q1 | ¿Cuántos kioscos y pantallas de visualización habrá por sucursal? | Dimensionamiento de longpolling y concurrencia | Pendiente |
| Q2 | ¿Cuál es el ancho de banda de internet disponible en la sucursal? | Determinará si se requiere optimización agresiva de payload o cache offline más robusto | Pendiente |
| Q3 | ¿Qué hacer con turnos pendientes al final del día? | Definir política: cancelar automáticamente (cron), mantener, o mover al siguiente día | **RESUELTO**: No deben quedar turnos pendientes porque el sistema calcula un tope diario por área basado en: `(hora_fin - hora_inicio) / tiempo_promedio_turno`. Ej: (11:30 - 7:30) = 4h = 240min / 15min = **16 turnos máx/día por área**. El kiosco bloquea la generación de nuevos turnos cuando se alcanza el tope del área. Los turnos que excepcionalmente queden pendientes al cierre se cancelan vía cron. |
| Q4 | ¿Hay necesidad de turnos con cita previa (agendados) además de walk-in? | Impacta modelo de datos y flujo del kiosco | Pendiente — supuesto: solo walk-in en MVP |
| Q5 | ¿Se requiere modo multi-sucursal desde el inicio? | Impacta modelo de datos (campo `branch_id`) | Pendiente — supuesto: una sola sucursal en MVP |
| Q6 | ¿Los operarios atienden un solo turno a la vez o pueden tener varios en paralelo? | Impacta UX del panel de operario | **RESUELTO**: Depende del área. Geodesia: 1 operario = 1 turno a la vez. Información Territorial (PB): puede haber varios boxes atendiendo en paralelo. El sistema debe ser **parametrizable por área** (`max_counters` en `dgc.appointment.area`), permitiendo N operarios simultáneos. Además, el branding (logo, color de fondo) debe ser configurable por instancia para reutilización en otras organizaciones. |
| Q7 | ¿El sistema debe funcionar fuera del horario configurado (ej. para turnos de emergencia)? | Impacta validación de horarios | Pendiente — supuesto: no genera turnos fuera de horario |
| Q8 | ¿Se requiere que el kiosco lea DNI desde tarjeta SUBE/DNI digital/código de barras? | Impacta hardware y lógica del kiosco | Pendiente — supuesto: solo ingreso manual |
| Q9 | ¿Existe un directorio de ciudadanos/contribuyentes en Odoo (`res.partner`) con DNI cargado? | Impacta búsqueda y autocompletado de nombre | **RESUELTO**: Aún no hay un directorio completo, pero pueden existir profesionales registrados como contactos y ciudadanos que hayan solicitado cita vía formulario web. El sistema debe buscar por CUIT/DNI en `res.partner` y: (a) si existe, vincular el turno al partner existente y autocompletar nombre; (b) si no existe, crear un `res.partner` nuevo; (c) **nunca duplicar** contactos por CUIT — si el CUIT ya existe pero el email ingresado difiere, avisar al ciudadano mostrando el email registrado (parcialmente oculto) y preguntar si desea actualizarlo. |

### Supuestos

1. **Conectividad estable**: la sucursal tiene internet de al menos 10 Mbps con uptime > 99%.
2. **Navegadores modernos**: todos los dispositivos usan Chrome 90+ o equivalente.
3. **Una sucursal**: el MVP opera en una sola sede de la DGC.
4. **Solo walk-in**: no hay citas previas en el MVP.
5. **Boxes paralelos por área**: cada área define cuántos operarios pueden atender simultáneamente (`max_counters`). Geodesia = 1, Información Territorial = N configurable.
6. **Tope diario de turnos por área**: el sistema calcula automáticamente el máximo de turnos diarios como `(hora_fin - hora_inicio) / avg_service_time` y bloquea nuevos turnos al alcanzar el tope. Cron cancela turnos residuales al cierre.
7. **Sin migración**: no se importan datos del sistema PHP anterior.
8. **Odoo.sh Enterprise**: se asume licencia Enterprise para acceso completo al módulo `appointment` y funcionalidades de bus/longpolling.
9. **Unicidad de contacto por CUIT**: el sistema no duplica `res.partner` — busca por CUIT/DNI antes de crear. Si el CUIT existe con email diferente, notifica y ofrece actualización.
10. **Turnos múltiples opcional**: booleano configurable por área para permitir o no que un mismo ciudadano saque turnos en distintos horarios/áreas el mismo día.
11. **Branding parametrizable**: logo, colores corporativos y nombre de la organización son configurables desde el backoffice para permitir reutilización del módulo en otras entidades.

---

## 19. Riesgos y Mitigaciones

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|:---:|:---:|-----------|
| R1 | **Caída de conexión a internet en la sucursal** | Media | Alto | Cache local en kiosco (áreas, config). Mensaje de error amigable. Procedimiento manual de backup (lista en papel). Retry automático con backoff exponencial. |
| R2 | **Sobrecarga de turnos en horas pico** | Media | Medio | Límite configurable de turnos por hora por área. Alertas automáticas al responsable cuando la cola supera umbral. Dashboard de monitoreo en tiempo real. |
| R3 | **Adopción baja por operarios** | Baja | Alto | Capacitación presencial con práctica. UI inspirada en el sistema PHP que ya conocen. Guía rápida impresa en cada escritorio. Soporte técnico durante las primeras 4 semanas. |
| R4 | **Hardware de kiosco falla** | Baja | Medio | Procedimiento manual documentado (operario genera turno desde su PC). URL del kiosco accesible desde cualquier dispositivo con navegador como respaldo (tablet, celular). |
| R5 | **Latencia alta de Odoo.sh desde la sucursal** | Baja | Alto | Medir latencia antes del go-live. Optimizar payloads JSON (enviar solo datos necesarios). Polling interval configurable (aumentar si hay latencia). Evaluar CDN para assets estáticos. |
| R6 | **Conflictos de secuencia de turno bajo alta concurrencia** | Baja | Medio | Usar `ir.sequence` de Odoo con `implementation='no_gap'` para evitar huecos. Transacciones atómicas. Test de carga con 100 turnos simultáneos. |
| R7 | **Ciudadanos con dificultad para usar el kiosco** | Media | Bajo | Botones grandes (≥ 60px), alto contraste, fuentes ≥ 18px. Personal de apoyo los primeros días. Señalética clara junto al kiosco. |
| R8 | **Incompatibilidad con módulo `appointment` en actualizaciones de Odoo** | Baja | Alto | Minimizar herencia del módulo nativo. Preferir composición sobre herencia donde sea posible. Documentar puntos de acoplamiento. Mantener tests de regresión. |
| R9 | **Pérdida de audio en pantalla display por políticas de autoplay del navegador** | Media | Medio | Agregar botón "Activar sonido" en pantalla display (requiere interacción del usuario al iniciar). Almacenar preferencia en localStorage. Documentar configuración de Chrome flags si es necesario. |
| R10 | **Datos personales (DNI) expuestos en pantalla pública** | Baja | Alto | DNI enmascarado en display (primeros 4 dígitos + asteriscos). No mostrar nombre completo en pantalla pública. Solo mostrar lo necesario para identificación. |

---

## Apéndice A: Manifest del Módulo

```python
# __manifest__.py
{
    'name': 'DGC Turnero - Sistema de Turnos con Kiosco',
    'version': '19.0.1.0.0',
    'summary': 'Sistema de gestión de turnos presenciales con kiosco touchscreen y pantalla de visualización',
    'description': """
        Módulo de gestión de turnos para la Dirección General de Catastro (DGC).
        Incluye kiosco de auto-registro, panel de operarios, pantalla de sala de espera,
        gestión por áreas, derivaciones, reportes y configuración.
    """,
    'author': 'DGC - Dirección General de Catastro',
    'website': 'https://www.catastro.gob.ar',
    'category': 'Services/Appointment',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'bus',
        'web',
        'appointment',
    ],
    'data': [
        # Security
        'security/security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'data/default_config_data.xml',
        # Views
        'views/dgc_appointment_area_views.xml',
        'views/dgc_appointment_turn_views.xml',
        'views/dgc_appointment_config_views.xml',
        'views/dgc_appointment_derivation_views.xml',
        'views/dgc_dashboard_views.xml',
        'views/menu_views.xml',
        # Wizards
        'wizards/dgc_turn_derive_wizard_views.xml',
        # Templates (públicas)
        'templates/kiosk_main_view.xml',
        'templates/display_queue_view.xml',
        # Reports
        'report/dgc_turn_report.xml',
        'report/dgc_turn_report_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dgc_appointment_kiosk/static/src/js/backoffice.js',
            'dgc_appointment_kiosk/static/src/css/backoffice.scss',
        ],
        'dgc_appointment_kiosk.assets_kiosk': [
            'dgc_appointment_kiosk/static/src/js/kiosk.js',
            'dgc_appointment_kiosk/static/src/css/kiosk.scss',
        ],
        'dgc_appointment_kiosk.assets_display': [
            'dgc_appointment_kiosk/static/src/js/display.js',
            'dgc_appointment_kiosk/static/src/css/display.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}
```

## Apéndice B: Secuencia de Numeración

```xml
<!-- data/ir_sequence_data.xml -->
<odoo>
    <data noupdate="1">
        <record id="seq_dgc_turn" model="ir.sequence">
            <field name="name">DGC Turn Sequence</field>
            <field name="code">dgc.appointment.turn</field>
            <field name="prefix">%(y)s%(month)s%(day)s-</field>
            <field name="padding">3</field>
            <field name="implementation">no_gap</field>
            <field name="use_date_range">True</field>
        </record>
    </data>
</odoo>
```

## Apéndice C: Cron de Cierre Diario

```xml
<!-- data/ir_cron_data.xml -->
<odoo>
    <data noupdate="1">
        <record id="cron_close_pending_turns" model="ir.cron">
            <field name="name">DGC: Cerrar turnos pendientes del día</field>
            <field name="model_id" ref="model_dgc_appointment_turn"/>
            <field name="state">code</field>
            <field name="code">model._cron_close_pending_turns()</field>
            <field name="interval_number">1</field>
            <field name="interval_type">days</field>
            <field name="nextcall">2026-03-18 03:00:00</field>
            <field name="numbercall">-1</field>
            <field name="active">True</field>
        </record>
    </data>
</odoo>
```

---

**Fin del documento PRD v1.1.0**

*Este documento debe ser versionado en Git y revisado por el equipo de desarrollo y los stakeholders antes de iniciar la implementación. Cualquier cambio debe generar una nueva versión del documento con changelog.*

---

## Changelog

### v1.1.0 — 18 de marzo de 2026

**Preguntas resueltas:**

- **Q3 (Turnos pendientes al cierre)**: El sistema calcula un tope diario por área basado en `(hora_fin - hora_inicio) / avg_service_time * max_counters`. El kiosco bloquea nuevos turnos al alcanzar el tope. Turnos residuales se cancelan vía cron al cierre.
- **Q6 (Operarios en paralelo)**: Parametrizable por área vía `max_counters`. Geodesia = 1, Información Territorial (PB) = N boxes configurables. El tope diario se multiplica por la cantidad de boxes.
- **Q9 (Directorio de ciudadanos)**: No existe directorio completo aún. El sistema busca por CUIT/DNI en `res.partner` y crea si no existe, nunca duplica.

**Nuevos requisitos funcionales:**

- **RF-02.17**: Control de capacidad diaria por área con cálculo automático del tope.
- **RF-02.18**: Integración con `res.partner` sin duplicados — búsqueda por `vat` (CUIT/DNI).
- **RF-02.19**: Detección de email conflictivo — notifica al ciudadano y ofrece actualización.
- **RF-02.20**: Booleano configurable `allow_multiple_turns` para permitir o no turnos múltiples por ciudadano.

**Cambios en modelo de datos:**

- `dgc.appointment.area`: nuevos campos computed `max_daily_turns` y `remaining_turns_today`.
- `dgc.appointment.config`: nuevos campos `allow_multiple_turns`, `branding_logo`, `branding_name`, `branding_primary_color`, `branding_bg_color`.
- `dgc.appointment.turn._find_or_create_partner()`: método para búsqueda/creación de `res.partner` con deduplicación por CUIT y detección de conflicto de email.

**Cambios en API:**

- `POST /kiosk/api/turn/create`: nuevo campo `update_email` en request; nuevos campos `remaining_capacity`, `citizen_name`, `partner_id` en response; nueva response `EMAIL_CONFLICT`; nuevos errores `CAPACITY_FULL` y `EMAIL_CONFLICT`.
- `POST /kiosk/api/areas`: nuevos campos `max_daily_turns`, `remaining_capacity`, `is_full` en response.

**Nuevos tests:**

- 10 tests adicionales para capacidad diaria, dedup de partner, conflicto de email, y turnos múltiples.

**Wireframes actualizados:**

- Paso 2 (Selección de área): muestra cupos disponibles y "CUPOS AGOTADOS" cuando el área está llena.
- Configuración: nueva sección "Branding / Identidad Visual" y checkbox de turnos múltiples.

### v1.0.0 — 17 de marzo de 2026

- Versión inicial del PRD.
