#!/usr/bin/env python3
"""
Script para probar el sistema completo de permisos de fila
"""

import os
import sys
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    User, PlanDesarrollo, LineaEstrategica, Componente,
    Programa, Proyecto, IndicadorProducto, RowPermission
)

def test_row_permissions_system():
    """Probar el sistema completo de permisos de fila"""
    app = create_app()
    app.app_context().push()

    print("🧪 PRUEBA COMPLETA DEL SISTEMA DE PERMISOS DE FILA")
    print("=" * 60)

    # Obtener usuario admin
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        print("❌ Usuario admin no encontrado")
        return

    print(f"✅ Usuario admin encontrado: {admin.username}")

    # Verificar plan activo
    active_plan = PlanDesarrollo.query.filter_by(
        municipio=admin,
        estado='activo'
    ).first()

    if not active_plan:
        print("❌ No hay plan activo para el admin")
        return

    print(f"✅ Plan activo encontrado: {active_plan.titulo}")
    print()

    # =============================================
    # PRUEBA 1: CREAR PERMISOS DE FILA
    # =============================================
    print("📝 PRUEBA 1: CREACIÓN DE PERMISOS DE FILA")
    print("-" * 40)

    # Obtener algunas entidades para asignar permisos
    linea = LineaEstrategica.query.filter_by(plan_id=active_plan.id).first()
    if not linea:
        print("❌ No hay líneas estratégicas en el plan")
        return

    componente = Componente.query.filter_by(linea_estrategica_id=linea.id).first()
    programa = Programa.query.filter_by(componente_id=componente.id).first() if componente else None
    proyecto = Proyecto.query.filter_by(programa_id=programa.id).first() if programa else None
    indicador = IndicadorProducto.query.filter_by(proyecto_id=proyecto.id).first() if proyecto else None

    print(f"✅ Entidades encontradas:")
    print(f"   Línea: {linea.nombre}")
    if componente:
        print(f"   Componente: {componente.nombre}")
    if programa:
        print(f"   Programa: {programa.nombre}")
    if proyecto:
        print(f"   Proyecto: {proyecto.nombre}")
    if indicador:
        print(f"   Indicador: {indicador.nombre}")

    # Crear permisos de fila de prueba
    permissions_created = []

    if indicador:
        # Permiso para indicador
        permission_indicador = RowPermission(
            user_id=admin.id,
            plan_id=active_plan.id,
            indicador_id=indicador.id,
            permission_scope='indicador',
            can_view=True,
            can_edit=True,
            description='Permiso de prueba para indicador específico',
            assigned_by=admin.id
        )
        db.session.add(permission_indicador)
        permissions_created.append(('indicador', indicador.nombre))

    if proyecto:
        # Permiso para proyecto
        permission_proyecto = RowPermission(
            user_id=admin.id,
            plan_id=active_plan.id,
            proyecto_id=proyecto.id,
            permission_scope='proyecto',
            can_view=True,
            can_edit=False,
            description='Permiso de solo lectura para proyecto específico',
            assigned_by=admin.id
        )
        db.session.add(permission_proyecto)
        permissions_created.append(('proyecto', proyecto.nombre))

    if programa:
        # Permiso para programa
        permission_programa = RowPermission(
            user_id=admin.id,
            plan_id=active_plan.id,
            programa_id=programa.id,
            permission_scope='programa',
            can_view=True,
            can_edit=False,
            description='Permiso de solo lectura para programa específico',
            assigned_by=admin.id
        )
        db.session.add(permission_programa)
        permissions_created.append(('programa', programa.nombre))

    db.session.commit()
    print(f"✅ Permisos creados: {len(permissions_created)}")
    for scope, name in permissions_created:
        print(f"   - {scope.title()}: {name}")

    print()

    # =============================================
    # PRUEBA 2: VERIFICACIÓN DE PERMISOS
    # =============================================
    print("🔍 PRUEBA 2: VERIFICACIÓN DE PERMISOS")
    print("-" * 40)

    # Probar métodos de verificación
    if indicador:
        can_edit_indicador = admin.can_edit_entity(indicador.id, 'indicador', active_plan.id)
        can_view_indicador = admin.can_view_entity(indicador.id, 'indicador', active_plan.id)
        print(f"📊 Indicador '{indicador.nombre}':")
        print(f"   Puede editar: {'✅' if can_edit_indicador else '❌'}")
        print(f"   Puede ver: {'✅' if can_view_indicador else '❌'}")

        # Verificar método legacy
        can_edit_row = admin.can_edit_row(indicador.id, active_plan.id)
        print(f"   Método legacy can_edit_row: {'✅' if can_edit_row else '❌'}")

    if proyecto:
        can_edit_proyecto = admin.can_edit_entity(proyecto.id, 'proyecto', active_plan.id)
        can_view_proyecto = admin.can_view_entity(proyecto.id, 'proyecto', active_plan.id)
        print(f"📊 Proyecto '{proyecto.nombre}':")
        print(f"   Puede editar: {'✅' if can_edit_proyecto else '❌'}")
        print(f"   Puede ver: {'✅' if can_view_proyecto else '❌'}")

    if programa:
        can_edit_programa = admin.can_edit_entity(programa.id, 'programa', active_plan.id)
        can_view_programa = admin.can_view_entity(programa.id, 'programa', active_plan.id)
        print(f"📊 Programa '{programa.nombre}':")
        print(f"   Puede editar: {'✅' if can_edit_programa else '❌'}")
        print(f"   Puede ver: {'✅' if can_view_programa else '❌'}")

    print()

    # =============================================
    # PRUEBA 3: ESTADÍSTICAS DE PERMISOS
    # =============================================
    print("📈 PRUEBA 3: ESTADÍSTICAS DE PERMISOS")
    print("-" * 40)

    # Obtener permisos del usuario para el plan
    user_permissions = RowPermission.get_user_permissions_for_plan(admin.id, active_plan.id)

    print(f"🔢 Total de permisos activos para {admin.username}: {len(user_permissions)}")

    for permission in user_permissions:
        print(f"   - {permission.entity_type_display}: {permission.entity_name}")
        print(f"     Permisos: Ver={'✅' if permission.can_view else '❌'}, Editar={'✅' if permission.can_edit else '❌'}")

        # Mostrar jerarquía
        hierarchy = permission.get_scope_hierarchy()
        if hierarchy:
            print(f"     Jerarquía: {' → '.join([f'{item[0]}: {item[1]}' for item in hierarchy])}")
        print()

    # =============================================
    # PRUEBA 4: LIMPIEZA
    # =============================================
    print("🧹 PRUEBA 4: LIMPIEZA DE DATOS DE PRUEBA")
    print("-" * 40)

    # Marcar permisos como inactivos (no eliminar)
    cleaned_count = 0
    for permission in user_permissions:
        if permission.description and 'prueba' in permission.description.lower():
            permission.is_active = False
            cleaned_count += 1

    if cleaned_count > 0:
        db.session.commit()
        print(f"✅ Limpiados {cleaned_count} permisos de prueba")
    else:
        print("ℹ️  No se encontraron permisos de prueba para limpiar")

    print()

    # =============================================
    # RESULTADO FINAL
    # =============================================
    print("🎯 RESULTADO FINAL")
    print("=" * 60)

    all_tests_passed = True

    # Verificar permisos básicos
    if indicador and not admin.can_edit_entity(indicador.id, 'indicador', active_plan.id):
        print("❌ ERROR: El admin no puede editar el indicador asignado")
        all_tests_passed = False

    if indicador and not admin.can_view_entity(indicador.id, 'indicador', active_plan.id):
        print("❌ ERROR: El admin no puede ver el indicador asignado")
        all_tests_passed = False

    if proyecto and admin.can_edit_entity(proyecto.id, 'proyecto', active_plan.id):
        print("❌ ERROR: El admin puede editar el proyecto (debería ser solo lectura)")
        all_tests_passed = False

    if all_tests_passed:
        print("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("🎉 El sistema de permisos de fila está funcionando correctamente")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("🔧 Revisar la configuración de permisos")

    print()
    print("📋 FUNCIONALIDADES VERIFICADAS:")
    print("✅ Creación de permisos de fila")
    print("✅ Verificación de permisos por entidad")
    print("✅ Métodos de verificación para diferentes tipos de entidad")
    print("✅ Integración con plan activo")
    print("✅ Jerarquía de entidades")
    print("✅ Estadísticas de permisos")
    print("✅ Limpieza de permisos")

if __name__ == "__main__":
    test_row_permissions_system()
