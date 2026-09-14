# Proyecto INNOVA

Sistema web para la formulación y el seguimiento del **Plan de Desarrollo** de
alcaldías y gobernaciones de Colombia (PDM / PDD).

Hoy, la mayoría de entidades territoriales gestionan su plan en un único archivo
de Excel que circula por correo entre secretarías. Ese archivo tiene una fila por
indicador de producto y unas 37 columnas que recorren toda la cadena de valor,
desde la línea estratégica hasta la ejecución de cada trimestre. El archivo
`plantilla_plan.xlsx` de este repositorio es esa matriz, y
`Diccionario_de_datos.txt` describe el tipo de dato de cada columna.

INNOVA conserva esa matriz —los funcionarios la siguen viendo y editando como
una hoja de cálculo— pero la respalda con una base de datos relacional, control
de acceso por columna y por fila, y una pista de auditoría de cada cambio.

## Qué resuelve

| Problema del Excel compartido | Respuesta de INNOVA |
|---|---|
| Cualquiera puede modificar cualquier celda | Permisos por **columna** (rol) y por **fila** (entidad concreta) |
| No se sabe quién cambió qué ni por qué | Cada edición exige justificación y genera un **acta PDF de auditoría** |
| Versiones divergentes por correo | Una sola base de datos, con importación y exportación a Excel |
| Sin trazabilidad de la ejecución | Seguimiento trimestral con cálculo automático de cumplimiento |
| Sin control de sesiones | Sesiones con JWT, una sesión activa por usuario, panel de sesiones |

## Documentación

| Documento | Contenido |
|---|---|
| [docs/DOCKER.md](docs/DOCKER.md) | Arrancar con Docker, usuarios de prueba y guion de pruebas |
| [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) | Estructura del código, blueprints, flujo de una petición |
| [docs/MODELO_DATOS.md](docs/MODELO_DATOS.md) | Jerarquía del plan, tablas y correspondencia con la matriz Excel |
| [docs/PERMISOS.md](docs/PERMISOS.md) | Roles, permisos de columna, permisos de fila y auditoría |
| [docs/INTERFAZ.md](docs/INTERFAZ.md) | Sistema de diseño: paleta, tipografía, componentes y accesibilidad |
| [docs/DESPLIEGUE.md](docs/DESPLIEGUE.md) | Puesta en producción con Nginx/Apache, respaldos y seguridad |
| [docs/CORRECCIONES.md](docs/CORRECCIONES.md) | Errores corregidos en la revisión de septiembre de 2026 |

## Arranque rápido con Docker

Si solo quiere ver el sistema funcionando, es el camino corto: no hace falta
instalar Python ni dependencias.

```bash
docker compose up -d --build
```

En un par de minutos, <http://localhost:8000> con un plan de demostración de
unos 200 indicadores y tres usuarios listos:

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin123` | Administrador |
| `editor` | `editor123` | Editor General |
| `viewer` | `viewer123` | Visualizador |

Guía completa y qué probar: [docs/DOCKER.md](docs/DOCKER.md).

---

## Instalación local

## Requisitos

- Python 3.11 o superior (probado hasta 3.14)
- SQLite (incluido con Python); PostgreSQL y MySQL funcionan cambiando `DATABASE_URL`

Antes de ejecutar `flask ...` conviene exportar la variable de la aplicación:

```bash
# Linux / macOS
export FLASK_APP=run.py
# Windows PowerShell
$env:FLASK_APP = "run.py"
```

## Instalación

```bash
git clone <url-del-repositorio>
cd Proyect--INNOVA

# 1. Entorno virtual
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# 2. Dependencias
pip install -r requirements.txt

# 3. Configuración
cp .env.example .env      # Windows: copy .env.example .env
#    Edite .env y ponga un SECRET_KEY propio antes de usarlo en serio.

# 4. Crear el esquema de la base de datos
flask db upgrade

# 5. (Opcional) Cargar datos de ejemplo para probar el sistema
python scripts/init_db.py

