#!/usr/bin/env python3
"""
Script para debuggear las consultas de la aplicación
"""

import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, PlanDesarrollo, LineaEstrategica

def debug_queries():
    """Debuggea las consultas que usa la aplicación"""
    app = create_app()
    app.app_context().push()

    print("🔧 DEBUGGING CONSULTAS DE LA APLICACIÓN")
    print("=" * 60)

    # Verificar todos los usuarios
    users = User.query.all()
    print(f"👥 Total de usuarios: {len(users)}")
    for i, user in enumerate(users, 1):
        print(f"  {i}. {user.username} ({user.email}) - Municipio: {user.municipality}")
    print()

    # Verificar planes de desarrollo
    plans = PlanDesarrollo.query.all()
    print(f"📋 Total de planes: {len(plans)}")
    for i, plan in enumerate(plans, 1):
        print(f"  {i}. {plan.titulo}")
        print(f"     Estado: {plan.estado}")
        print(f"     Municipio: {plan.municipio.username if plan.municipio else 'N/A'}")
        print(f"     Usuario ID: {plan.municipio_id if plan.municipio else 'N/A'}")
    print()

    # Simular la consulta que haría la aplicación para un usuario específico
    print("🎯 SIMULANDO CONSULTAS DE LA APLICACIÓN:")
    print("-" * 40)

    for user in users:
        print(f"\n👤 Consultando para usuario: {user.username}")

        # Esta es la consulta que probablemente usa la aplicación
        user_plans = PlanDesarrollo.query.filter_by(
            municipio=user,
            estado='activo'
        ).all()

        print(f"   📋 Planes encontrados: {len(user_plans)}")
        for plan in user_plans:
            print(f"     ✅ {plan.titulo}")

        if not user_plans:
            print("     ❌ No se encontraron planes para este usuario")
            # Verificar si hay planes pero con estado diferente
            all_user_plans = PlanDesarrollo.query.filter_by(municipio=user).all()
            if all_user_plans:
                print(f"     ℹ️  Hay {len(all_user_plans)} planes pero con estado diferente:")
                for plan in all_user_plans:
                    print(f"        - {plan.titulo} (estado: {plan.estado})")

    print("\n" + "=" * 60)
    print("💡 POSIBLES PROBLEMAS IDENTIFICADOS:")
    print("=" * 60)

    # Verificar si hay problemas de permisos
    test_user = User.query.filter_by(username='admin_test_data').first()
    if test_user:
        print("1. ✅ Usuario 'admin_test_data' existe")

        # Verificar si tiene planes asociados
        user_plans = PlanDesarrollo.query.filter_by(municipio=test_user).all()
        if user_plans:
            print("2. ✅ Usuario tiene planes asociados")
            for plan in user_plans:
                print(f"   - {plan.titulo} (estado: {plan.estado})")
        else:
            print("2. ❌ Usuario NO tiene planes asociados")

        # Verificar si hay algún plan sin usuario asignado
        orphan_plans = PlanDesarrollo.query.filter(
            db.or_(PlanDesarrollo.municipio_id.is_(None), PlanDesarrollo.municipio_id == 0)
        ).all()
        if orphan_plans:
            print("3. ⚠️  Hay planes sin usuario asignado:")
            for plan in orphan_plans:
                print(f"   - {plan.titulo}")
        else:
            print("3. ✅ No hay planes huérfanos")

    print("\n🔧 RECOMENDACIONES:")
    print("- Verifica con qué usuario estás logueado en la aplicación")
    print("- Asegúrate de que el usuario tenga permisos para ver planes")
    print("- Revisa la consola del navegador por errores JavaScript")
    print("- Verifica que la aplicación esté conectada a la misma base de datos")

if __name__ == "__main__":
    debug_queries()
