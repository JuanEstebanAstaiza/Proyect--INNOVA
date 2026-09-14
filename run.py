#!/usr/bin/env python3
"""Punto de entrada para ejecutar el Proyecto INNOVA en desarrollo.

Uso:
    python run.py

Variables de entorno relevantes (ver .env.example):
    FLASK_ENV    development | production | testing   (por defecto: development)
    PORT         puerto de escucha                    (por defecto: 5000)
    HOST         interfaz de escucha                  (por defecto: 127.0.0.1)
    FLASK_DEBUG  True | False                         (por defecto: True)
    LOG_LEVEL    DEBUG | INFO | WARNING | ERROR       (por defecto: INFO)
"""

import logging
import os
import sys


def _force_utf8_output():
    """Fuerza UTF-8 en la salida estándar.

    La consola de Windows usa cp1252 por defecto y no puede representar los
    acentos del castellano ni los símbolos que emite la aplicación, lo que
    aborta la petición en curso con UnicodeEncodeError.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, 'reconfigure', None)
        if reconfigure is not None:
            reconfigure(encoding='utf-8', errors='replace')


_force_utf8_output()

logging.basicConfig(
    level=getattr(logging, os.environ.get('LOG_LEVEL', 'INFO').upper(), logging.INFO),
    format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
)

from app import create_app  # noqa: E402  (después de configurar el logging)

app = create_app()

if __name__ == '__main__':
    app.run(
        host=os.environ.get('HOST', '127.0.0.1'),
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', 'True').lower() == 'true',
    )
