# Permisos y auditoría

El control de acceso tiene cuatro capas que se aplican en cascada. Para que un
usuario edite una celda de la matriz deben cumplirse todas.

```
0. ¿El plan es de SU MUNICIPIO?         PlanDesarrollo.visibles_para()
1. ¿Tiene sesión iniciada?              @login_required
2. ¿Su rol puede editar ESA COLUMNA?    ColumnPermission
3. ¿Puede editar ESA FILA?              RowPermission
```

## Capa 0 — Municipio

Un plan pertenece a la entidad territorial, no a quien lo creó. `municipio_id`
apunta al usuario que lo dio de alta, pero la visibilidad se resuelve
comparando **municipio y departamento** del usuario con los del propietario
(`PlanDesarrollo.filtro_visibilidad`). Se comparan los dos campos porque en
Colombia hay nombres de municipio repetidos en departamentos distintos.

Consecuencias:

- Todos los funcionarios de una alcaldía comparten el mismo plan, sin importar
  quién lo creó.
- Nadie ve el plan de otra entidad, ni siquiera un administrador.
- Los identificadores no son adivinables entre entidades: pedir el plan de otro
  municipio por su `id` devuelve 404 o redirige, nunca sus datos.

Toda consulta de planes debe pasar por `PlanDesarrollo.visibles_para(usuario)` o
por los ayudantes `get_plan_or_404` / `get_plan_or_redirect` de `planes.py`.

## Capa 1 — Autenticación

Flask-Login con sesión respaldada por JWT. Todas las rutas de `/admin` pasan
además por `require_admin()`, un `before_request` del blueprint que exige
`current_user.is_admin()`.

Un usuario es administrador si tiene asignado un rol llamado `admin` o
`administrador`, o —cuando no tiene ningún rol asignado— si su `legacy_role`
es `admin`.

## Capa 2 — Permisos de columna (rol)

Cada `Role` tiene **37 filas** en `column_permissions`, una por columna de la
matriz, cada una con `can_view` y `can_edit`.

### Roles por defecto

| Rol | De sistema | Columnas editables | Para quién |
|---|---|---|---|
| **Administrador** | Sí | 37 de 37 | Secretaría de Planeación, soporte |
| **Editor General** | Sí | 33 de 37 | Coordinador del plan. Todo salvo códigos y dependencia responsable |
| **Editor de Ejecución** | No | 18 de 37 | Enlaces de secretaría. Ejecución, cumplimiento, población y observaciones |
| **Editor de Metas** | No | 10 de 37 | Formulación. Metas, indicadores, línea base, unidad, sentido |
| **Visualizador** | Sí | 0 de 37 | Consulta: control interno, veedurías, concejo |

Los cinco pueden **ver** las 37 columnas. Los roles de sistema no se pueden
borrar desde la interfaz.

Los roles se siembran con `flask init-db`, `flask crear-roles` o
`python scripts/init_db.py`. Para recrearlos o repararlos en una instalación ya
existente: `python scripts/init_roles.py`.

### Dónde se aplica

El nombre de columna que viaja en el formulario de la vista Excel
(`meta_2024`, `ejecucion_1_trimestre`) **no** es el que guardan los permisos
(`META 2024`, `EJECUCIÓN I TRIMESTRE `). `app/services/edicion_celda.py`
traduce entre ambos con `columna_de_la_matriz()`, y `puede_editar()` es la
función que debe usarse para autorizar una edición.

### Cómo se decide

`User.can_edit_column(nombre)`:

1. Si el usuario es administrador → `True` sin más comprobaciones.
2. Si **alguno** de sus roles activos permite editar esa columna → `True`.
3. En caso contrario → `False`.

Los roles **suman**: un usuario con dos roles puede editar la unión de las
columnas de ambos.

> Los nombres de columna son los del Excel original, con sus erratas y espacios
> finales (`'INDICADORES '`, `'DEPENDENCIA RESPOSABLE'`). Al comparar por
> nombre hay que respetarlos exactamente.

### Editar los permisos de un rol

`/admin/roles` → *Editar*. Las columnas se agrupan por categoría (`estructura`,
`indicadores`, `ejecucion`, `cumplimiento`, `poblacion`, `observaciones`), que
`ColumnPermission._assign_category()` deduce del nombre.

## Capa 3 — Permisos de fila

Los permisos de columna son horizontales: afectan a *todas* las filas. Los
`RowPermission` son verticales: dan acceso a una **rama concreta** de la
jerarquía.

Un permiso de fila apunta a un plan y a **una** entidad:

| `permission_scope` | Alcance concedido |
|---|---|
| `linea` | Toda la línea estratégica y lo que cuelga de ella |
| `componente` | El componente y sus programas, proyectos e indicadores |
| `programa` | El programa y lo que cuelga de él |
| `proyecto` | El proyecto y sus indicadores |
| `indicador` | Solo ese indicador |

Ejemplo típico: la Secretaría de Salud recibe el rol *Editor de Ejecución*
(qué columnas) más un permiso de fila sobre el componente «Salud Pública» (qué
filas). Así puede registrar la ejecución trimestral únicamente de sus propios
indicadores.

Se gestionan en `/admin/row-permissions` y `/admin/user-row-permissions`.

Los administradores saltan esta capa: `User.can_edit_row()` devuelve `True` para
ellos sin consultar la tabla.

## Contraseñas temporales

Al crear un usuario desde `/admin/users/create` el sistema genera una contraseña
temporal con caducidad (`UserTempPassword`). Si el municipio tiene configurado un
servidor SMTP en `/admin/smtp-config`, las credenciales se envían por correo; si
no, el administrador puede consultarlas en
`/admin/users/<id>/temp-password`.

## Auditoría

### Qué se registra

Toda edición hecha desde la vista Excel genera un `EditJustification` con:

- columna afectada e indicador,
- valor anterior y valor nuevo,
- **justificación escrita por el usuario** (obligatoria),
- autor, fecha y archivo de soporte si se adjuntó.

### Actas en PDF

Además del registro en base de datos, cada edición produce un **acta PDF con
marca de agua** en `audit_files/user_<id>/`, con nombre
`AAAAMMDD_HHMMSS_plan_<id>_<columna>.pdf`.

Si ReportLab no está instalado o falla, `audit_file_system.py` escribe un `.txt`
con el mismo contenido. La pista de auditoría no se pierde en ningún caso.

### Dónde consultarla

| Ruta | Quién | Qué muestra |
|---|---|---|
| `/audit/` | Cualquier usuario | Sus propios cambios |
| `/audit/files` | Cualquier usuario | Sus actas, descargables |
| `/audit/summary` | Cualquier usuario | PDF consolidado de todos sus cambios |
| `/audit/admin` | Administradores | Actas de todos los usuarios |

`ActivityLog` registra por separado los eventos de sesión (inicios, cierres,
creación de planes), consultables en `/admin/activities`.

## Recomendaciones de configuración

- Dé **Visualizador** por defecto; conceda edición solo cuando haga falta.
- Combine siempre rol + permiso de fila para las secretarías sectoriales: sin el
  permiso de fila, un *Editor de Ejecución* podría tocar los indicadores de
  cualquier otra dependencia.
- Reserve **Administrador** para dos o tres personas: salta las capas 2 y 3.
- Revise `/admin/sessions` con regularidad. Solo se admite una sesión activa por
  usuario, y las credenciales compartidas se detectan como cierres continuos.
