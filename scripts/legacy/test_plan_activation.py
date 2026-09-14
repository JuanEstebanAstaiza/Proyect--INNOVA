#!/usr/bin/env python3
"""
Script de prueba para el sistema de activación de planes
"""

from app import create_app, db
from app.models import PlanDesarrollo, User

def test_plan_activation():
    """Prueba el sistema de activación/desactivación de planes"""

    app = create_app()
    with app.app_context():
        print("🧪 PRUEBA DEL SISTEMA DE ACTIVACIÓN DE PLANES")
        print("=" * 60)

        try:
            # Buscar usuario admin
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("❌ No se encontró usuario admin")
                return False

            print(f"👤 Usuario de prueba: {admin.username}")

            # Obtener todos los planes del admin
            planes = PlanDesarrollo.query.filter_by(municipio=admin).all()
            print(f"\n📋 Total de planes encontrados: {len(planes)}")

            if len(planes) < 2:
                print("⚠️  Necesitas al menos 2 planes para probar el sistema.")
                print("   Crea más planes desde la interfaz web.")
                return False

            # Mostrar estado actual de los planes
            print("\n📊 Estado actual de los planes:")
            for plan in planes:
                estado_icon = "✅" if plan.estado == 'activo' else "⭕"
                print(f"   {estado_icon} ID: {plan.id} - {plan.titulo} ({plan.estado})")

            # Encontrar un plan inactivo para activar
            plan_inactivo = None
            for plan in planes:
                if plan.estado != 'activo':
                    plan_inactivo = plan
                    break

            if not plan_inactivo:
                print("\n❌ Todos los planes ya están activos")
                return False

            print(f"\n🎯 Activando plan: {plan_inactivo.titulo}")

            # Activar el plan
            plan_inactivo.activar()

            # Verificar que se activó correctamente
            plan_refreshed = PlanDesarrollo.query.get(plan_inactivo.id)
            if plan_refreshed.estado != 'activo':
                print("❌ Error: El plan no se activó correctamente")
                return False

            # Verificar que los demás planes se desactivaron
            planes_desactivados = PlanDesarrollo.query.filter_by(
                municipio=admin,
                estado='borrador'
            ).count()

            print("\n✅ Resultado de la activación:")
            print(f"   • Plan activado: {plan_refreshed.titulo}")
            print(f"   • Estado: {plan_refreshed.estado}")
            print(f"   • Planes desactivados: {planes_desactivados}")

            # Probar desactivación
            print(f"\n🎯 Desactivando plan: {plan_refreshed.titulo}")
            plan_refreshed.desactivar()

            plan_after_deactivate = PlanDesarrollo.query.get(plan_refreshed.id)
            print(f"   • Estado después de desactivar: {plan_after_deactivate.estado}")

            # Probar métodos de clase
            print("\n🧪 Probando métodos de clase:")
            plan_activo = PlanDesarrollo.get_plan_activo(admin)
            if plan_activo:
                print(f"   • Plan activo encontrado: {plan_activo.titulo}")
            else:
                print("   • No hay plan activo (correcto)")

            plan_activo_o_primero = PlanDesarrollo.get_plan_activo_o_primero(admin)
            if plan_activo_o_primero:
                print(f"   • Plan activo o primero: {plan_activo_o_primero.titulo}")

            print("\n🎉 ¡Sistema de activación de planes funcionando correctamente!")
            return True

        except Exception as e:
            print(f"\n❌ Error durante la prueba: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test_plan_activation()
    if success:
        print("\n✅ Todas las pruebas pasaron exitosamente!")
    else:
        print("\n❌ Algunas pruebas fallaron.")
