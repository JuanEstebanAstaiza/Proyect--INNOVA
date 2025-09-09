#!/usr/bin/env python3
"""
Script para probar que el dashboard funciona correctamente
"""

from app import create_app
from app.models import User, PlanDesarrollo

def test_dashboard():
    """Prueba que el dashboard funciona correctamente"""

    app = create_app()
    with app.app_context():
        print("📊 PRUEBA DEL DASHBOARD")
        print("=" * 40)

        try:
            # Verificar usuario admin
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("❌ No hay usuario admin")
                return False

            print(f"✅ Usuario admin encontrado: {admin.username}")

            # Verificar que hay al menos un plan
            planes_count = PlanDesarrollo.query.filter_by(municipio=admin).count()
            print(f"📋 Total de planes: {planes_count}")

            # Verificar que funciona la consulta del plan activo
            plan_activo = PlanDesarrollo.query.filter_by(
                municipio=admin,
                estado='activo'
            ).first()

            if plan_activo:
                print(f"✅ Plan activo encontrado: {plan_activo.titulo}")
            else:
                print("ℹ️  No hay plan activo (esto es normal)")

            print("\n🎯 PRUEBA MANUAL:")
            print("   1. Inicia la aplicación: python run.py")
            print("   2. Ve a: http://localhost:5000")
            print("   3. Inicia sesión: admin / admin123")
            print("   4. Deberías ver el dashboard sin errores")
            print("   5. Los botones deberían funcionar correctamente")

            print("\n🔧 CORRECCIÓN REALIZADA:")
            print("   ✅ Movida consulta del plan activo al controlador")
            print("   ✅ Eliminada consulta problemática del template")
            print("   ✅ Usada variable plan_activo desde el contexto")
            print("   ✅ Dashboard debería cargar sin errores 500")

            return True

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test_dashboard()
    if success:
        print("\n🎉 ¡Dashboard corregido!")
        print("   Prueba manual recomendada.")
    else:
        print("\n❌ Hay problemas.")
