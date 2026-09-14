# Despliegue en producción

## Antes de exponer el sistema

Lista de comprobación obligatoria:

- [ ] `SECRET_KEY` y `JWT_SECRET_KEY` propios y aleatorios en `.env`
- [ ] `FLASK_ENV=production` y `FLASK_DEBUG=False`
- [ ] Contraseñas de demostración (`admin123`, `editor123`, `viewer123`) cambiadas o los usuarios eliminados
- [ ] `.env` **fuera** del control de versiones (ya está en `.gitignore`)
- [ ] HTTPS configurado: `ProductionConfig` marca las cookies como `Secure` y sin él no habrá sesión
- [ ] Copia de seguridad de la base de datos programada
- [ ] `audit_files/` y `uploads/` incluidos en la copia de seguridad
- [ ] `pytest` en verde sobre el servidor antes de abrir el acceso

Genere claves con:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Nunca use `run.py` en producción

`run.py` levanta el servidor de desarrollo de Werkzeug: un solo proceso, sin
concurrencia real y sin endurecimiento. Use un servidor WSGI que cargue
`wsgi.py`, que expone `application`.

### Linux — Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 127.0.0.1:8000 --timeout 120 wsgi:application
```

Servicio systemd (`/etc/systemd/system/innova.service`):

```ini
[Unit]
Description=Proyecto INNOVA
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/innova
Environment="PATH=/var/www/innova/.venv/bin"
EnvironmentFile=/var/www/innova/.env
ExecStart=/var/www/innova/.venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 --timeout 120 wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now innova
sudo systemctl status innova
```

### Windows — Waitress

Gunicorn no funciona en Windows. Use Waitress:

```powershell
pip install waitress
waitress-serve --listen=127.0.0.1:8000 wsgi:application
```

Para que arranque solo, registre el comando como servicio con NSSM o mediante el
Programador de tareas con disparador «al iniciar el sistema».

## Servidor web delantero

El repositorio incluye `nginx.conf` y `apache.conf` como punto de partida.
Ambos asumen el dominio `alcaldias.midominio.com` y una aplicación escuchando en
el puerto 8000: **cambie el dominio y las rutas** antes de usarlos.

### Nginx

```nginx
location /static {
    alias /var/www/innova/app/static;
    expires 30d;
}

location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host              $host;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

client_max_body_size 50M;   # debe coincidir con MAX_CONTENT_LENGTH
```

`client_max_body_size` es importante: la aplicación admite anexos de hasta
50 MB y Nginx rechaza 1 MB por defecto.

Para el certificado TLS, lo más simple es Certbot:

```bash
sudo certbot --nginx -d alcaldias.midominio.com
```

### Detrás de un proxy

Si el proxy termina el TLS, la aplicación necesita saberlo para generar URLs
`https` correctas. Añada al final de `wsgi.py`:

```python
from werkzeug.middleware.proxy_fix import ProxyFix
application.wsgi_app = ProxyFix(application.wsgi_app, x_for=1, x_proto=1, x_host=1)
```

## Base de datos

SQLite basta para una alcaldía: un plan ronda unos pocos miles de indicadores y
los usuarios concurrentes son decenas, no miles. Sus límites aparecen con
escritura concurrente intensa.

Para una gobernación con varios municipios, o si prevé muchos editores
simultáneos, migre a PostgreSQL:

```bash
pip install psycopg2-binary
```

```env
DATABASE_URL=postgresql://usuario:contrasena@localhost:5432/innova
```

### Esquema y migraciones

El esquema está bajo control de Alembic (Flask-Migrate). En un servidor nuevo:

```bash
export FLASK_APP=run.py
flask db upgrade          # crea todas las tablas
flask crear-roles         # siembra los 5 roles por defecto
python scripts/crear_admin.py   # designa el primer administrador
```

Si viene de una instalación anterior a las migraciones, cuya base se creó con
`create_all()`, regístrela una sola vez antes de nada:

```bash
flask db stamp head       # marca la versión actual sin recrear tablas
```

A partir de ahí, cada actualización del sistema se aplica con `flask db upgrade`.

### Copias de seguridad

Con SQLite, use el comando `.backup`, que es seguro con la base en uso:

```bash
sqlite3 instance/alcaldias.db ".backup '/respaldos/innova_$(date +%F).db'"
```

Respalde también `audit_files/` y `uploads/`: contienen las actas de auditoría y
los documentos de soporte, que no están en la base de datos.

## Permisos de archivos (Linux)

```bash
sudo chown -R www-data:www-data /var/www/innova
sudo chmod 640 /var/www/innova/.env
sudo chmod -R 750 /var/www/innova/audit_files /var/www/innova/uploads /var/www/innova/instance
```

`.env` contiene la clave secreta y las credenciales SMTP: no debe ser legible
por todos.

## Registro de eventos

`run.py` configura `logging` según `LOG_LEVEL`. Bajo Gunicorn, la salida va a
los registros del servicio:

```bash
journalctl -u innova -f
```

Para archivo propio, añada a `wsgi.py` un `RotatingFileHandler` sobre
`application.logger`.

## Actualización

```bash
sudo systemctl stop innova
cd /var/www/innova
sqlite3 instance/alcaldias.db ".backup '/respaldos/pre_actualizacion.db'"
git pull
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=run.py
flask db upgrade          # aplica los cambios de esquema
pytest                    # comprueba que la instalación sigue sana
sudo systemctl start innova
```

`flask db upgrade` aplica tanto las tablas nuevas como los cambios sobre
columnas existentes. Si algo sale mal, `flask db downgrade` revierte la última
migración y el respaldo previo sigue disponible.

## Notas de seguridad

- La protección CSRF está activa en toda la aplicación (`CSRFProtect`). Los
  endpoints JSON de la vista Excel esperan el token en el formulario.
- Las contraseñas se guardan con el hash de Werkzeug (`generate_password_hash`).
- Solo se admite **una sesión activa por usuario**; al iniciar sesión se
  invalidan las anteriores.
- Los anexos se guardan con nombre saneado (`secure_filename`) fuera de las
  rutas servidas directamente por Nginx, y se descargan a través de una vista
  que comprueba permisos.
- La lista blanca de extensiones está en `Config.ALLOWED_EXTENSIONS`.