# 6. Arrancar
python run.py
```

> El esquema **no** se crea al arrancar la aplicación: hay que pedirlo con
> `flask db upgrade` (o `flask init-db`). Así una migración nunca se encuentra
> las tablas ya creadas por su cuenta.

La aplicación queda en <http://127.0.0.1:5000>.

### Usuarios de ejemplo

`scripts/init_db.py` crea tres usuarios de demostración:

| Usuario  | Contraseña  | Rol asignado   | Puede |
|----------|-------------|----------------|-------|
| `admin`  | `admin123`  | Administrador  | Todo, incluido `/admin` |
| `editor` | `editor123` | Editor General | Editar el plan, no gestionar usuarios |
| `viewer` | `viewer123` | Visualizador   | Solo consultar |

> **Cámbielas antes de exponer el sistema.** Son credenciales públicas de
> demostración. Para una instalación real, use
> `python scripts/limpiar_db_para_produccion.py`, que vacía los datos de prueba.

### Base de datos vacía (sin datos de ejemplo)

```bash
flask db upgrade    # crea las tablas
flask crear-roles   # siembra los 5 roles por defecto
```

El registro público (`/auth/register`) crea siempre usuarios con rol
`Visualizador`, así que el primer administrador se designa desde consola:

```bash
python scripts/crear_admin.py                 # crea uno nuevo, preguntando los datos
python scripts/crear_admin.py --usuario juan  # eleva a un usuario ya registrado
```

## Variables de entorno

Se leen de `.env` (ver `.env.example`).

| Variable | Por defecto | Descripción |
|---|---|---|
| `FLASK_ENV` | `development` | `development`, `production` o `testing` |
| `SECRET_KEY` | clave de desarrollo | Firma las cookies de sesión. **Obligatorio cambiarla** |
| `JWT_SECRET_KEY` | clave de desarrollo | Firma los JWT de sesión. **Obligatorio cambiarla** |
| `DATABASE_URL` | `sqlite:///alcaldias_dev.db` | Cadena de conexión SQLAlchemy |
| `HOST` | `127.0.0.1` | Interfaz de escucha en desarrollo |
| `PORT` | `5000` | Puerto |
| `FLASK_DEBUG` | `True` | Depurador de Werkzeug. **`False` en producción** |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD` | — | SMTP global; cada municipio puede tener el suyo desde `/admin/smtp-config` |

> `run.py` escucha en `127.0.0.1` de forma deliberada. Con `FLASK_DEBUG=True`,
> exponer el depurador de Werkzeug en `0.0.0.0` permite ejecutar código
> arbitrario desde la red. Para producción, ver [docs/DESPLIEGUE.md](docs/DESPLIEGUE.md).

## Uso

### Vista Excel

`/planes/<id>/excel` es la pantalla principal de trabajo: reproduce la matriz de
37 columnas del plan. Al hacer doble clic sobre una celda editable se abre un
cuadro que exige una **justificación** del cambio y admite adjuntar un archivo de
soporte. Cada edición confirmada:

1. actualiza el dato en la base,
2. guarda un registro `EditJustification` con valor anterior y nuevo,
3. genera un **acta PDF con marca de agua** en `audit_files/user_<id>/`.

Las columnas que el rol del usuario no puede editar aparecen bloqueadas.

### Importar y exportar

- **Exportar**: `/planes/<id>/exportar-excel` descarga la matriz completa en `.xlsx`.
- **Importar**: desde la vista Excel, campo `excel_file`. Se admiten `.xlsx` y `.xls`
  y se espera la estructura de columnas de `plantilla_plan.xlsx`.

### Jerarquía del plan

```
Plan de Desarrollo
└── Línea Estratégica      (CÓD LINEA)
    └── Componente         (CÓD COMPONENTE)
        └── Programa PDM   (CÓD PROGRAMA)
            └── Proyecto   (NOMBRE PROYECTO / BPIM)
                └── Indicador de Producto
                    └── Ejecución Trimestral (I a IV)
