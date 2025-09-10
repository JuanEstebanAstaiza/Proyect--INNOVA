#!/usr/bin/env python3
"""
Script para verificar que la gestión de planes funciona en el dashboard
"""
from app import create_app
from app.models import PlanDesarrollo

def test_dashboard_plans():
    """Verificar que la gestión de planes está disponible en el dashboard"""
    print("🔧 Verificando gestión de planes en dashboard...")

    try:
        app = create_app()
        with app.app_context():
            print("✅ Aplicación creada correctamente")

            # Verificar que hay rutas de planes disponibles
            with app.test_client() as client:
                # Verificar que la ruta de planes existe
                response = client.get('/planes/')
                print(f"📡 GET /planes/: HTTP {response.status_code}")

                # Verificar que la ruta de crear plan existe
                response = client.get('/planes/crear')
                print(f"📡 GET /planes/crear: HTTP {response.status_code}")

                # Verificar estadísticas de planes
                plans = PlanDesarrollo.query.all()
                active_plans = PlanDesarrollo.query.filter_by(estado='activo').all()

                print(f"📊 Total de planes: {len(plans)}")
                print(f"📊 Planes activos: {len(active_plans)}")

                if plans:
                    print("\n📋 Lista de planes disponibles:")
                    for plan in plans[:3]:  # Mostrar primeros 3
                        status = "✅ ACTIVO" if plan.estado == 'activo' else f"📝 {plan.estado.upper()}"
                        print(f"   - ID: {plan.id}, Título: {plan.titulo}, Estado: {status}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n🎯 Próximos pasos:")
    print("1. Ejecuta la aplicación: python run.py")
    print("2. Ve a http://localhost:5000/admin/")
    print("3. Deberías ver el botón 'Gestionar Planes' en los accesos rápidos")
    print("4. Haz click en 'Gestionar Planes' para acceder a la gestión completa")
    print("5. La tarjeta de estadísticas debería mostrar el número de planes")

if __name__ == "__main__":
    test_dashboard_plans()
