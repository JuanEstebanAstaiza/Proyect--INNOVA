# Correcciones — revisión de septiembre de 2026

Registro de los defectos encontrados al poner el repositorio en marcha y de cómo
se resolvieron. Se ordenan de mayor a menor impacto.

## Bloqueantes

### 1. Una instalación nueva no creaba ningún rol

`app/models/role.py` usaba `ColumnPermission` sin importarlo. Al construir el
primer `Role`, `_create_default_column_permissions()` lanzaba
`NameError: name 'ColumnPermission' is not defined`. El error quedaba atrapado
por un `try/except` en la siembra, así que la aplicación arrancaba **sin roles y
sin permisos de columna**: nadie salvo un administrador legacy podía editar nada.

La base de datos del repositorio tenía roles porque en su momento se ejecutó
`migrate_permissions.py` a mano, lo que ocultaba el fallo.

*Corregido*: se añadió `from .column_permission import ColumnPermission`.
Verificado creando una base desde cero: los 5 roles se siembran con sus 37
columnas cada uno.

### 2. Los emojis de `print()` rompían la aplicación en Windows

La consola de Windows usa cp1252, que no puede representar `✅`, `❌` ni `→`.
Cualquier `print()` con esos caracteres abortaba la petición con
`UnicodeEncodeError`. Efectos medidos:

- `create_app()` fallaba al arrancar (`python run.py` no llegaba a servir).
- `/audit/summary` devolvía 500.
- **Las actas de auditoría no se escribían**: se perdía la trazabilidad.

*Corregido*: se sustituyeron los emojis por etiquetas ASCII (`[OK]`, `[ERROR]`)
en los módulos de la aplicación, `app/__init__.py` pasó a usar `logging` en vez
de `print`, y `run.py` fuerza UTF-8 en la salida.

### 3. Los roles de sistema se quedaban sin permisos de columna

`Role.__init__` solo creaba las 37 filas de permisos `if not self.is_system_role`.
Como *Editor General* y *Visualizador* son roles de sistema y resuelven sus
permisos a través de esas filas, quedaban con cero: un Editor General no podía
editar ninguna columna.

*Corregido*: todos los roles reciben el juego completo de columnas al crearse.

### 4. Plantilla rota: `/admin/users/<id>/temp-password` daba 500

`app/templates/admin/user_temp_password.html` cerraba un `{% if %}` con
`{% endfor %}`. Jinja no compilaba la plantilla.

*Corregido*. Se compilaron después las 58 plantillas del proyecto: todas válidas.

### 5. Dependencias incompatibles

`requirements.txt` fijaba Flask 2.3.3, Werkzeug 2.3.7 y pandas 2.1.3, que no
instalan en Python 3.12+. Además el repositorio incluía un `.venv/Scripts/python.exe`
suelto y sin `pyvenv.cfg`, es decir, un entorno virtual inservible.

*Corregido*: versiones actualizadas y verificadas en Python 3.14 (Flask 3.1.3,
SQLAlchemy 2.0.52, pandas 3.0.5, reportlab 5.0.1). El binario suelto se eliminó.

## Pérdida de datos y fallos silenciosos

### 6. La vista Excel y la exportación ocultaban el 75 % del plan

Ambas tomaban `proyecto.indicadores[0]`, es decir, **solo el primer indicador de
cada proyecto**. En el plan de ejemplo, con 28 proyectos y 111 indicadores, se
mostraban 28 filas en vez de 111. Como la matriz del PDM lleva una fila por
indicador, la exportación entregaba un plan incompleto y la reimportación
propagaba la pérdida.

*Corregido*: ambos recorridos emiten una fila por indicador. Comprobado: la
exportación pasó de 29 a 112 filas (111 indicadores + encabezado) y la
importación procesa las 111.

### 7. Editar una celda decía «guardado» sin guardar nada

`/planes/<id>/editar-celda-excel` localizaba el indicador con
`filter_by(proyecto_id=<subconsulta>.c.id)`, comparando una columna con un objeto
de SQLAlchemy, dentro de un `except:` desnudo. Cuando no encontraba el indicador
—por ejemplo, si pertenecía a otro plan— registraba la justificación, no
modificaba el dato y respondía **`"Celda editada exitosamente"`**.

*Corregido*: la consulta une la jerarquía completa y exige
`LineaEstrategica.plan_id == plan_id`. Si el indicador no pertenece al plan, se
devuelve 404 en vez de fingir éxito. Verificado con ambos casos.

### 8. El panel de administración contaba 0 administradores

`User.query.filter_by(role='admin')` filtraba por `role`, que es una *propiedad
de Python*, no una columna. SQLAlchemy no da error: devuelve 0 filas.

*Corregido*: se filtra por `legacy_role`.

