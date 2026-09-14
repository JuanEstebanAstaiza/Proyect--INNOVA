#!/usr/bin/env python3
"""
Script para reasignar el plan generado al usuario admin correcto
"""

import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, PlanDesarrollo

def fix_plan_assignment():
    """Reasigna el plan al usuario admin correcto"""
    app = create_app()
    app.app_context().push()

    print("🔧 REASIGNANDO PLAN AL USUARIO ADMIN")
    print("=" * 50)

    # Obtener el usuario admin actual (el que probablemente esté usando)
    admin_user = User.query.filter_by(email='admin@alcaldia.com').first()
    if not admin_user:
        print("❌ Usuario admin (admin@alcaldia.com) no encontrado")
        return False

    print(f"👤 Usuario admin encontrado: {admin_user.username} (ID: {admin_user.id})")

    # Obtener el plan generado
    plan = PlanDesarrollo.query.filter_by(titulo='Plan de Desarrollo TEST 2024-2027').first()
    if not plan:
        print("❌ Plan 'Plan de Desarrollo TEST 2024-2027' no encontrado")
        return False

    print(f"📋 Plan encontrado: {plan.titulo}")
    print(f"   Estado actual: {plan.estado}")
    if plan.municipio:
        print(f"   Usuario actual: {plan.municipio.username} ({plan.municipio.email})")

    # Reasignar el plan al usuario admin
    plan.municipio = admin_user
    db.session.commit()

    print("\n✅ PLAN REASIGNADO EXITOSAMENTE!")
    print(f"   Nuevo usuario: {admin_user.username} ({admin_user.email})")
    print(f"   Plan: {plan.titulo}")
    print(f"   Estado: {plan.estado}")

    # Verificar que la reasignación funcionó
    updated_plan = PlanDesarrollo.query.filter_by(titulo='Plan de Desarrollo TEST 2024-2027').first()
    if updated_plan and updated_plan.municipio == admin_user:
        print("\n🎉 VERIFICACIÓN EXITOSA:")
        print("   ✅ El plan está correctamente asignado al usuario admin")
        print("   ✅ Ahora podrás ver el plan en la aplicación")
        return True
    else:
        print("\n❌ ERROR EN LA VERIFICACIÓN:")
        print("   La reasignación no funcionó correctamente")
        return False

def main():
    """Función principal"""
    print("🔧 SOLUCIÓN: Reasignar plan al usuario admin")
    print("=" * 50)

    success = fix_plan_assignment()

    if success:
        print("\n" + "=" * 50)
        print("💡 PRÓXIMOS PASOS:")
        print("1. Actualiza la página en tu navegador")
        print("2. Deberías ver ahora el plan 'Plan de Desarrollo TEST 2024-2027'")
        print("3. Explora las 4 líneas estratégicas, 11 componentes, 28 proyectos, etc.")
        print("4. Prueba la vista Excel con los 111 indicadores")
        print("=" * 50)
    else:
        print("\n❌ No se pudo completar la reasignación")
        print("Por favor verifica los logs de error")

if __name__ == "__main__":
    main()
