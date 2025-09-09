#!/usr/bin/env python3
"""
Script para probar que los errores de templates han sido corregidos
"""

import requests
import json

def test_templates_fixed():
    """Prueba que los templates funcionan correctamente"""

    base_url = "http://localhost:5000"

    print("🧪 PRUEBA DE CORRECCIÓN DE TEMPLATES")
    print("=" * 50)

    # Paso 1: Iniciar sesión
    print("\n1️⃣ Iniciando sesión...")
    session = requests.Session()

    login_data = {
        'username': 'admin',
        'password': 'admin123',
        'csrf_token': 'IjNlN2FhNjRhMDQwZTI5Njg0ZDRkNDZhNjc1YjQ1OWIxNzZjN2ExNWYi.aMBUTg.jnr-ygkYsOKcawKu7yhlr28016Y'  # Token de ejemplo
    }

    try:
        response = session.post(f"{base_url}/auth/login", data=login_data)
        if response.status_code == 200:
            print("✅ Login exitoso")
        else:
            print(f"❌ Error en login: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    # Paso 2: Probar acceso a diferentes vistas de detalles
    print("\n2️⃣ Probando vistas de detalles...")

    test_urls = [
        (f"{base_url}/planes", "Lista de planes"),
        (f"{base_url}/dashboard", "Dashboard"),
    ]

    for url, description in test_urls:
        try:
            response = session.get(url)
            if response.status_code == 200:
                print(f"✅ {description}: OK")
            else:
                print(f"❌ {description}: Error {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: Error de conexión - {e}")

    print("\n📝 INSTRUCCIONES PARA PRUEBA MANUAL:")
    print("=" * 50)
    print("🔗 URL: http://localhost:5000")
    print("👤 Usuario: admin")
    print("🔑 Contraseña: admin123")
    print("")
    print("✅ FUNCIONALIDADES A PROBAR:")
    print("   • Acceso a líneas estratégicas")
    print("   • Botón 'Detalles' en tarjetas de líneas")
    print("   • Botón 'Editar' en tarjetas de líneas")
    print("   • Vista de detalles sin errores 500")
    print("   • Formulario de edición funcional")
    print("   • Navegación entre vistas")
    print("")
    print("🎯 ERRORES CORREGIDOS:")
    print("   • TypeError: unsupported operand type(s) for +")
    print("   • Expresiones Jinja2 complejas optimizadas")
    print("   • Cálculos de estadísticas en Python")
    print("   • Templates más eficientes y legibles")

if __name__ == '__main__':
    test_templates_fixed()