### 9. Faltaban dos tablas en la base de datos de desarrollo

`smtp_configs` y `user_temp_passwords` no existían, aunque el código las usa. Las
funciones de correo por municipio y contraseñas temporales habrían fallado.
`db.create_all()` las creó al arrancar. Ningún dato existente se modificó.

## Errores en tiempo de ejecución

### 10. Joins ambiguos entre `users` y las tablas de permisos

`user_roles` y `row_permissions` tienen **dos** claves foráneas hacia `users.id`
(`user_id` y `assigned_by`), así que un `.join()` sin condición explícita falla:

- `/admin/api/roles/stats` → 500 `AmbiguousForeignKeysError`
- `/admin/user-row-permissions` → excepción no controlada

*Corregido*: ambos joins declaran su condición (`UserRole.user_id == User.id`,
`RowPermission.user_id == User.id`).

### 11. `NameError` por nombres no importados

- `app/views/admin.py` usaba `current_app.logger` sin importar `current_app`;
  saltaba al fallar el envío de credenciales, ocultando el error real.
- `app/views/planes.py` llamaba a `obtener_datos_plan_completo()`, eliminada en el
  commit 62a0120.
- `app/__init__.py`: `_assign_roles_to_existing_users()` usaba `User` y `UserRole`,
  importados solo en el ámbito local de otra función.

*Corregido* los tres.

### 12. `PlanDesarrollo.get_progreso_general()` lanzaba `AttributeError`

Se apoyaba en `self.objetivos`, relación del modelo `Objetivo`, que no se exporta
en `app/models/__init__.py` y por tanto no se registra en SQLAlchemy.

*Corregido*: promedia el progreso de las líneas estratégicas, igual que hace
`LineaEstrategica.get_progreso_general()` con sus componentes.

### 13. Clave foránea inválida al sembrar roles

La asignación automática usaba `assigned_by=1` con el comentario «asumir que el
usuario 1 es el super admin». Si ese usuario no existe, la inserción viola la
clave foránea.

*Corregido*: se usa el primer usuario existente, o `NULL` si la tabla está vacía.

### 14. `scripts/init_db.py` fallaba a media ejecución

Tres problemas encadenados en el script que arranca una instalación nueva:

- `ActivityLog.log_activity()` recibía `user_id`, que no acepta (es un ayudante
  que lee `current_user`, inexistente fuera de una petición).
- `ActiveSession(...)` se construía sin `jwt_token`, obligatorio desde que se
  añadieron las sesiones con JWT.
- Los usuarios creados no quedaban enlazados con el sistema de roles, así que el
  usuario `editor` no podía editar ninguna columna.

*Corregido*: los registros de actividad se crean directamente, se eliminó la
sesión activa de ejemplo (las sesiones las crea el login) y el script llama al
nuevo `assign_default_roles_to_users()`. Verificado de extremo a extremo.

## Configuración y seguridad

### 15. El archivo `.env` no se leía nunca

`config.py` leía `os.environ`, pero nada cargaba `.env`, pese a que
`python-dotenv` estaba en las dependencias y existía `env_ejemplo.txt`. Toda la
configuración quedaba en sus valores por defecto, incluida la clave secreta de
desarrollo.

*Corregido*: `create_app()` carga `.env` antes de leer la configuración, y
`env_ejemplo.txt` se copió como `.env.example` (nombre convencional).

### 16. Servidor de desarrollo expuesto a la red con el depurador activo

`run.py` escuchaba en `0.0.0.0` con `debug=True` por defecto. El depurador de
Werkzeug permite ejecutar código arbitrario desde el navegador.

*Corregido*: por defecto `127.0.0.1`, configurable con `HOST`.

### 17. Categorías de columna mal asignadas

`ColumnPermission._assign_category()` buscaba `'poblacion'` y `'observacion'` sin
tilde, pero las columnas reales llevan `POBLACIÓN` y `OBSERVACIÓN`. Además
comprobaba `'trimestre'` antes, y esa palabra aparece en casi todas: las columnas
de población y observaciones acababan clasificadas como `ejecucion`, lo que
desordena la pantalla de edición de roles.

*Corregido*: se comprueban las variantes con y sin tilde, de la regla más
específica a la más general.

### 18. Directorios de trabajo inexistentes

`UPLOAD_FOLDER` y `AUDIT_FILES_PATH` se declaraban en `config.py` pero no se
creaban al arrancar.

*Corregido*: `create_app()` los crea junto con `instance/`.

## Higiene del repositorio

- **Sin `.gitignore`**: se añadió uno que cubre `__pycache__`, `.venv`, `.env`,
  `instance/`, `uploads/` y `audit_files/`.
- **`__pycache__` versionado**: 60 archivos `.pyc` (de Python 3.10 y 3.11)
  estaban en el repositorio. Se retiraron del control de versiones.
