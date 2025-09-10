#!/usr/bin/env python3
"""
Script específico para diagnosticar el problema de indicadores
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    PlanDesarrollo, LineaEstrategica, Componente,
    Programa, Proyecto, IndicadorProducto
)

def diagnosticar_indicadores(plan_id):
    """Diagnóstico específico de indicadores"""

    print("🔍 DIAGNÓSTICO DE INDICADORES")
    print("=" * 50)

    # Verificar plan
    plan = PlanDesarrollo.query.get(plan_id)
    if not plan:
        print(f"❌ Plan con ID {plan_id} no encontrado")
        return

    print(f"📋 Plan: {plan.titulo}")

    # Verificar indicadores en la base de datos
    from app.models import IndicadorProducto
    total_indicadores = IndicadorProducto.query.count()
    indicadores_activos = IndicadorProducto.query.filter_by(estado='activo').count()

    print("\n📊 INDICADORES EN BASE DE DATOS:")
    print(f"   Total: {total_indicadores}")
    print(f"   Activos: {indicadores_activos}")

    if total_indicadores == 0:
        print("❌ No hay indicadores en la base de datos")
        return

    # Verificar algunos indicadores
    print("\n🔍 MUESTRA DE INDICADORES:")
    indicadores_muestra = IndicadorProducto.query.limit(10).all()
    for i, indicador in enumerate(indicadores_muestra, 1):
        proyecto = indicador.proyecto if hasattr(indicador, 'proyecto') and indicador.proyecto else None
        print(f"   {i}. {indicador.nombre}")
        print(f"      ID: {indicador.id}")
        print(f"      Estado: {indicador.estado}")
        print(f"      Proyecto ID: {indicador.proyecto_id}")
        print(f"      Proyecto: {proyecto.nombre if proyecto else 'SIN PROYECTO'}")
        print(f"      Meta 2024: {indicador.meta_2024}")
        print()

    # Verificar proyectos con indicadores
    print("🏗️ ANÁLISIS DE PROYECTOS:")
    proyectos_con_indicadores = 0
    proyectos_sin_indicadores = 0
    total_proyectos = 0

    for proyecto in Proyecto.query.all():
        total_proyectos += 1
        indicadores_proyecto = IndicadorProducto.query.filter_by(proyecto_id=proyecto.id).count()
        if indicadores_proyecto > 0:
            proyectos_con_indicadores += 1
            print(f"   ✅ Proyecto '{proyecto.nombre}' (ID: {proyecto.id}) tiene {indicadores_proyecto} indicadores")
        else:
            proyectos_sin_indicadores += 1

    print("\n📊 ESTADÍSTICAS DE PROYECTOS:")
    print(f"   Total proyectos: {total_proyectos}")
    print(f"   Con indicadores: {proyectos_con_indicadores}")
    print(f"   Sin indicadores: {proyectos_sin_indicadores}")

    # Probar la relación desde proyecto a indicadores
    print("\n🔗 PRUEBA DE RELACIONES:")
    proyecto_prueba = Proyecto.query.first()
    if proyecto_prueba:
        print(f"Proyecto de prueba: {proyecto_prueba.nombre} (ID: {proyecto_prueba.id})")

        # Método 1: Usando la relación
        try:
            indicadores_relacion = proyecto_prueba.indicadores
            print(f"   ✅ Relación proyecto.indicadores: {len(indicadores_relacion)} indicadores")
            for indicador in indicadores_relacion[:3]:  # Solo primeros 3
                print(f"      - {indicador.nombre}")
        except Exception as e:
            print(f"   ❌ Error en relación: {e}")

        # Método 2: Consulta directa
        try:
            from sqlalchemy import text
            indicadores_directos = IndicadorProducto.query.filter_by(proyecto_id=proyecto_prueba.id).all()
            print(f"   ✅ Consulta directa: {len(indicadores_directos)} indicadores")
        except Exception as e:
            print(f"   ❌ Error en consulta directa: {e}")

    print("\n" + "=" * 50)
    print("✅ DIAGNÓSTICO COMPLETADO")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python test_indicadores.py <plan_id>")
        sys.exit(1)

    plan_id = int(sys.argv[1])

    app = create_app()
    with app.app_context():
        diagnosticar_indicadores(plan_id)