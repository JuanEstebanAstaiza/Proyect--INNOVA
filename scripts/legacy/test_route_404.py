#!/usr/bin/env python3
"""
Script para probar la ruta /planes/2 que está dando 404
"""

from app import create_app, db
from app.models.user import User
from app.models.plan_desarrollo import PlanDesarrollo

app = create_app()

def test_route():
    with app.app_context():
        print("🔍 PROBANDO RUTA /planes/2")
        print("=" * 30)

        # Verificar usuario admin
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("❌ No hay usuario admin")
            return

        print(f"✅ Usuario admin encontrado: {admin.username}")

        # Verificar planes
        planes = PlanDesarrollo.query.filter_by(municipio=admin).all()
        if not planes:
            print("❌ No hay planes para el usuario admin")
            return

        print(f"✅ Encontrados {len(planes)} planes")

        # Mostrar detalles de cada plan
        for i, plan in enumerate(planes, 1):
            print(f"   {i}. ID: {plan.id}, Título: {plan.titulo}, Estado: {plan.estado}")

        # Verificar que existe el plan con ID 2
        plan_2 = PlanDesarrollo.query.filter_by(id=2, municipio=admin).first()
        if plan_2:
            print(f"✅ Plan con ID 2 encontrado: {plan_2.titulo}")
        else:
            print("❌ No existe plan con ID 2")
            # Mostrar todos los IDs disponibles
            all_ids = [p.id for p in planes]
            print(f"   IDs disponibles: {all_ids}")

        # Probar la ruta con cliente de prueba
        print("\n🌐 PROBANDO RUTA CON CLIENTE HTTP")
        print("-" * 30)

        with app.test_client() as client:
            # Intentar acceder sin login (debería redirigir)
            response = client.get('/planes/2')
            print(f"Sin login - Status: {response.status_code}")

            if response.status_code == 302:
                print("   ✅ Redirección correcta (usuario no autenticado)")

            # Intentar login
            login_response = client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            }, follow_redirects=True)

            print(f"Login - Status: {login_response.status_code}")

            if login_response.status_code == 200:
                print("   ✅ Login exitoso")

                # Ahora intentar acceder a /planes/2 con usuario autenticado
                planes_response = client.get('/planes/2')
                print(f"Con login - /planes/2 - Status: {planes_response.status_code}")

                if planes_response.status_code == 200:
                    print("   ✅ Ruta /planes/2 funciona correctamente")
                    content = planes_response.get_data(as_text=True)
                    if 'Plan de Desarrollo Municipal' in content:
                        print("   ✅ Template renderizado correctamente")
                    else:
                        print("   ⚠️  Template podría tener problemas")
                elif planes_response.status_code == 404:
                    print("   ❌ Error 404 - Ruta no encontrada")
                    print("   Posibles causas:")
                    print("   - Template 'planes/ver.html' no existe")
                    print("   - Error en la función ver(plan_id)")
                    print("   - Problema con el Blueprint")
                else:
                    print(f"   ⚠️  Status inesperado: {planes_response.status_code}")
                    print(f"   Respuesta: {planes_response.get_data(as_text=True)[:200]}...")
            else:
                print("   ❌ Error en login")
                print(f"   Respuesta: {login_response.get_data(as_text=True)[:200]}...")

        print("\n🔧 RECOMENDACIONES:")
        print("-" * 20)
        print("1. Verificar que el template 'app/templates/planes/ver.html' existe")
        print("2. Verificar que no hay errores de sintaxis en planes.py")
        print("3. Verificar que el plan con ID 2 existe en la base de datos")
        print("4. Probar acceder directamente desde el navegador con login")

        print("\n🧪 PRUEBA MANUAL:")
        print("-" * 15)
        print("1. python run.py")
        print("2. Ir a http://localhost:5000")
        print("3. Login: admin / admin123")
        print("4. Ir directamente a: http://localhost:5000/planes/2")
        print("5. Verificar si se carga la página correctamente")

if __name__ == '__main__':
    test_route()
