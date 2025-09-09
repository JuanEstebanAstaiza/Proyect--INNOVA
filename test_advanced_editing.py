#!/usr/bin/env python3
"""
Script para probar la funcionalidad de edición avanzada de celdas Excel
"""

import requests
import json

def test_advanced_editing():
    """Prueba la edición avanzada de celdas Excel"""

    base_url = "http://localhost:5000"

    print("🧪 PRUEBA DE EDICIÓN AVANZADA DE CELDAS EXCEL")
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

    # Paso 2: Acceder a la vista Excel
    print("\n2️⃣ Accediendo a vista Excel...")
    try:
        response = session.get(f"{base_url}/planes/1/excel")
        if response.status_code == 200:
            print("✅ Vista Excel accesible")

            # Verificar que contiene el modal de edición
            if 'editModal' in response.text:
                print("✅ Modal de edición presente")
            else:
                print("⚠️ Modal de edición no encontrado")

            # Verificar que contiene JavaScript de edición
            if 'abrirModalEdicion' in response.text:
                print("✅ JavaScript de edición presente")
            else:
                print("⚠️ JavaScript de edición no encontrado")

        else:
            print(f"❌ Error en vista Excel: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    print("\n📝 INSTRUCCIONES PARA PRUEBA MANUAL:")
    print("=" * 50)
    print("🔗 URL: http://localhost:5000")
    print("👤 Usuario: admin")
    print("🔑 Contraseña: admin123")
    print("")
    print("✅ FUNCIONALIDADES A PROBAR:")
    print("   • Acceder a la vista Excel de un plan")
    print("   • Hacer doble clic en una celda editable")
    print("   • Verificar que se abre el modal de edición")
    print("   • Completar el formulario con justificación")
    print("   • Subir un archivo de soporte (opcional)")
    print("   • Guardar los cambios")
    print("   • Verificar que se actualiza la celda")
    print("   • Verificar que se muestra mensaje de éxito")
    print("")
    print("🎯 CAMPOS QUE SE PUEDEN EDITAR:")
    print("   • Indicadores de producto")
    print("   • Tipo de indicador")
    print("   • Línea base")
    print("   • Sentido")
    print("   • Tipología")
    print("   • Unidad")
    print("   • Meta cuatrienio")
    print("   • Meta 2024")
    print("   • Datos trimestrales (ejecución, cumplimiento, etc.)")
    print("")
    print("📁 ARCHIVOS DE SOPORTE:")
    print("   • Se almacenan en: uploads/justifications/")
    print("   • Nombres únicos con timestamp")
    print("   • Tipos permitidos: PDF, Word, Excel, imágenes")

if __name__ == '__main__':
    test_advanced_editing()
