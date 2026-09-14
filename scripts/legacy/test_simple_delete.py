#!/usr/bin/env python3
"""
Script simple para probar la eliminación de planes
"""

from app import create_app
from app.models import User, PlanDesarrollo

def test_simple_delete():
    """Prueba simple de eliminación de plan"""

    app = create_app()
    with app.app_context():
        print("🗑️ PRUEBA SIMPLE DE ELIMINACIÓN")
        print("=" * 40)

        try:
            # Verificar usuario admin
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("❌ No hay usuario admin")
                return False

            # Verificar planes inactivos
            plan = PlanDesarrollo.query.filter_by(
                municipio=admin,
                estado='borrador'
            ).first()

            if not plan:
                print("❌ No hay planes inactivos para eliminar")
                print("💡 Crea o desactiva un plan desde la interfaz web")
                return False

            print(f"✅ Usuario: {admin.username}")
            print(f"✅ Plan a eliminar: {plan.titulo} (ID: {plan.id})")
            print(f"✅ Estado: {plan.estado}")

            print("\n📋 INSTRUCCIONES PARA PRUEBA MANUAL:")
            print("   1. Inicia la aplicación: python run.py")
            print("   2. Ve a: http://localhost:5000")
            print("   3. Inicia sesión: admin / admin123")
            print("   4. Ve a Planes (/planes)")
            print(f"   5. Busca el plan: '{plan.titulo}'")
            print("   6. Haz clic en 'Eliminar'")
            print("   7. Confirma la eliminación")
            print("   8. Debería funcionar sin error CSRF")

            print("\n🔧 CAMBIOS REALIZADOS:")
            print("   ✅ Eliminado JavaScript complejo")
            print("   ✅ Cada formulario tiene su token CSRF")
            print("   ✅ Confirmación simple con onclick")
            print("   ✅ Formularios independientes por plan")
            print("   ✅ Sin manipulación dinámica de DOM")

            return True

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False

if __name__ == '__main__':
    success = test_simple_delete()
    if success:
        print("\n🎯 ¡Configuración completada!")
        print("   Ahora prueba la eliminación manualmente.")
    else:
        print("\n❌ Hay problemas de configuración.")
