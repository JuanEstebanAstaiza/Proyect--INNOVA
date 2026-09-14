#!/usr/bin/env python3
"""
Script simple para probar que los reportes funcionan
"""

from app import create_app
from app.models import User, PlanDesarrollo

def test_reportes_simple():
    """Prueba simple que los reportes funcionan"""

    app = create_app()
    with app.app_context():
        print("🧪 PRUEBA SIMPLE DE REPORTES")
        print("=" * 40)

        try:
            # Verificar usuario admin
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("❌ No hay usuario admin")
                return False

            # Verificar planes
            plan = PlanDesarrollo.query.filter_by(municipio=admin).first()
            if not plan:
                print("❌ No hay planes")
                return False

            print(f"✅ Usuario: {admin.username}")
            print(f"✅ Plan: {plan.titulo} (ID: {plan.id})")

            # Probar que la aplicación responde
            with app.test_client() as client:
                # Login
                login_response = client.post('/auth/login', data={
                    'username': 'admin',
                    'password': 'admin123'
                }, follow_redirects=True)

                if login_response.status_code not in [200, 302]:
                    print(f"❌ Error en login: {login_response.status_code}")
                    return False

                print("✅ Login exitoso")

                # Probar página de reportes
                reportes_response = client.get(f'/planes/{plan.id}/reportes')
                print(f"📊 Status de reportes: {reportes_response.status_code}")

                if reportes_response.status_code == 200:
                    print("✅ Página de reportes accesible")

                    # Verificar contenido básico
                    content = reportes_response.get_data(as_text=True)
                    checks = [
                        'Reportes y Análisis' in content,
                        'Filtros de Análisis' in content,
                        'Chart.js' in content.lower()
                    ]

                    if all(checks):
                        print("✅ Contenido de reportes correcto")
                        return True
                    else:
                        print("⚠️  Contenido incompleto")
                        return False
                else:
                    print(f"❌ Error en reportes: {reportes_response.status_code}")
                    return False

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False

if __name__ == '__main__':
    success = test_reportes_simple()
    if success:
        print("\n🎉 ¡Reportes funcionando correctamente!")
        print("   Ya puedes acceder a /planes/ID/reportes")
    else:
        print("\n❌ Hay problemas con los reportes.")