- **111 scripts sueltos en la raíz**: se reorganizaron en `scripts/` (10
  operativos, con un arranque que ajusta `sys.path`) y `scripts/legacy/` (96
  artefactos de depuración, sin mantenimiento). En la raíz quedan los 5 módulos
  que son parte de la aplicación.
- Se añadió `scripts/crear_admin.py`: el registro público crea usuarios
  `Visualizador`, así que no había forma documentada de designar el primer
  administrador.

## Cómo se verificó

- Las **99 rutas** recorridas con un cliente de prueba autenticado: 61 respuestas
  200, 5 redirecciones legítimas, 4 respuestas 4xx correctas (parámetros
  ausentes o entidades inexistentes), **0 errores 5xx y 0 excepciones**.
- Las **58 plantillas** Jinja compiladas sin error.
- Flujos de escritura probados de principio a fin: login real, vista Excel,
  exportación, edición de celda con auditoría, importación de ida y vuelta,
  creación de plan y cierre de sesión.
- Instalación **desde cero** con `scripts/init_db.py` y comprobación de que los
  tres usuarios de ejemplo obtienen los permisos de columna correctos.
- Aislamiento entre planes comprobado: editar un indicador ajeno devuelve 404.
- `pyflakes` sin hallazgos de nombres indefinidos.

---

# Segunda ronda — limpieza y endurecimiento

Con la aplicación ya funcionando se hizo una segunda pasada centrada en la
calidad del código. Lo primero fue escribir la suite de pruebas: sirvió de red
de seguridad para los refactors y, de paso, destapó varios defectos más.

## Defectos encontrados por las pruebas

### 19. La población impactada nunca se guardaba

Para saber a qué trimestre pertenecía una celda, el código hacía
`column_name.split('_')[1]`. Funciona con `ejecucion_2_trimestre`, pero en
`poblacion_impactada_2_trimestre` esa posición es `'impactada'`: la conversión a
entero fallaba, el trimestre quedaba en `None`, **no se escribía nada** y la
respuesta seguía diciendo «Celda editada exitosamente».

*Corregido*: el número se extrae con una expresión regular en
`app/services/edicion_celda.py`.

### 20. Un número mal escrito se guardaba como cero

Las conversiones estaban envueltas en `except:` desnudos que, ante cualquier
fallo, asignaban `0.0`. Si un funcionario escribía `1.5OO` (con letra O), la
meta pasaba a valer 0 sin ningún aviso.

*Corregido*: se lanza `ValorInvalido` y se responde 400 con el motivo. El dato
anterior no se toca.

### 21. La edición de celdas no comprobaba el permiso de columna

`/planes/<id>/editar-celda-excel` no consultaba `ColumnPermission` en ningún
momento: cualquier usuario con sesión podía editar cualquier columna de su plan,
sin importar su rol.

La causa de fondo es que los nombres no coincidían: la plantilla envía
`meta_2024` y los permisos guardan `META 2024`. Sin traducción, comprobar el
permiso habría bloqueado todo.

*Corregido*: `columna_de_la_matriz()` traduce entre ambos espacios de nombres y
`puede_editar()` autoriza. Un rol sin permiso recibe 403.

### 22. El Editor General sí podía editar la dependencia responsable

La regla excluía las columnas que contuvieran `'responsable'`, pero el
encabezado real del Excel dice `DEPENDENCIA RESPOSABLE`, sin la N. La errata
anulaba la regla.

*Corregido*: se comprueban ambas grafías.

### 23. `get_tamano_legible()` devolvía basura y corrompía el dato

El método devolvía la cadena literal `".1f"` en lugar del tamaño y, en cada
vuelta del bucle, hacía `self.tamano /= 1024.0`: **consultar** el tamaño de un
documento dividía el valor guardado en el modelo.

*Corregido*: se calcula sobre una variable local y se devuelve `'2.4 MB'`.

### 24. `/audit/summary` devolvía 500

El generador produce `resumen_auditoria.pdf`, pero la vista pedía siempre
`resumen_auditoria.txt`. Además el `abort(404)` quedaba atrapado por el
`except Exception` de la propia función y se convertía en un 500.

*Corregido*: se envía la ruta que devuelve el generador y el 404 se propaga.

### 25. Predicados que devolvían `None` en vez de `False`

`can_edit_row`, `can_view_row`, `can_edit_column` y `can_view_column` terminaban
en `return permission and permission.can_edit`, que devuelve `None` cuando no
hay permiso. Comparaciones como `if resultado is False` fallaban.

*Corregido*: los seis devuelven un booleano real.

## Aislamiento entre entidades territoriales

### 26. Cada quien veía lo que no debía

El modelo de visibilidad era incoherente en los dos extremos:

- administradores y editores consultaban los planes **de todos los municipios**,
  sin filtro alguno;
- un visualizador solo veía los planes de los que él mismo constaba como dueño.

En la práctica: si Planeación creaba el plan, Control Interno de la misma
alcaldía no veía nada, mientras que un editor de Palmira sí podía abrir el plan
de Cali. Además, `importar-excel` aceptaba cualquier `plan_id`, así que se podía
sobrescribir el plan de otra entidad.

*Corregido* (decisión del responsable del proyecto): un plan pertenece al
**municipio**, no a la persona. `PlanDesarrollo.filtro_visibilidad()` compara
municipio y departamento, y todas las consultas pasan por `visibles_para()`. Se
cerraron las fugas de `index`, `dashboard`, `get_plan_or_redirect`, `lineas`,
`importar-excel`, el panel de auditoría y las estadísticas de administración.
Hay 12 pruebas dedicadas a esto.

## Estructura del código

### 27. El recorrido de la matriz estaba duplicado

La vista Excel y la exportación repetían el mismo bucle de cinco niveles. Esa
duplicación fue la causa del defecto n.º 6: había que arreglarlo dos veces.

*Corregido*: `app/services/matriz_plan.py` concentra el recorrido y el cálculo
de acumulados; `app/services/edicion_celda.py` hace lo propio con la escritura
de celdas. `planes.py` pasó de 1.973 a 1.696 líneas y `editar_celda_excel` de
201 líneas muy anidadas a una función lineal con tres ayudantes.

### 28. Migraciones de esquema

No había forma controlada de cambiar el esquema: `db.create_all()` solo crea
tablas nuevas y nunca altera las existentes, así que los cambios se habían ido
resolviendo con scripts sueltos.

*Corregido*: se adoptó Flask-Migrate (Alembic) con una migración base que
reproduce el esquema completo. `create_all()` dejó de ejecutarse al arrancar la
aplicación —chocaba con `flask db upgrade`— y ahora el esquema se pide de forma
explícita con `flask db upgrade` o `flask init-db`.

### 29. Suite de pruebas

No existía ninguna. Se añadieron **119 pruebas** en `tests/`, con una base
SQLite temporal que nunca toca los datos reales. La suite falla ante cualquier
`DeprecationWarning` o `LegacyAPIWarning`, de modo que el código no se quedará
atrás con las versiones nuevas de Python o SQLAlchemy.

### 30. APIs obsoletas

- `datetime.utcnow()` (obsoleto desde Python 3.12) en 25 sitios. Se sustituyó
  por `app/utils/fechas.ahora_utc()`, que devuelve UTC **sin** zona horaria para
  seguir siendo comparable con lo ya almacenado.
- `Model.query.get()` y `Model.query.get_or_404()` (obsoletos en SQLAlchemy 2.0)
  en 30 sitios, sustituidos por `db.session.get()` y `db.get_or_404()`.

### 31. Estilo y errores latentes

`ruff` señalaba 312 problemas. Quedan **cero**: imports sin usar, `except`
desnudos, variables muertas, comparaciones `== True` en filtros de SQLAlchemy y
nombres ambiguos. Se documentaron con `per-file-ignores` los casos en que
atrapar `Exception` es correcto (borde de una vista, envío de correo), y en
todos ellos se comprobó que dejan traza en el log.

Cuatro `plan = get_plan_or_404(...)` aparecían como variables sin usar: **no**
eran código muerto, sino la comprobación de permisos. Se dejaron como llamada
explícita con un comentario, para que nadie las borre por descuido.

## Licencia

El repositorio se publica bajo **GPL v3.0 o posterior** (archivo `LICENSE`), a
elección del responsable del proyecto: las mejoras que haga cualquier entidad
sobre el sistema deben quedar disponibles para las demás.

## Verificación de esta ronda

- **119 pruebas** en verde en unos 4 segundos.
- `ruff check .` sin hallazgos.
- Sin avisos de obsolescencia, ni siquiera ejecutando con `-W error`.
- Los cuatro caminos de instalación probados de principio a fin:
  `flask db upgrade`, `flask init-db`, `python scripts/init_db.py` y
  `python scripts/crear_admin.py`.
- Servidor real arrancado y sirviendo páginas.

## Pendiente

- **Consultas N+1** en la vista Excel y en `/admin/user-roles`.
- `planes.py` y `admin.py` siguen rondando las 1.700 líneas cada uno.
- El seguimiento trimestral está fijado al año 2024 (`ANIO_SEGUIMIENTO`), aunque
  el plan cubre el cuatrienio completo.
- Los 96 scripts de `scripts/legacy/` siguen sin mantenimiento; se conservan
  solo como referencia.
- No hay integración continua: conviene ejecutar `pytest` y `ruff` en cada
  cambio.
