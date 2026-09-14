# Arquitectura

## Panorama

INNOVA es una aplicación Flask monolítica con renderizado en el servidor
(Jinja2 + Bootstrap 5) y unos pocos endpoints JSON para la parte interactiva de
la vista Excel. No hay framework de frontend ni proceso de compilación: se sirve
HTML y JavaScript plano.

```
Navegador
   │  HTML (Jinja2) + fetch() a los endpoints JSON
   ▼
Flask  ──►  Blueprints (auth, main, planes, admin, audit)
   │            │
   │            ├──► Servicios de dominio     (app/services/)
   │            ├──► Formularios WTForms      (app/forms/)
   │            ├──► Modelos SQLAlchemy       (app/models/)
   │            └──► Utilidades JWT y correo  (app/utils/)
   ▼
SQLite / PostgreSQL          audit_files/    uploads/
(datos del plan)             (actas PDF)     (documentos anexos)
```

## Fábrica de la aplicación

`app/__init__.py` expone `create_app(config_name)`. En orden:

1. Carga `.env` con python-dotenv.
2. Aplica la clase de configuración de `config.py` según `FLASK_ENV`.
3. Crea los directorios `UPLOAD_FOLDER`, `AUDIT_FILES_PATH` e `instance/`.
4. Inicializa las extensiones: SQLAlchemy, Flask-Migrate, Flask-Login,
   CSRFProtect y Flask-Mail.
5. Registra los cinco blueprints.
6. Registra los comandos propios de `flask`.

**El esquema de la base NO se toca al arrancar.** Crearlo es un paso explícito
(`flask db upgrade`, o `flask init-db`). Si `create_all()` se ejecutara al
importar la aplicación, cualquier `flask db upgrade` se encontraría las tablas
ya creadas y fallaría.

`initialize_default_roles()` solo actúa si la tabla `roles` está vacía, así que
volver a ejecutarlo no duplica nada.

Puntos de entrada:

- `run.py` — desarrollo. Fuerza UTF-8 en la salida, configura `logging` y llama a `app.run()`.
- `wsgi.py` — producción. Expone `application` para Gunicorn, uWSGI o mod_wsgi.

## Servicios de dominio

`app/services/` contiene la lógica que no pertenece ni a un modelo concreto ni a
una vista, y que antes estaba duplicada dentro de `planes.py`:

| Módulo | Responsabilidad |
|---|---|
| `matriz_plan.py` | Recorre el plan y produce **una fila por indicador**. Lo usan la vista Excel y la exportación, que antes repetían el recorrido y perdían el 75 % del plan |
| `edicion_celda.py` | Traduce el nombre de columna de la plantilla al campo real del modelo, valida el dato y lo escribe. También traduce al encabezado del Excel para comprobar el permiso de columna |

Ambos son funciones puras sobre los modelos: se pueden probar sin levantar una
petición HTTP.

## Blueprints

| Blueprint | Prefijo | Archivo | Responsabilidad |
|---|---|---|---|
| `auth` | `/auth` | `app/views/auth.py` | Login, logout, registro. Crea la sesión con JWT |
| `main` | `/` | `app/views/main.py` | Dashboard, perfil, cambio de contraseña, latidos de actividad |
| `planes` | `/planes` | `app/views/planes.py` | Planes, jerarquía completa, vista Excel, import/export, documentos |
| `admin` | `/admin` | `app/views/admin.py` | Usuarios, roles, permisos, sesiones, SMTP |
| `audit` | `/audit` | `app/views/audit.py` | Consulta y descarga de actas de auditoría |

`planes.py` y `admin.py` (unas 1.700 líneas cada uno) concentran la mayor parte
de la lógica. La parte de la matriz salió ya a `app/services/`; el resto podría
separarse por área si el proyecto crece.

## Control de acceso

Dos mecanismos distintos:

- **`admin`** usa un guardia de blueprint. `require_admin()` está decorado con
  `@admin_bp.before_request` y `@login_required`, así que **todas** las rutas de
  `/admin` exigen sesión iniciada y `current_user.is_admin()`. Por eso las
  funciones individuales de `admin.py` no llevan decorador propio.
- **El resto** decora cada vista con `@login_required`.

Los permisos finos (columna y fila) se resuelven dentro de la vista, no en el
enrutador. Ver [PERMISOS.md](PERMISOS.md).

## Sesiones con JWT

Además de la cookie de sesión de Flask-Login, cada inicio de sesión crea un
registro `ActiveSession` con un JWT propio:

1. `auth.login` valida las credenciales.
2. `ActiveSession.create_session_with_jwt()` **invalida las sesiones anteriores
   del mismo usuario** y genera un `session_id` (UUID) más un JWT.
3. El JWT, el `session_id` y una huella del dispositivo quedan en `session`.

Consecuencia práctica: un usuario solo puede tener una sesión activa a la vez.
Un administrador puede cerrar sesiones ajenas desde `/admin/sessions`.

## Flujo de una edición en la vista Excel

Es el recorrido más característico del sistema:

```
Doble clic en una celda
   └─► el navegador abre el diálogo de edición (justificación obligatoria)
        └─► POST /planes/<id>/editar-celda-excel
             (column_name, new_value, justification, indicator_id, archivo opcional)
              │
              ├─ 1. Se comprueba que el indicador pertenece a ese plan
              ├─ 2. Se comprueba el permiso de columna del rol
              ├─ 3. Se lee el valor anterior
              ├─ 4. Se escribe el valor nuevo
              ├─ 5. Se guarda un EditJustification (antes, después, motivo, autor)
              └─ 6. audit_file_system.py genera el acta PDF con marca de agua
                    en audit_files/user_<id>/
```

Si falla la generación del PDF se escribe un `.txt` de respaldo con el mismo
contenido, de modo que la pista de auditoría nunca se pierde.

## Módulos de auditoría

Viven en la raíz, fuera del paquete `app`, porque también se usan desde scripts:

- `audit_file_system.py` — decide dónde y cómo se guarda cada acta; hace de
  fachada sobre el generador de PDF y ofrece el respaldo en texto plano.
- `audit_pdf_generator.py` — construye los PDF con ReportLab, incluida la marca
  de agua.

## Configuración

`config.py` define cuatro clases: `Config` (base), `DevelopmentConfig`,
`ProductionConfig` y `TestingConfig`, seleccionadas por el diccionario `config`.
`ProductionConfig` añade `SESSION_COOKIE_SECURE`, `REMEMBER_COOKIE_SECURE` y
`HTTPONLY`.

## Dependencias opcionales

`pandas`, `openpyxl` y `reportlab` se importan de forma perezosa dentro de las
funciones que los necesitan. Si faltan, la aplicación arranca igualmente y solo
se desactivan las funciones de Excel o de PDF, con un mensaje al usuario.

## Migraciones de esquema

El esquema está bajo control de **Alembic** a través de Flask-Migrate. Las
migraciones viven en `migrations/versions/`.

```bash
flask db upgrade                  # aplica lo pendiente
flask db migrate -m "descripción" # genera una migración desde los modelos
flask db current                  # versión aplicada
flask db downgrade                # revierte la última
```

Una base creada antes de adoptar migraciones se pone al día con
`flask db stamp head`, que registra la versión sin volver a crear nada.

## Pruebas

`tests/` contiene 119 pruebas con pytest. `conftest.py` levanta la aplicación
una sola vez por sesión contra una base SQLite **temporal** y siembra un plan
completo con un usuario por rol.

| Archivo | Cubre |
|---|---|
| `test_arranque.py` | Fábrica, blueprints, plantillas y roles por defecto |
| `test_auth.py` | Login, logout, sesión JWT y protección de rutas |
| `test_rutas.py` | Recorre todas las rutas GET buscando errores 500 |
| `test_permisos.py` | Roles, permisos de columna y de fila |
| `test_visibilidad.py` | Aislamiento entre municipios |
| `test_excel.py` | Matriz, exportación, importación y edición con auditoría |
| `test_edicion_celda.py` | Traducción de columnas y escritura de celdas |
| `test_modelos.py` | Progreso, estado del plan y utilidades |

La suite falla ante cualquier aviso de obsolescencia (`DeprecationWarning`,
`LegacyAPIWarning`), para que el código no se quede atrás con Python o
SQLAlchemy.

## Limitaciones conocidas

- **Consultas N+1** en las vistas que recorren la jerarquía completa (la vista
  Excel y `/admin/user-roles`). Con planes de unos pocos miles de indicadores es
  asumible; por encima de eso conviene usar `joinedload`.
- `planes.py` (~1.700 líneas) y `admin.py` (~1.700) siguen siendo archivos
  grandes. Extraer los servicios fue el primer paso; el resto de la lógica de
  cada blueprint podría separarse por área.
- El seguimiento trimestral está fijado al año **2024**
  (`ANIO_SEGUIMIENTO` en `app/services/matriz_plan.py`), aunque el plan cubre
  el cuatrienio completo.
