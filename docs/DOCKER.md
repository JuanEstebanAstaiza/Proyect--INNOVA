# Ejecutar con Docker

La forma más rápida de tener el sistema funcionando, sin instalar Python ni
dependencias en la máquina.

## Requisitos

Docker Desktop (Windows/macOS) o Docker Engine con el plugin `compose` (Linux).

```bash
docker --version          # 20.10 o superior
docker compose version
```

## Arrancar

Desde la raíz del proyecto:

```bash
docker compose up -d --build
```

El primer arranque tarda unos dos minutos: construye la imagen, aplica las
migraciones, siembra los roles y genera el plan de demostración (unos 200
indicadores con su ejecución trimestral).

Cuando el contenedor aparezca como `healthy`, abra <http://localhost:8000>.

```bash
docker compose ps         # debe decir: Up (healthy)
docker compose logs -f    # seguir el arranque en directo
```

## Usuarios de prueba

Los crea `scripts/init_db.py` dentro del contenedor. Los tres pertenecen al
mismo municipio, así que **los tres ven el mismo plan**; lo que cambia es qué
pueden editar.

| Usuario  | Contraseña  | Rol            | Puede hacer |
|----------|-------------|----------------|-------------|
| `admin`  | `admin123`  | Administrador  | Todo: editar cualquier columna, gestionar usuarios y roles, ver la auditoría de todos |
| `editor` | `editor123` | Editor General | Editar el plan (33 de 37 columnas). **No** entra en `/admin` |
| `viewer` | `viewer123` | Visualizador   | Solo consultar. No puede editar ninguna celda |

> Son credenciales de demostración públicas. Para cualquier uso real, cámbielas
> y ponga `INNOVA_DEMO_DATA: "false"` en `docker-compose.yml`.

## Qué probar

### 1. La matriz del plan (lo característico del sistema)

Entre como **admin** → *Planes* → abra el plan → botón **Vista Excel**
(o vaya directo a <http://localhost:8000/planes/1/excel>).

Verá la matriz del PDM con sus 37 columnas y una fila por indicador de producto.

- **Doble clic** en una celda de ejecución (por ejemplo *EJECUCIÓN I TRIMESTRE*).
- Escriba un valor y **una justificación** (es obligatoria).
- Guarde. El sistema anota quién, cuándo, el valor anterior y el nuevo, y genera
  un **acta PDF con marca de agua**.

Pruebe también a escribir algo que no sea un número (`12,3O`): lo rechaza en vez
de guardar un cero.

### 2. Los permisos por rol

Cierre sesión y entre como **viewer**:

- Ve el mismo plan y la misma matriz.
- Al intentar editar una celda recibe *«Su rol no tiene permiso para editar la
  columna…»*.
- `http://localhost:8000/admin/dashboard` lo devuelve al inicio.

Entre como **editor**: sí puede editar metas y ejecución, pero tampoco entra
en `/admin`.

### 3. La pista de auditoría

Como cualquier usuario: <http://localhost:8000/audit/> muestra sus cambios y
`/audit/files` permite descargar las actas en PDF.

Como **admin**: <http://localhost:8000/audit/admin> muestra las de todos.

### 4. Importar y exportar

- **Exportar**: en la vista Excel, botón de exportar (o
  `/planes/1/exportar-excel`). Descarga la matriz completa en `.xlsx`.
- **Importar**: suba ese mismo archivo. Debe procesar todas las filas.

### 5. Administración

Como **admin**:

| Página | Qué muestra |
|---|---|
| `/admin/dashboard` | Estadísticas de usuarios y planes |
| `/admin/users` | Alta de usuarios y envío de credenciales |
| `/admin/roles` | Los 5 roles y sus permisos columna por columna |
| `/admin/user-roles` | Asignación de roles |
| `/admin/row-permissions` | Permisos sobre ramas concretas del plan |
| `/admin/sessions` | Sesiones activas (solo una por usuario) |

## Comandos habituales

```bash
docker compose logs -f              # ver los registros
docker compose restart              # reiniciar (los datos se conservan)
docker compose down                 # detener (los datos se conservan)
docker compose down -v              # detener y BORRAR los datos
docker compose exec innova sh       # abrir una consola dentro del contenedor
docker compose exec innova sh -c "pip install pytest && pytest"   # suite de pruebas
                                    # (la imagen no lleva pytest: es de ejecución)
```

## Configuración

Todo se ajusta en la sección `environment` de `docker-compose.yml`.

| Variable | Por defecto | Para qué |
|---|---|---|
| `INNOVA_DEMO_DATA` | `completo` | `completo` (usuarios + plan grande), `basico` (usuarios + plan mínimo) o `false` (nada) |
| `SESSION_COOKIE_SECURE` | `false` | **Póngalo en `true` en cuanto tenga HTTPS.** En `false` permite entrar por HTTP plano |
| `SECRET_KEY` | clave de demo | Firma las cookies. **Cámbiela** |
| `JWT_SECRET_KEY` | clave de demo | Firma los JWT de sesión. **Cámbiela** |
| `DATABASE_URL` | SQLite en el volumen | Cadena de conexión SQLAlchemy |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

Genere claves nuevas con:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Dónde viven los datos

Tres volúmenes de Docker, que sobreviven a `docker compose down`:

| Volumen | Montado en | Contenido |
|---|---|---|
| `datos` | `/app/instance` | La base de datos SQLite |
| `anexos` | `/app/uploads` | Documentos adjuntos |
| `auditoria` | `/app/audit_files` | Actas de auditoría en PDF |

Copia de seguridad de la base:

```bash
docker compose exec innova sqlite3 /app/instance/innova.db ".backup '/tmp/copia.db'"
docker compose cp innova:/tmp/copia.db ./copia-$(date +%F).db
```

Respalde también los anexos y las actas:

```bash
docker compose cp innova:/app/audit_files ./respaldo-auditoria
docker compose cp innova:/app/uploads ./respaldo-anexos
```

## Empezar de cero

```bash
docker compose down -v      # borra los tres volúmenes
docker compose up -d --build
```

## Antes de usarlo en serio

El `docker-compose.yml` está pensado para probar. Para una instalación real:

1. `SECRET_KEY` y `JWT_SECRET_KEY` propios y aleatorios.
2. `INNOVA_DEMO_DATA: "false"` y borre los usuarios de demostración.
3. HTTPS delante (Nginx o Traefik) y `SESSION_COOKIE_SECURE: "true"`.
4. No publique el puerto 8000 al exterior: déjelo tras el proxy.
5. Copias de seguridad programadas de los tres volúmenes.

Ver [DESPLIEGUE.md](DESPLIEGUE.md) para el detalle.

## Si algo falla

**El contenedor no llega a `healthy`**

```bash
docker compose logs --tail=50
```

El arranque imprime cada paso con el prefijo `[innova]`.

**No puedo iniciar sesión**

Casi siempre es `SESSION_COOKIE_SECURE`. Si está en `true` y entra por HTTP
plano, el navegador no devuelve la cookie de sesión y el login falla en
silencio. Póngalo en `false` para pruebas por HTTP.

**El puerto 8000 está ocupado**

Cambie la publicación en `docker-compose.yml`:

```yaml
ports:
  - "9000:8000"     # ahora en http://localhost:9000
```

**Quiero volver a generar el plan de demostración**

```bash
docker compose exec innova rm -f /app/instance/.demo-completo
docker compose exec innova python scripts/generate_synthetic_data.py
```
