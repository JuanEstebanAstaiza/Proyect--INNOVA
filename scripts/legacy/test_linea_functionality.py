#!/usr/bin/env python3
"""
Script para probar las funcionalidades de edición y detalles de líneas estratégicas
"""

import requests
import json

def test_linea_functionality():
    """Prueba las funcionalidades de líneas estratégicas"""

    base_url = "http://localhost:5000"

    print("🧪 PRUEBA DE FUNCIONALIDADES DE LÍNEAS ESTRATÉGICAS")
    print("=" * 60)

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

    # Paso 2: Acceder al dashboard
    print("\n2️⃣ Accediendo al dashboard...")
    try:
        response = session.get(f"{base_url}/dashboard")
        if response.status_code == 200:
            print("✅ Dashboard accesible")
        else:
            print(f"❌ Error en dashboard: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    # Paso 3: Buscar planes disponibles
    print("\n3️⃣ Buscando planes disponibles...")
    try:
        response = session.get(f"{base_url}/planes")
        if response.status_code == 200:
            print("✅ Lista de planes accesible")
        else:
            print(f"❌ Error en lista de planes: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    # Paso 4: Intentar acceder a líneas estratégicas (simulando navegación)
    print("\n4️⃣ Verificando navegación a líneas estratégicas...")
    print("   Para completar esta prueba:")
    print("   1. Ve a http://localhost:5000")
    print("   2. Inicia sesión con admin/admin123")
    print("   3. Ve al Dashboard")
    print("   4. Selecciona un plan de desarrollo")
    print("   5. Haz clic en 'Líneas Estratégicas'")
    print("   6. Verifica que aparecen las líneas")
    print("   7. Haz clic en 'Detalles' de una línea")
    print("   8. Haz clic en 'Editar' de una línea")
    print("   9. Verifica que los formularios funcionan")

    print("\n📝 INSTRUCCIONES PARA PRUEBA MANUAL:")
    print("=" * 50)
    print("🔗 URL: http://localhost:5000")
    print("👤 Usuario: admin")
    print("🔑 Contraseña: admin123")
    print("")
    print("✅ FUNCIONALIDADES A PROBAR:")
    print("   • Acceso a líneas estratégicas")
    print("   • Visualización de detalles")
    print("   • Edición de líneas estratégicas")
    print("   • Navegación entre vistas")
    print("   • Validación de formularios")
    print("")
    print("🎯 RUTAS A VERIFICAR:")
    print(f"   • {base_url}/planes/[plan_id]/lineas")
    print(f"   • {base_url}/planes/lineas/[linea_id]/detalles")
    print(f"   • {base_url}/planes/lineas/[linea_id]/editar")

if __name__ == '__main__':
    test_linea_functionality()