```

Cada nivel se crea desde su pantalla (`/planes/<id>/lineas`,
`/planes/lineas/<id>/componentes`, y así sucesivamente) y admite documentos anexos.

### Quién ve qué

Un plan pertenece al **municipio**, no a la persona que lo creó: todos los
funcionarios de la misma alcaldía (mismo municipio y departamento) ven y
comparten el mismo plan, y ninguno ve el de otra entidad territorial. Lo que
cambia según el rol es qué puede **editar**, no qué puede ver.

### Administración

Bajo `/admin` (solo administradores):

- `/admin/users` — alta de usuarios, contraseña temporal y envío de credenciales
- `/admin/roles` — roles y permisos de columna
- `/admin/user-roles` — asignación de roles
- `/admin/row-permissions` — permisos sobre filas concretas
- `/admin/sessions` — sesiones activas, con cierre forzado
- `/admin/smtp-config` — configuración SMTP por municipio
- `/audit/admin` — actas de auditoría de todos los usuarios

## Comandos de `flask`

| Comando | Qué hace |
|---|---|
| `flask db upgrade` | Aplica las migraciones pendientes (crea o actualiza el esquema) |
| `flask db migrate -m "..."` | Genera una migración a partir de los cambios en los modelos |
| `flask init-db` | Crea las tablas que falten y siembra los roles (alternativa sin migraciones) |
| `flask crear-roles` | Siembra los roles por defecto si aún no existen |

## Scripts

Los scripts operativos están en `scripts/` y se ejecutan desde la raíz del proyecto:

| Script | Para qué sirve |
|---|---|
| `init_db.py` | Crea las tablas y carga datos de ejemplo |
| `crear_admin.py` | Crea el primer administrador o eleva a uno existente |
| `init_roles.py` | Siembra o repara los roles por defecto y los asigna según el rol legacy |
| `migrate_permissions.py` | Migra al sistema de permisos por columna |
| `migrate_jwt_sessions.py` | Migra las sesiones al esquema con JWT |
| `create_new_tables.py`, `create_row_permissions_table.py` | Crean tablas añadidas después del despliegue inicial |
| `clean_sessions.py` | Limpia sesiones caducadas |
| `limpiar_db_para_produccion.py` | Borra datos de prueba y deja la base lista para producción |
| `generate_synthetic_data.py` | Genera un plan sintético completo para demostraciones |
| `update_plan_data.py` | Carga masiva de datos de un plan |

`scripts/legacy/` contiene 96 scripts de depuración de la etapa de desarrollo.
**No están mantenidos y muchos no funcionan**; se conservan solo como referencia.

## Estructura del proyecto

```
Proyect--INNOVA/
├── app/
│   ├── __init__.py          # create_app(), comandos flask y siembra de roles
│   ├── models/              # 19 modelos SQLAlchemy
│   ├── views/               # blueprints: auth, main, planes, admin, audit
│   ├── services/            # lógica de la matriz y de la edición de celdas
│   ├── forms/               # formularios WTForms
│   ├── utils/               # JWT, correo y fechas
│   ├── templates/           # 58 plantillas Jinja2 (Bootstrap 5)
│   └── static/              # CSS y JavaScript
├── tests/                   # suite de pruebas (pytest)
├── migrations/              # migraciones de esquema (Alembic)
├── docs/                    # documentación (ver tabla arriba)
├── scripts/                 # scripts operativos
│   └── legacy/              # artefactos de desarrollo, sin mantenimiento
├── audit_file_system.py     # escritura de actas de auditoría
├── audit_pdf_generator.py   # generación de PDF con marca de agua
├── config.py                # configuración por entorno
├── Dockerfile               # imagen de la aplicación
├── docker-compose.yml       # orquestación (app + volúmenes de datos)
├── docker/entrypoint.sh     # migra, siembra y arranca el servidor
├── pyproject.toml           # configuración de pytest y ruff
├── run.py                   # arranque en desarrollo
├── wsgi.py                  # punto de entrada WSGI
├── plantilla_plan.xlsx      # matriz de referencia del plan
└── Diccionario_de_datos.txt # tipos de dato de las 37 columnas
```

## Pruebas

El proyecto trae una suite con **119 pruebas** que cubre el arranque, la
autenticación, las 99 rutas, los permisos, el aislamiento entre municipios y
todo el flujo de la matriz Excel:

```bash
pytest                 # toda la suite (~4 s)
pytest tests/test_excel.py -v   # solo un archivo
pytest --cov=app       # con informe de cobertura
```

Las pruebas trabajan contra una base SQLite temporal: **nunca** tocan
`instance/alcaldias_dev.db`.

### Estilo de código

```bash
ruff check .           # revisa
ruff check . --fix     # corrige lo automatizable
```

La configuración de ambas herramientas está en `pyproject.toml`.

## Licencia

GNU General Public License v3.0 o posterior. El texto completo está en
[LICENSE](LICENSE).

En la práctica: cualquier entidad puede usar, estudiar y adaptar el sistema,
pero quien distribuya una versión modificada debe publicar también su código
fuente bajo la misma licencia. Así las mejoras que haga una alcaldía quedan
disponibles para las demás.
