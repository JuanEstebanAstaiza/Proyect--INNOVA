#!/usr/bin/env python3
"""
Archivo principal para ejecutar la aplicación Proyecto INNOVA
"""

import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Configuración para desarrollo
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    )
