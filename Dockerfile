# Proyecto INNOVA — imagen de la aplicación
#
# Construir:  docker compose build
# Arrancar :  docker compose up

FROM python:3.13-slim

# ---------------------------------------------------------------------------
# Entorno
# ---------------------------------------------------------------------------
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # La aplicación escribe en castellano: sin UTF-8 los acentos rompen la salida.
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    FLASK_APP=run.py \
    FLASK_ENV=production

WORKDIR /app

# ---------------------------------------------------------------------------
# Dependencias del sistema
#   curl   -> healthcheck de docker compose
#   sqlite3 -> respaldos con el comando .backup
# ---------------------------------------------------------------------------
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Dependencias de Python (capa aparte para aprovechar la caché de Docker)
# ---------------------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    # gunicorn sirve la aplicación; faker solo lo necesita el generador del
    # plan de demostración (scripts/generate_synthetic_data.py).
    && pip install --no-cache-dir "gunicorn==23.0.0" "faker==38.2.0"

# ---------------------------------------------------------------------------
# Código de la aplicación
# ---------------------------------------------------------------------------
COPY . .

COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# ---------------------------------------------------------------------------
# Usuario sin privilegios
# ---------------------------------------------------------------------------
RUN useradd --create-home --uid 1000 innova \
    && mkdir -p /app/instance /app/uploads /app/audit_files \
    && chown -R innova:innova /app

USER innova

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", \
     "--access-logfile", "-", "--error-logfile", "-", "wsgi:application"]
