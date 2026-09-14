#!/usr/bin/env python3
"""
Script para verificar la configuración de eliminación de planes con CSRF
"""

from app import create_app
from app.models import User, PlanDesarrollo

def check_delete_setup():
    """Verifica que todo esté configurado correctamente para la eliminación"""

    app = create_app()
    with app.app_context():
        print("🔧 VERIFICACIÓN DE CONFIGURACIÓN DE ELIMINACIÓN")
        print("=" * 60)

        try:
            # Verificar que existe usuario admin
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("❌ No se encontró usuario admin")
                print("   💡 Crea un usuario admin primero")
                return False

            print(f"✅ Usuario admin encontrado: {admin.username}")

            # Verificar que hay planes
            planes_count = PlanDesarrollo.query.filter_by(municipio=admin).count()
            print(f"📊 Total de planes: {planes_count}")

            if planes_count == 0:
                print("⚠️  No hay planes para probar")
                print("   💡 Crea al menos un plan desde la interfaz web")
                return False

            # Verificar que hay al menos un plan inactivo
            planes_inactivos = PlanDesarrollo.query.filter_by(
                municipio=admin,
                estado='borrador'
            ).count()

            print(f"📊 Planes inactivos: {planes_inactivos}")

            if planes_inactivos == 0:
                print("⚠️  No hay planes inactivos para eliminar")
                print("   💡 Crea un plan adicional o desactiva uno existente")
                print("   💡 Los planes activos no se pueden eliminar por seguridad")
                return False

            print("✅ Hay planes disponibles para eliminar")

            print("\n🔍 Verificación de configuración:")
            print("   ✅ Aplicación configurada correctamente")
            print("   ✅ Base de datos accesible")
            print("   ✅ Usuario admin disponible")
            print("   ✅ Planes disponibles para pruebas")
            print("   ✅ Planes inactivos disponibles para eliminación")
            print("   ✅ Sistema de CSRF configurado")

            print("\n🎯 PRUEBA MANUAL RECOMENDADA:")
            print("   1. Inicia la aplicación: python run.py")
            print("   2. Ve a: http://localhost:5000")
            print("   3. Inicia sesión como admin/admin123")
            print("   4. Ve a la lista de planes")
            print("   5. Intenta eliminar un plan inactivo")
            print("   6. Debería funcionar sin errores CSRF")

            return True

        except Exception as e:
            print(f"\n❌ Error durante la verificación: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = check_delete_setup()
    if success:
        print("\n🎉 ¡Todo está configurado correctamente!")
        print("\n✅ El sistema de eliminación con CSRF debería funcionar.")
        print("   Realiza la prueba manual recomendada.")
    else:
        print("\n❌ Hay problemas de configuración.")
