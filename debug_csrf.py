#!/usr/bin/env python3
"""
Script de diagnóstico para el problema CSRF
"""

from app import create_app
from app.models import User, PlanDesarrollo
from flask import Flask
from flask_wtf.csrf import generate_csrf, validate_csrf

def diagnosticar_csrf():
    """Diagnóstico completo del problema CSRF"""

    app = create_app()
    with app.app_context():
        print("🔍 DIAGNÓSTICO COMPLETO DEL PROBLEMA CSRF")
        print("=" * 60)

        try:
            # Verificar configuración
            print("📋 CONFIGURACIÓN:")
            print(f"   SECRET_KEY: {'✅ Configurado' if app.config.get('SECRET_KEY') else '❌ No configurado'}")
            print(f"   WTF_CSRF_ENABLED: {app.config.get('WTF_CSRF_ENABLED', 'No definido')}")
            print(f"   WTF_CSRF_SECRET_KEY: {app.config.get('WTF_CSRF_SECRET_KEY', 'Usando SECRET_KEY')}")

            # Verificar que existe usuario admin
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("❌ No se encontró usuario admin")
                return False

            # Verificar planes
            plan = PlanDesarrollo.query.filter_by(municipio=admin, estado='borrador').first()
            if not plan:
                print("❌ No hay planes inactivos para probar")
                return False

            print("\n👤 USUARIO:")
            print(f"   Username: {admin.username}")
            print(f"   ID: {admin.id}")

            print("\n📄 PLAN A ELIMINAR:")
            print(f"   ID: {plan.id}")
            print(f"   Título: {plan.titulo}")
            print(f"   Estado: {plan.estado}")

            # Probar generación de token CSRF
            print("\n🔑 PRUEBA DE TOKEN CSRF:")
            try:
                with app.test_request_context():
                    csrf_token = generate_csrf()
                    print(f"   Token generado: {csrf_token[:20]}...")
                    print(f"   Longitud: {len(csrf_token)} caracteres")
                    print("   ✅ Token CSRF generado correctamente")
                    # Probar validación del token
                    try:
                        validate_csrf(csrf_token)
                        print("   ✅ Token CSRF válido")
                    except Exception as e:
                        print(f"   ❌ Error validando token: {str(e)}")

            except Exception as e:
                print(f"   ❌ Error generando token CSRF: {str(e)}")

            # Simular la solicitud de eliminación
            print("\n🚀 SIMULACIÓN DE ELIMINACIÓN:")
            with app.test_client() as client:
                with app.test_request_context():
                    # Paso 1: Login
                    print("   1. Intentando login...")
                    login_response = client.post('/auth/login', data={
                        'username': 'admin',
                        'password': 'admin123',
                        'csrf_token': generate_csrf()
                    }, follow_redirects=True)

                    print(f"      Status: {login_response.status_code}")
                    if login_response.status_code != 200:
                        print("      ❌ Login fallido")
                        return False
                    print("      ✅ Login exitoso")

                    # Paso 2: Verificar que estamos autenticados
                    dashboard_response = client.get('/dashboard')
                    print(f"   2. Dashboard access: {dashboard_response.status_code}")

                    # Paso 3: Intentar eliminación
                    print("   3. Intentando eliminación...")
                    delete_response = client.post(f'/planes/{plan.id}/eliminar',
                                                data={'csrf_token': generate_csrf()},
                                                follow_redirects=True)

                    print(f"      Status: {delete_response.status_code}")

                    if delete_response.status_code == 400:
                        print("      ❌ Error 400 - CSRF problem")
                        print(f"      Response: {delete_response.get_data(as_text=True)[:200]}")
                        return False
                    elif delete_response.status_code == 200:
                        print("      ✅ Eliminación exitosa")
                        return True
                    else:
                        print(f"      ⚠️  Status inesperado: {delete_response.status_code}")
                        print(f"      Response: {delete_response.get_data(as_text=True)[:200]}")
                        return False

        except Exception as e:
            print(f"\n❌ Error durante diagnóstico: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = diagnosticar_csrf()
    if success:
        print("\n🎉 ¡El problema CSRF está resuelto!")
    else:
        print("\n❌ Hay problemas con CSRF que necesitan corrección.")
