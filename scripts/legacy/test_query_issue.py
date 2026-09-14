#!/usr/bin/env python3
"""
Script para probar específicamente el problema de consultas
"""

import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, PlanDesarrollo

def test_query_issue():
    """Prueba el problema específico de consultas"""
    app = create_app()
    app.app_context().push()

    print("🔍 TESTEANDO PROBLEMA DE CONSULTAS ESPECÍFICO")
    print("=" * 60)

    # Obtener el usuario que tiene el plan
    user = User.query.filter_by(username='admin_test_data').first()
    if not user:
        print("❌ Usuario 'admin_test_data' no encontrado")
        return

    print(f"👤 Usuario encontrado: {user.username} (ID: {user.id})")
    print(f"   Email: {user.email}")
    print(f"   Municipio: {user.municipality}")
    print()

    # Verificar el plan directamente
    plan = PlanDesarrollo.query.filter_by(municipio=user).first()
    if plan:
        print("✅ CONSULTA DIRECTA: Plan encontrado")
        print(f"   Título: {plan.titulo}")
        print(f"   Estado: {plan.estado}")
        print(f"   Municipio ID: {plan.municipio_id}")
        print(f"   Usuario relacionado: {plan.municipio.username if plan.municipio else 'N/A'}")
    else:
        print("❌ CONSULTA DIRECTA: Plan NO encontrado")

    # Probar consulta por municipio_id
    plan_by_id = PlanDesarrollo.query.filter_by(municipio_id=user.id).first()
    if plan_by_id:
        print("✅ CONSULTA POR ID: Plan encontrado")
        print(f"   Título: {plan_by_id.titulo}")
        print(f"   Estado: {plan_by_id.estado}")
        print(f"   Municipio ID: {plan_by_id.municipio_id}")
    else:
        print("❌ CONSULTA POR ID: Plan NO encontrado")

    # Probar consulta por estado
    active_plans = PlanDesarrollo.query.filter_by(
        municipio=user,
        estado='activo'
    ).all()
    print(f"\n📊 Planes activos para {user.username}: {len(active_plans)}")
    for p in active_plans:
        print(f"   - {p.titulo}")

    # Verificar todos los planes en la base de datos
    all_plans = PlanDesarrollo.query.all()
    print(f"\n📋 TODOS los planes en BD: {len(all_plans)}")
    for p in all_plans:
        print(f"   - {p.titulo}")
        print(f"     Estado: {p.estado}")
        print(f"     Municipio ID: {p.municipio_id}")
        print(f"     Usuario: {p.municipio.username if p.municipio else 'N/A'}")

    print("\n" + "=" * 60)
    print("🔧 DIAGNÓSTICO:")
    print("=" * 60)

    if plan and len(active_plans) == 0:
        print("❌ PROBLEMA IDENTIFICADO:")
        print("   - El plan existe y pertenece al usuario")
        print("   - Pero la consulta con estado='activo' no lo encuentra")
        print("   - Posible problema: El estado no es exactamente 'activo'")

    if plan and len(active_plans) > 0:
        print("✅ TODO FUNCIONA CORRECTAMENTE:")
        print("   - El plan se encuentra correctamente")
        print("   - Las consultas están funcionando")

    print("\n💡 RECOMENDACIONES:")
    print("- Verifica el estado exacto del plan en la base de datos")
    print("- Asegúrate de que el usuario logueado sea el correcto")
    print("- Revisa si hay problemas de permisos en la aplicación")

if __name__ == "__main__":
    test_query_issue()
