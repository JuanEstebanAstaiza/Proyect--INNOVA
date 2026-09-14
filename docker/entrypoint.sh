#!/bin/sh
# Prepara la base de datos antes de ceder el control al servidor.
#
# Es idempotente: se puede reiniciar el contenedor las veces que haga falta.
set -e

echo "[innova] Aplicando migraciones de esquema..."
flask db upgrade

echo "[innova] Verificando los roles por defecto..."
flask crear-roles

# Datos de demostración.
#   basico  -> 3 usuarios y un plan mínimo
#   completo -> además, un plan con ~240 indicadores y su ejecución trimestral
# Solo se cargan si la base está vacía: init_db.py no pisa datos existentes.
case "${INNOVA_DEMO_DATA}" in
    basico|completo|true)
        echo "[innova] Creando los usuarios y el plan de ejemplo..."
        python scripts/init_db.py
        ;;
esac

if [ "${INNOVA_DEMO_DATA}" = "completo" ]; then
    if [ -f /app/instance/.demo-completo ]; then
        echo "[innova] El plan completo de demostración ya estaba cargado."
    else
        echo "[innova] Generando el plan completo de demostración..."
        python scripts/generate_synthetic_data.py && touch /app/instance/.demo-completo
    fi
fi

echo "[innova] Listo. Arrancando el servidor."
exec "$@"
