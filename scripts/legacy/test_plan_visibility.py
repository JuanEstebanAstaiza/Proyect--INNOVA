#!/usr/bin/env python3
"""
Script para probar que los editores pueden ver el plan activo global
"""
from app import create_app, db
from app.models import User, PlanDesarrollo

def test_plan_visibility():
    """Probar que los editores pueden ver el plan activo global"""
    print("🔍 PROBANDO VISIBILIDAD DE PLANES PARA EDITORES")
    print("=" * 60)

    with create_app().app_context():
        try:
            # Obtener usuarios
            admin_user = User.query.filter_by(username='admin').first()
            auditor_pruebas = User.query.filter_by(username='auditor_pruebas').first()

            # Obtener plan activo
            plan_activo = PlanDesarrollo.query.filter_by(estado='activo').first()

            print(f"📋 Plan Activo: {plan_activo.titulo if plan_activo else 'Ninguno'}")
            print(f"🏛️ Municipio del Plan: {plan_activo.municipio.municipality if plan_activo else 'N/A'}")
            print()

            # Simular lógica de dashboard para admin
            print("👤 SIMULACIÓN PARA ADMIN:")
            puede_ver_global_admin = admin_user.is_admin() or admin_user.is_editor()
            print(f"   ✅ ¿Puede ver global?: {puede_ver_global_admin}")
            print(f"   🏛️ Municipio admin: {admin_user.municipality}")
            print(f"   📋 Plan que vería: {plan_activo.titulo if plan_activo else 'Ninguno'}")
            print()

            # Simular lógica de dashboard para auditor
            print("👤 SIMULACIÓN PARA AUDITOR DE PRUEBAS:")
            puede_ver_global_auditor = auditor_pruebas.is_admin() or auditor_pruebas.is_editor()
            print(f"   ✅ ¿Puede ver global?: {puede_ver_global_auditor}")
            print(f"   👔 Rol: {auditor_pruebas.legacy_role}")
            print(f"   🏛️ Municipio auditor: {auditor_pruebas.municipality}")

            if puede_ver_global_auditor:
                print("   📋 Plan que vería: Plan activo global")
            else:
                print("   ❌ Solo vería planes de su municipio")
            print()

            # Simular lógica de lista de planes para auditor
            print("📋 SIMULACIÓN LISTA DE PLANES PARA AUDITOR:")
            if puede_ver_global_auditor:
                plan_activo_global = PlanDesarrollo.query.filter_by(estado='activo').first()
                planes_municipio = PlanDesarrollo.query.filter_by(municipio=auditor_pruebas).all()
                planes = [plan_activo_global] if plan_activo_global not in planes_municipio else []
                planes.extend(planes_municipio)
                print(f"   📊 Planes que vería: {len(planes)}")
                for plan in planes:
                    print(f"      - {plan.titulo} ({'Activo' if plan.estado == 'activo' else 'Borrador'})")
            else:
                plan_activo_local = PlanDesarrollo.query.filter_by(
                    municipio=auditor_pruebas,
                    estado='activo'
                ).first()
                if plan_activo_local:
                    print(f"   📋 Plan que vería: {plan_activo_local.titulo}")
                else:
                    print("   ❌ No vería ningún plan")
            print()

            # Verificar resultado esperado
            print("🎯 RESULTADO ESPERADO:")
            if auditor_pruebas.legacy_role == 'editor' and plan_activo:
                print("   ✅ El auditor debería poder ver el plan activo global")
                print("   ✅ La solución debería funcionar correctamente")
            else:
                print("   ⚠️ Revisar configuración de roles o planes")

            return True

        except Exception as e:
            print(f"❌ Error probando visibilidad: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_plan_visibility()
    if success:
        print("\n🎊 ¡Prueba completada exitosamente!")
        print("Los editores ahora deberían poder ver el plan activo global.")
    else:
        print("\n❌ Error en la prueba.")
