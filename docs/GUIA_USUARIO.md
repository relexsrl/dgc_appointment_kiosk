# Guía de Usuario - Sistema Turnero DGC

## Versión 19.0.6.0.0

---

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Niveles de Acceso](#niveles-de-acceso)
3. [Para Ciudadanos - Kiosco](#para-ciudadanos---kiosco)
4. [Para Operadores](#para-operadores)
5. [Para Responsables de Área](#para-responsables-de-área)
6. [Para Administradores](#para-administradores)
7. [Solución de Problemas](#solución-de-problemas)
8. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## Introducción

### ¿Qué es el Sistema Turnero DGC?

El Sistema Turnero DGC es una solución integral de gestión de turnos (citas) desarrollada para la Dirección General de Catastro (DGC). Permite que los ciudadanos soliciten turnos de atención a través de un kiosco táctil y que los operadores de atención las colas de espera desde paneles modernos.

### Características Principales

- **Kiosco de Autoservicio**: Interface táctil intuitiva para que los ciudadanos soliciten turnos
- **Pantalla de Cola Pública**: Muestra el número de turno siendo atendido y los próximos turnos
- **Panel del Operador**: Control completo de turnos en tiempo real desde el mostrador
- **Panel de Administración**: Monitoreo integral de todas las áreas y operadores
- **Gestión de Derivaciones**: Derivar turnos entre áreas cuando es necesario
- **Estadísticas Detalladas**: Métricas de desempeño, tiempos de espera y atención

### Beneficios

- Mejor experiencia del ciudadano: proceso ordenado y transparente
- Reducción de tiempos de espera
- Control centralizado de todas las áreas
- Seguimiento en tiempo real de operaciones
- Reportes y estadísticas detalladas

---

## Niveles de Acceso

El sistema cuenta con cuatro niveles de acceso definidos según el rol del usuario:

### 1. Ciudadano (Kiosco Público)

**Acceso**: Sin autenticación
- Accede solo al kiosco de autoservicio
- Puede solicitar nuevos turnos
- Puede consultar sus turnos activos

### 2. Operador

**Acceso**: Usuario autenticado con grupo "Operador"
- Acceso al Panel del Operador
- Gestión de turnos en tiempo real (llamar, atender, finalizar, marcar no presentado)
- Creación manual de turnos
- Derivación de turnos a otras áreas
- Visualización de turnos en sus áreas asignadas

### 3. Responsable de Área

**Acceso**: Usuario autenticado con grupo "Responsable de Área"
- Acceso al Panel de Administración
- Visualización de todas las áreas asignadas
- Gestión de operadores y puestos de atención
- Configuración de fechas no laborables
- Estadísticas detalladas del área
- Todas las funciones del Operador

### 4. Administrador

**Acceso**: Usuario autenticado con grupo "Administrador"
- Acceso a todas las funciones del sistema
- Configuración global del sistema
- Acceso a todas las áreas y operadores
- Configuración de parámetros generales
- Acceso a herramientas de administración avanzadas

---

## Para Ciudadanos - Kiosco

### Solicitar un Nuevo Turno

El kiosco presente una interfaz clara y amigable para solicitantes de turnos.

#### Paso 1: Pantalla de Bienvenida

Al iniciar, verá dos opciones:

- **Sacar Nuevo Turno** (botón principal con símbolo +)
- **Consultar mi Turno** (botón secundario con signo ?)

Para un nuevo turno, presione el botón "Sacar Nuevo Turno".

#### Paso 2: Ingresar DNI o CUIT

El kiosco muestra un teclado numérico táctil. Puede elegir entre:

- **DNI**: Documento Nacional de Identidad (7-8 dígitos)
- **CUIT**: Código Único de Impuestos Tributarios (11 dígitos con formato XX-XXXXXXXX-X)

**Para cambiar entre DNI y CUIT**: Use el switch (interruptor) deslizable en la pantalla.

**Ingreso de número**:
1. Presione los números del teclado numérico
2. Vea su número aparecer en el campo de entrada
3. Botón "Borrar": Elimina el último dígito
4. Botón "Siguiente": Se activa cuando el número es válido

**Validación automática**:
- El sistema verifica que el número tenga la longitud correcta
- Valida el CUIT según el algoritmo oficial
- Muestra mensaje de error si el número es inválido

#### Paso 3: Seleccionar el Área

Después de ingresar el DNI válido, verá una lista de áreas disponibles. Cada área muestra:

- **Nombre del área** (ej: "Catastro", "Licencias")
- **Código** (identificador único)
- **Estado de disponibilidad**:
  - Verde: Area disponible, hay turnos disponibles
  - Gris: Area sin turnos disponibles (capacidad alcanzada)
  - Rojo: Area cerrada hoy

**Seleccione el área** donde desea ser atendido. El sistema verificará:

- Que haya turnos disponibles para hoy
- Que el área este abierta
- Que no tenga ya un turno activo en esa área y fecha

#### Paso 4: Confirmación y Número de Turno

Después de seleccionar el área, verá la pantalla de confirmación con:

- **Número de Turno**: Número único para su consulta (ej: "GAT-0042")
- **Área de Atención**: Nombre del área seleccionada
- **Ubicación**: Piso y sector del mostrador (si está configurado)
- **Turnos en Espera**: Cantidad de personas esperando antes de usted
- **Tiempo Estimado de Espera**: Estimación en minutos

El kiosco retornará automáticamente a la pantalla inicial en 10 segundos.

**Importante**: Anote el número de turno. Lo necesitará para consultar el estado de su turno.

### Consultar mi Turno

Para saber en qué estado está su turno activo:

1. En la pantalla inicial, presione **"Consultar mi Turno"**
2. Ingrese su DNI o CUIT usando el teclado numérico
3. El sistema mostrará:
   - Número de turno
   - Área y ubicación
   - Estado actual (En espera, Siendo llamado, En atención, Finalizado)
   - Número de veces que fue llamado

### Estados del Turno (Desde la Perspectiva del Ciudadano)

- **En Espera**: Su turno está en la cola, esperando ser llamado
- **Siendo Llamado**: Su turno ha sido llamado, debe dirigirse al mostrador indicado
- **En Atención**: Está siendo atendido en el mostrador
- **Finalizado**: La atención se completó
- **No se Presentó**: No se presentó cuando fue llamado

---

## Para Operadores

Los operadores atienden a los ciudadanos desde los mostradores y gestionan los turnos a través del **Panel del Operador**.

### Panel del Operador

El Panel del Operador es la interfaz principal para la gestión de turnos.

#### Acceso

- En el menú principal de Odoo, seleccione **Turnero DGC → Panel Operador**
- El panel carga automáticamente los datos de su sesión actual

#### Elementos Principales

##### 1. Turno Actual

En la parte superior central, muestra:

- **Número de Turno**: Identificador único (ej: "GAT-0042")
- **DNI del Ciudadano**: Documento de identidad
- **Nombre**: Nombre completo del ciudadano
- **Email**: Contacto del ciudadano
- **Caja/Box**: Número de mostrador asignado
- **Observaciones**: Notas adicionales
- **Tiempo Transcurrido**: Cronómetro que muestra cuánto lleva siendo atendido (formato HH:MM:SS)

##### 2. Botones de Acción

Debajo del turno actual, encontrará los botones para gestionar el estado del turno:

| Botón | Acción | Uso |
|-------|--------|-----|
| **Llamar** | Pasa el turno a estado "Llamando" | Primera llamada al turno |
| **Re-llamar** | Incrementa el contador de llamadas | Si el ciudadano no escuchó la primera llamada |
| **Atender** | Pasa a estado "Atendiendo" | Cuando el ciudadano llega al mostrador |
| **Finalizar** | Marca el turno como completado | Cuando termina la atención |
| **No se Presentó** | Marca como no presentado | Si llamó pero no se presentó |
| **Derivar** | Abre el asistente de derivación | Para trasladar el turno a otra área |

##### 3. Turnos en Espera

En la sección izquierda, una lista ordenada de todos los turnos pendientes:

- Ordenados por fecha de creación (más antiguos primero)
- Muestra: Número de turno, DNI, Nombre, Área, Tiempo en cola
- Click para ver detalles
- Color de fondo indica prioridad o estado

##### 4. Turnos Finalizados (Últimas 50)

En la sección derecha inferior, historial de turnos completados hoy:

- Ordenados por fecha de finalización (más recientes primero)
- Muestra: Número de turno, DNI, Nombre, Duración de atención, Hora de finalización
- Útil para verificar desempeño

##### 5. Indicadores KPI

En la parte superior derecha, métricas del desempeño actual:

| Métrica | Descripción |
|---------|-------------|
| **Turnos Atendidos** | Cantidad de turnos completados hoy |
| **Duración Promedio** | Tiempo medio de atención (en minutos) |
| **Pendientes** | Total de turnos esperando en el sistema |
| **Derivaciones** | Turnos derivados a otras áreas hoy |

##### 6. Estado de la Caja/Mostrador

En la esquina superior derecha:

- **Símbolo de Caja**: Indica estado (abierto/cerrado)
- **Cantidad de Cajas Activas**: Número de mostradores funcionando
- Click para abrir/cerrar su caja

### Estados del Turno en el Panel Operador

| Estado | Descripción | Desde | Hacia |
|--------|-------------|-------|-------|
| **Nuevo** | Turno recién creado | (inicial) | En espera |
| **En Espera** | Esperando ser llamado | Nuevo | Llamando |
| **Llamando** | Siendo llamado al mostrador | En espera | Atendiendo, No se presentó |
| **Atendiendo** | En atención actualmente | Llamando | Finalizado |
| **Finalizado** | Atención completada | Atendiendo | (final) |
| **Derivado** | Trasladado a otra área | Llamando | (final, nuevo en área destino) |
| **No se Presentó** | No se presentó cuando fue llamado | Llamando | (final) |

### Flujo Típico de Operación

```
1. Turno entra en sistema (Estado: Nuevo → En Espera)
2. Presione LLAMAR para llamar al ciudadano (Estado: Llamando)
3. El ciudadano se presenta en el mostrador
4. Presione ATENDER para iniciar atención (Estado: Atendiendo)
5. Realice la atención necesaria
6. Presione FINALIZAR cuando termine (Estado: Finalizado)
```

### Crear Turno Manualmente

A veces es necesario crear turnos manualmente (por teléfono, ventanilla, etc.).

#### Acceso

- En el menú principal: **Turnero DGC → Turnos** → Botón "Crear"
- O use el asistente desde el Panel del Operador

#### Datos Requeridos

- **DNI/CUIT**: Documento del ciudadano (validado automáticamente)
- **Nombre Completo**: Nombre del ciudadano
- **Email**: Contacto (opcional)
- **Área**: Seleccione el área donde será atendido
- **Observaciones**: Notas adicionales (opcional)

#### Proceso

1. Ingrese el DNI/CUIT
2. El sistema intenta encontrar un contacto existente; si existe, carga sus datos
3. Corrija o complete nombre y email según sea necesario
4. Seleccione el área (solo áreas que usted tiene permisos)
5. Agregue observaciones si es necesario
6. Presione "Crear Turno"

El sistema validará:
- Que el DNI sea válido
- Que no exista un turno activo para el mismo DNI, área y fecha
- Que la capacidad diaria no esté alcanzada

### Derivar Turnos

Cuando un ciudadano necesita ser atendido en otra área, puede derivar su turno.

#### Cuándo Derivar

- El asunto requiere atención en otra área
- El ciudadano solicita ser atendido en otra área
- Necesidad administrativa

#### Proceso de Derivación

1. Asegúrese que el turno esté en estado "Llamando"
2. Presione el botón **"Derivar"**
3. Se abrirá un asistente con:
   - **Área Actual**: Automáticamente precargada (solo lectura)
   - **Área Destino**: Seleccione la nueva área
   - **Motivo**: Escriba la razón de la derivación
4. Presione **"Derivar"**

#### Resultado de la Derivación

- El turno original en la área actual cambia a estado "Derivado"
- Se crea un nuevo turno en el área destino con los mismos datos del ciudadano
- Se registra la derivación con toda la información
- El ciudadano puede ver su nuevo turno

### Estadísticas e Historial

#### Ver Historial de Llamadas

Cada turno mantiene un registro de cuántas veces fue llamado:

- En el detalle del turno, verá "Veces Llamado: X"
- El historial completo está en la pestaña "Historial de Llamadas"

#### Analizar Desempeño

Use los indicadores KPI del panel:
- Cantidad de turnos atendidos
- Duración promedio de atención
- Número de derivaciones
- Total de pendientes en el área

---

## Para Responsables de Área

Los Responsables de Área gestionan un conjunto de áreas de DGC. Tienen acceso a un **Panel de Administración** con vista integral de todas las operaciones.

### Panel de Administración

El Panel de Administración proporciona visibilidad completa sobre las operaciones de las áreas.

#### Acceso

- En el menú principal de Odoo, seleccione **Turnero DGC → Panel Admin**
- El panel carga automáticamente las áreas asignadas a su cuenta

#### Resumen Global

En la parte superior del panel, encontrará un resumen general con:

| Métrica | Descripción |
|---------|-------------|
| **Total en Espera** | Ciudadanos esperando en todas las áreas |
| **Total Siendo Atendidos** | En atención en ese momento |
| **Total Finalizados** | Completados en el día |
| **Total No Presentados** | Que no se presentaron cuando fueron llamados |
| **Total Derivados** | Trasladados a otras áreas |
| **Turnos Restantes Disponibles** | Capacidad aún disponible para hoy |
| **Duración Promedio de Atención** | En minutos |
| **Tiempo Promedio de Espera** | En minutos |

#### Vista por Área

Para cada área asignada, verá una tarjeta con:

**Información General**:
- Nombre y código del área
- Color distintivo
- Estado de disponibilidad (abierta/cerrada)

**Estadísticas del Día**:
- Turnos en espera
- Siendo atendidos
- Finalizados
- No presentados
- Derivados
- Turnos máximos disponibles
- Duración promedio
- Tiempo de espera promedio

**Operadores y Puestos**:
- Lista de operadores asignados
- Estado de cada operador (en línea, atendiendo, inactivo)
- Número de caja/mostrador
- Turno actual que atiende

**Cajas/Mostradores**:
- Lista de todas las ventanillas
- Estado (activo/inactivo)
- Operador asignado

### Gestionar Operadores y Puestos

Acceda a través de **Turnero DGC → Áreas** para configurar:

#### Asignación de Operadores

1. Seleccione el área a gestionar
2. En la pestaña "Boxes/Ventanillas", agregue operadores
3. Para cada operador, asigne:
   - Usuario (operador del sistema)
   - Número de caja/mostrador
   - Estado (activo/inactivo)

#### Activar/Desactivar Puestos

- Desde el Panel de Administración, operadores pueden abrir/cerrar su propia caja
- Como Responsable de Área, puede forzar estados desde la configuración del área

### Configurar Fechas No Laborables

Para indicar que un área no funcionará en ciertos días (feriados, mantenimiento, etc.):

#### Acceso

- **Turnero DGC → Áreas** → Seleccionar área → Pestaña "Fechas No Laborables"

#### Agregar Fecha No Laborable

1. Presione "Crear"
2. Seleccione la fecha
3. Agregue una descripción (ej: "Feriado Nacional", "Mantenimiento")
4. Presione "Guardar"

#### Efecto

- El área aparecerá como "Cerrada" en el kiosco para esa fecha
- Los ciudadanos no podrán solicitar turnos
- No se mostrarán turnos disponibles
- El sistema automáticamente recalcula capacidad

### Gestionar Configuración del Área

En **Turnero DGC → Áreas**, configure para cada área:

| Campo | Descripción |
|-------|-------------|
| **Nombre** | Nombre visible del área |
| **Código DGC** | Código único (ej: "GAT", "LIC") |
| **Ubicación** | Piso y sector (visible en kiosco) |
| **Color** | Color distintivo en pantallas |
| **Cantidad de Puestos** | Máximo de mostradores simultáneos |
| **Duración de Atención** | Tiempo promedio esperado (en horas) |
| **Horarios de Funcionamiento** | Franjas horarias por día de semana |
| **Mensaje de Bienvenida** | Texto mostrado en el kiosco |

### Estadísticas Detalladas

Acceda a **Turnero DGC → Estadísticas** para generar reportes y gráficos.

#### Datos Disponibles

- Turnos procesados por período
- Tiempos de espera y duración de atención
- Desempeño por operador
- Tasa de no presentados
- Derivaciones entre áreas

---

## Para Administradores

Los Administradores tienen acceso a todas las funciones del sistema, incluyendo configuración avanzada.

### Panel de Administración Completo

Los administradores ven:
- Todas las áreas del sistema
- Todos los operadores y sus estadísticas
- Vista global de todas las operaciones

### Configuración Global del Sistema

En **Turnero DGC → Configuración → Ajustes**, puede configurar:

#### Horarios Generales (Fallback)

| Parámetro | Descripción | Valor Predeterminado |
|-----------|-------------|---------------------|
| **Hora de Inicio** | Hora de apertura (fallback global) | 8:00 (8.0) |
| **Hora de Cierre** | Hora de cierre (fallback global) | 14:00 (14.0) |

Nota: Los horarios específicos de cada área sobrescriben estos valores.

#### Configuración de Comportamiento

| Parámetro | Descripción | Valores |
|-----------|-------------|--------|
| **Permitir Múltiples Turnos** | Un ciudadano puede tener múltiples turnos en el mismo día | True/False |
| **Requerir Email en Kiosco** | El email es obligatorio al solicitar turno | True/False |
| **Mostrar Notas** | Mostrar campo de observaciones en el kiosco | True/False |

#### Duración de Sesión del Kiosco

- **Timeout del Kiosco**: Tiempo de inactividad antes de volver a bienvenida (segundos)

### Gestionar Usuarios y Permisos

En **Configuración → Gestión de Usuarios**, cree y administre cuentas.

#### Crear un Operador

1. Vaya a **Configuración → Usuarios → Crear**
2. Ingrese:
   - Nombre de usuario (login)
   - Nombre completo
   - Email
3. En la pestaña "Permisos", asigne:
   - Grupo: **Operador DGC**
4. Guarde

#### Asignar Operador a Área

1. En el menú **Turnero DGC → Áreas**, seleccione el área
2. En la pestaña "Operadores Asignados", agregue el usuario
3. El operador ahora verá esa área en el Panel del Operador

#### Crear un Responsable de Área

1. Cree el usuario igual que un Operador
2. En la pestaña "Permisos", asigne:
   - Grupo: **Responsable de Área**
3. En el menú **Turnero DGC → Áreas**, para cada área que gestionará:
   - Agregue el usuario en "Operadores Asignados"
4. El usuario podrá ver esas áreas en el Panel de Administración

#### Crear un Administrador

1. Solo el administrador actual puede crear nuevos administradores
2. Cree el usuario normalmente
3. En "Permisos", asigne:
   - Grupo: **Administrador DGC**
4. El usuario tendrá acceso completo al sistema

### Mantenimiento y Monitoreo

#### Ver Logs y Errores

- Sistema registra todas las acciones (creación, cambio de estado, derivaciones)
- Accede a través del formulario de cada turno

#### Cron Jobs (Tareas Automáticas)

El sistema ejecuta automáticamente:

- **Cierre de Turnos Pendientes**: Cada noche marca como "No Presentados" aquellos turnos llamados pero nunca atendidos
- **Limpieza de Caché**: Operaciones de mantenimiento automáticas

#### Gestionar Áreas Masivamente

Para configuraciones a gran escala:
1. Vaya a **Turnero DGC → Áreas**
2. Use filtros y acciones masivas para editar múltiples áreas
3. Asigne horarios y configuración en lote

---

## Solución de Problemas

### Problemas del Kiosco

#### El kiosco no responde al pulsar botones

**Causa**: Posible congelamiento de la interfaz
**Solución**:
1. Espere 5 segundos sin tocar nada
2. Presione el botón "Volver" si está disponible
3. Si persiste, recargue la página (F5)
4. Si aún no funciona, reinicie el navegador

#### "El DNI ingresado no es válido"

**Causas posibles**:
- El número es muy corto (menos de 7 dígitos)
- El CUIT no tiene el formato correcto
- El CUIT no pasa la validación matemática

**Solución**:
- DNI: Verifique que tiene 7-8 dígitos
- CUIT: Debe tener formato XX-XXXXXXXX-X (11 dígitos con guiones)
- Presione "Borrar" y reingrese el número

#### "Ya existe un turno pendiente para este DNI en la misma fecha"

**Causa**: El ciudadano ya tiene un turno activo para esa área y día

**Solución**:
- El ciudadano puede consultar su turno existente
- Si realmente necesita otro, un operador debe finalizar o derivar el anterior
- O crear manualmente un turno en otra área

#### "No hay más turnos disponibles para esta área hoy"

**Causa**: Se alcanzó la capacidad máxima diaria del área

**Solución**:
- Intente otra área si aplica
- Intente nuevamente mañana
- Un operador puede crear un turno manualmente si hay capacidad real

#### El kiosco no muestra algunas áreas

**Causa**: El área está cerrada hoy (non-working date, sin operadores, sin horarios)

**Solución**:
- Verifique con el Responsable de Área
- El área podría estar en mantenimiento

### Problemas del Panel Operador

#### No veo el botón "Crear Turno"

**Causa**: Permisos insuficientes
**Solución**: Verifique que esté en grupo "Operador" y tenga áreas asignadas

#### El botón "Llamar" está deshabilitado

**Causa**: El turno no está en estado "En Espera" o "Llamando"
**Solución**: Solo los turnos esperando pueden ser llamados. Verifique el estado actual.

#### Los datos no se actualizan en tiempo real

**Causa**: Conexión perdida con el servidor de buses (comunicación en tiempo real)
**Solución**:
1. Revise su conexión a internet
2. Recargue el panel (F5)
3. Si el problema persiste, contacte al administrador

#### "Error: Turno no encontrado"

**Causa**: El turno fue eliminado o el ID es incorrecto
**Solución**: Recargue el panel, intente nuevamente

#### El panel está muy lento

**Causa**: Demasiados turnos en el sistema, conexión lenta
**Solución**:
1. Cierre otras pestañas/aplicaciones
2. Verífique su conexión a internet
3. Contacte al administrador para optimizar el sistema

### Problemas del Panel Administración

#### No veo una de mis áreas

**Causa**: El área no está asignada a su usuario
**Solución**: Contacte al administrador para asignarle el área

#### Los números no coinciden entre Panel Operador y Panel Admin

**Causa**: Lag en actualización o cambios recientes
**Solución**: Presione F5 para recargar datos. La sincronización es automática.

#### "Solo los responsables de área pueden acceder al panel"

**Causa**: Su usuario no tiene el grupo "Responsable de Área"
**Solución**: Contacte al administrador para asignarle el rol

### Problemas de Acceso

#### "No tiene permisos para crear turnos en esta área"

**Causa**: No está asignado como operador en esa área
**Solución**: El Responsable de Área o Administrador debe agregarlo a la configuración del área

#### No aparece el menú "Turnero DGC"

**Causas posibles**:
- No tiene ningún grupo DGC asignado
- El módulo no está instalado

**Solución**: Contacte al administrador

#### Olvidé mi contraseña

**Solución**:
1. En la pantalla de login, presione "¿Olvido su contraseña?"
2. Ingrese su usuario/email
3. Recibirá un enlace para resetear
4. Si no recibe el email, contacte al administrador

### Problemas de Configuración

#### Los horarios de área no se reflejan en el kiosco

**Causa**: Puede estar usando fallback global o la configuración no se guardó correctamente
**Solución**:
1. Verifique que el área tiene horarios configurados (pestaña Horarios)
2. Recargue el kiosco (F5)

#### La capacidad diaria parece incorrecta

**Causa**: Depende de horarios, cantidad de puestos y duración de servicio
**Solución**:
- **Fórmula**: (Minutos de funcionamiento / Duración servicio en minutos) × Número de puestos
- Ejemplo: (6 horas = 360 min / 15 min por turno) × 3 puestos = 72 turnos
- Verifique todos estos parámetros en el área

---

## Preguntas Frecuentes

### General

#### ¿Es gratuito solicitar un turno?
Sí, todos los turnos del sistema DGC son gratuitos y están disponibles para todos los ciudadanos sin costo.

#### ¿Puedo solicitar turno antes de las 8am?
Los turnos están disponibles durante los horarios de funcionamiento de cada área (por defecto 8:00 a 14:00). Consulte los horarios específicos en el kiosco.

#### ¿Cuánto tiempo debo esperar?
El tiempo de espera depende de:
- Cantidad de personas esperando
- Cantidad de operadores disponibles
- Complejidad de cada trámite

El kiosco muestra una estimación al confirmar el turno.

### Ciudadanos - Kiosco

#### ¿Qué pasa si pierdo mi número de turno?
Puede consultar su turno nuevamente:
1. Presione "Consultar mi Turno"
2. Ingrese su DNI
3. Verá todos sus turnos activos

#### ¿Puedo transferir mi turno a otra persona?
No directamente. El turno está vinculado al DNI. Si otra persona necesita atención, debe solicitar su propio turno.

#### ¿Qué significa "En espera"?
Que su turno está en la cola y pronto será llamado. Cuando sea su turno, el kiosco lo anunciará y se mostrará en la pantalla pública.

#### Mi turno dice "No se presentó" pero sí me presenté
Contacte al operador del mostrador. Puede haber sido un error y pode recrear un nuevo turno. Guarde la evidencia de que se presentó.

#### ¿Puedo solicitar turno para otra persona?
Solo si tiene su DNI y datos. El turno está a nombre de esa persona. Los operadores pueden crear turnos manualmente para citaciones previas.

### Operadores

#### ¿Cuál es la diferencia entre "Llamar" y "Re-llamar"?
- **Llamar**: Pasa el turno a estado "Llamando" la primera vez
- **Re-llamar**: Incrementa el contador si el ciudadano no escuchó o no se presentó a la primera llamada

#### ¿Qué pasa si presiono "No se presentó"?
- El turno se marca como "No Presentado"
- Es considerado en estadísticas como un turno no atendido
- El ciudadano debe solicitar un nuevo turno si lo desea

#### ¿Puedo deshacer el cambio de estado?
No es posible mediante la interfaz regular. Contacte al administrador si necesita corregir un estado.

#### ¿Cómo sé cuántas veces fue llamado un turno?
El panel muestra "Veces Llamado: X" en la información del turno actual. El historial completo está en la pestaña "Historial de Llamadas".

#### ¿Qué pasa si se desconecta el panel?
El panel mostrará una alerta de desconexión. Recargue la página (F5) para reconectarse. Los turnos se sincronizarán automáticamente.

### Responsables de Área

#### ¿Cómo sé si un operador está disponible?
El Panel de Administración muestra el estado de cada operador:
- **En línea**: Conectado y trabajando
- **Atendiendo**: Tiene un turno actual en atención
- **Inactivo**: Conectado pero sin turno actual
- **Sin conexión**: No está conectado

#### ¿Cómo aumento la capacidad de un área?
La capacidad depende de:
1. **Cantidad de puestos**: Aumente "Cantidad de Puestos" en la configuración del área
2. **Duración de servicio**: Reduzca "Duración de Atención" si es posible
3. **Horarios**: Extienda los horarios de funcionamiento

La capacidad = (Minutos de funcionamiento / Duración por turno) × Puestos

#### ¿Puedo ver el historial de un operador específico?
Sí, en el formulario de turno, use los filtros para ver solo turnos atendidos por ese operador.

#### ¿Cómo reporto un problema técnico?
Documente:
- Hora del incidente
- Pasos que reproduzcan el problema
- Mensaje de error (si aplica)
- Contacte al administrador del sistema

### Administradores

#### ¿Cómo hago un respaldo de los datos?
El sistema de respaldo depende de su infraestructura Odoo. Consulte con el equipo de TI.

#### ¿Puedo exportar reportes?
Sí, en la mayoría de vistas puede usar el botón "Exportar" para descargar a Excel/CSV.

#### ¿Cuál es el volumen máximo de turnos que soporta el sistema?
Depende de su infraestructura. El sistema está optimizado para:
- Miles de turnos por día
- Cientos de operadores simultáneos
- Múltiples áreas

Para más información sobre escalabilidad, contacte a Relex SRL.

#### ¿Cómo agrego un área nueva?
1. **Turnero DGC → Áreas → Crear**
2. Configure:
   - Nombre y código
   - Cantidad de puestos
   - Horarios
   - Duración de atención
3. Agregue operadores en "Boxes"
4. Guarde

El área aparecerá en el kiosco inmediatamente.

#### ¿Cada cuánto se sincroniza el Panel Admin con los datos?
La sincronización es automática y en tiempo real mediante el sistema de buses de Odoo:
- Cambios en turnos: < 1 segundo
- Cambios en operadores: < 1 segundo
- Cambios en cajas: < 1 segundo

Si hay lag, verifique la conectividad.

---

## Información de Contacto y Soporte

**Empresa Desarrolladora**: Relex SRL
**Sitio Web**: https://www.relex.com.ar

Para reportar problemas o sugerir mejoras, contacte a su administrador del sistema.

---

## Versión del Documento

- **Versión del Sistema**: 19.0.6.0.0
- **Fecha de Actualización**: 2026-03-27
- **Idioma**: Español (Argentina)

---

## Apéndice: Glosario

| Término | Significación |
|---------|---------------|
| **Turno** | Cita o número de orden para ser atendido |
| **Área** | Sección o departamento de servicio |
| **Operador** | Persona que atiende en un mostrador |
| **Caja/Box** | Mostrador o ventanilla de atención |
| **DNI** | Documento Nacional de Identidad (7-8 dígitos) |
| **CUIT** | Código Único de Impuestos Tributarios (11 dígitos) |
| **Derivación** | Traslado de un turno a otra área |
| **Estado** | Situación actual del turno |
| **KPI** | Key Performance Indicator (Indicador de desempeño) |
| **Panel** | Interfaz de control para operadores/administradores |
| **Kiosco** | Máquina de autoservicio táctil para ciudadanos |

---

## Notas Finales

Este sistema fue desarrollado específicamente para la Dirección General de Catastro con el objetivo de mejorar la experiencia de los ciudadanos y optimizar la gestión de recursos.

Si tiene preguntas sobre funcionalidades específicas no cubiertas en esta guía, consulte con el Administrador del Sistema.

**¡Gracias por usar el Sistema Turnero DGC!**
