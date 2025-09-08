#!/usr/bin/env python3
"""
Archivo WSGI para deployment en Apache/Nginx
"""

import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(__file__))

# Configurar variables de entorno
os.environ.setdefault('FLASK_ENV', 'production')

from app import create_app

# Crear aplicación
application = create_app('production')

if __name__ == '__main__':
    application.run()
