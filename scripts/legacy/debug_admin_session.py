#!/usr/bin/env python3
"""
Script para debuggear específicamente la sesión del admin y planes activos
"""

import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, PlanDesarrollo

def debug_admin_session():
    """Debuggea la sesión del admin y los planes activos"""
    app = create_app()
    app.app_context().push()

    print("🔧 DEBUGGING SESIÓN ADMIN Y PLANES ACTIVOS")
    print("=" * 60)

    # Verificar todos los usuarios admin
    admin_users = User.query.filter(
        db.or_(
            User.username == 'admin',
            User.email == 'admin@alcaldia.com',
            User.username == 'admin_test_data',
            User.email == 'admin@test.com'
        )
    ).all()

    print(f"👥 Usuarios admin encontrados: {len(admin_users)}")
    for user in admin_users:
        print(f"  - {user.username} ({user.email}) - ID: {user.id}")
    print()

    # Verificar el plan generado
    plan = PlanDesarrollo.query.filter_by(titulo='Plan de Desarrollo TEST 2024-2027').first()
    if plan:
        print("✅ PLAN ENCONTRADO:")
        print(f"  Título: {plan.titulo}")
        print(f"  Estado: {plan.estado}")
        print(f"  Municipio ID: {plan.municipio_id}")
        if plan.municipio:
            print(f"  Usuario asignado: {plan.municipio.username} ({plan.municipio.email})")
        else:
            print("  ❌ Usuario asignado: NINGUNO")
        print()

        # Verificar qué usuarios tienen acceso a este plan
        for user in admin_users:
            user_plans = PlanDesarrollo.query.filter_by(
                municipio=user,
                estado='activo'
            ).all()
            print(f"📋 Planes activos para {user.username}: {len(user_plans)}")
            for p in user_plans:
                print(f"     ✅ {p.titulo}")
            if not user_plans:
                print("     ❌ No tiene planes activos")
    else:
        print("❌ PLAN NO ENCONTRADO")
        print("   El plan 'Plan de Desarrollo TEST 2024-2027' no existe")
    print()

    # Verificar todos los planes en la BD
    all_plans = PlanDesarrollo.query.all()
    print(f"📋 TODOS los planes en BD: {len(all_plans)}")
    for p in all_plans:
        print(f"  - {p.titulo}")
        print(f"    Estado: {p.estado}")
        print(f"    Municipio ID: {p.municipio_id}")
        if p.municipio:
            print(f"    Usuario: {p.municipio.username} ({p.municipio.email})")
        else:
            print("    Usuario: NINGUNO")
    print()

    # Simular la lógica del método get_plan_activo_o_primero
    print("🎯 SIMULANDO LÓGICA DE LA APLICACIÓN:")
    print("-" * 40)

    for user in admin_users:
        print(f"\n👤 Para usuario: {user.username}")

        # Paso 1: Buscar plan activo
        plan_activo = PlanDesarrollo.query.filter_by(
            municipio=user,
            estado='activo'
        ).first()

        if plan_activo:
            print(f"  ✅ Plan activo encontrado: {plan_activo.titulo}")
        else:
            print("  ❌ No hay plan activo")

            # Paso 2: Buscar el plan más reciente
            plan_reciente = PlanDesarrollo.query.filter_by(municipio=user).order_by(
                PlanDesarrollo.created_at.desc()
            ).first()

            if plan_reciente:
                print(f"  ✅ Plan más reciente encontrado: {plan_reciente.titulo}")
                print(f"     Estado: {plan_reciente.estado}")
            else:
                print("  ❌ No hay ningún plan para este usuario")

    print("\n" + "=" * 60)
    print("💡 POSIBLES PROBLEMAS:")
    print("=" * 60)

    # Verificar problemas específicos
    if plan:
        assigned_user = plan.municipio
        if not assigned_user:
            print("❌ PROBLEMA: El plan no tiene usuario asignado")
            print("   Solución: Asignar el plan a un usuario admin")
        elif assigned_user.username not in ['admin', 'admin_test_data']:
            print("❌ PROBLEMA: El plan está asignado a un usuario no admin")
            print(f"   Usuario actual: {assigned_user.username}")
            print("   Solución: Reasignar el plan a un usuario admin")
        else:
            print("✅ El plan está correctamente asignado a un usuario admin")
    else:
        print("❌ PROBLEMA: El plan no existe en la base de datos")

    print("\n🔧 RECOMENDACIONES:")
    print("- Verifica que estás logueado con el usuario correcto")
    print("- Si el problema persiste, puede ser necesario reasignar el plan")
    print("- Considera crear un nuevo plan si los datos están corruptos")

if __name__ == "__main__":
    debug_admin_session()
