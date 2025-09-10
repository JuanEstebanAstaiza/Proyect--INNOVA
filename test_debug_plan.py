#!/usr/bin/env python3
"""
Script de diagnóstico para verificar el estado del plan y sus relaciones
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    PlanDesarrollo, LineaEstrategica, Componente,
    Programa, Proyecto, IndicadorProducto, EjecucionTrimestral
)

def diagnosticar_plan(plan_id):
    """Diagnóstico completo del plan y sus relaciones"""

    print("🔍 DIAGNÓSTICO DEL PLAN DE DESARROLLO")
    print("=" * 50)

    # Verificar plan
    plan = PlanDesarrollo.query.get(plan_id)
    if not plan:
        print(f"❌ Plan con ID {plan_id} no encontrado")
        return

    print(f"📋 Plan encontrado:")
    print(f"   ID: {plan.id}")
    print(f"   Título: {plan.titulo}")
    print(f"   Estado: {plan.estado}")
    print(f"   Usuario: {plan.municipio.username if plan.municipio else 'N/A'}")
    print()

    # Verificar líneas estratégicas
    print("🏗️ LÍNEAS ESTRATÉGICAS:")
    print("-" * 30)

    lineas = plan.lineas_estrategicas
    print(f"Total de líneas: {len(lineas)}")

    for i, linea in enumerate(lineas, 1):
        print(f"{i}. {linea.nombre} (ID: {linea.id}, Estado: {linea.estado})")

        # Verificar componentes de la línea
        componentes = getattr(linea, 'componentes', [])
        print(f"   └─ Componentes: {len(componentes)}")

        for j, componente in enumerate(componentes, 1):
            print(f"      {j}. {componente.nombre} (ID: {componente.id}, Estado: {componente.estado})")

            # Verificar programas del componente
            programas = getattr(componente, 'programas', [])
            print(f"         └─ Programas: {len(programas)}")

            for k, programa in enumerate(programas, 1):
                print(f"            {k}. {programa.nombre} (ID: {programa.id}, Estado: {programa.estado})")

                # Verificar proyectos del programa
                proyectos = getattr(programa, 'proyectos', [])
                print(f"               └─ Proyectos: {len(proyectos)}")

                for l, proyecto in enumerate(proyectos, 1):
                    print(f"                  {l}. {proyecto.nombre} (ID: {proyecto.id}, Estado: {proyecto.estado})")

                    # Verificar indicadores del proyecto
                    indicadores = getattr(proyecto, 'indicadores', [])
                    print(f"                     └─ Indicadores: {len(indicadores)}")

                    for m, indicador in enumerate(indicadores, 1):
                        ejecuciones = getattr(indicador, 'ejecuciones_trimestrales', [])
                        print(f"                        {m}. {indicador.nombre}")
                        print(f"                           ID: {indicador.id}, Estado: {indicador.estado}")
                        print(f"                           Ejecuciones: {len(ejecuciones)}")
                        print(f"                           Meta 2024: {indicador.meta_2024}")
                        print()

    print("\n" + "=" * 50)
    print("✅ DIAGNÓSTICO COMPLETADO")

    # Intentar ejecutar la función de obtención de datos
    print("\n🔄 PROBANDO FUNCIÓN obtener_datos_plan_completo...")
    try:
        from app.views.planes import obtener_datos_plan_completo
        resultado = obtener_datos_plan_completo(plan, '2024', None)
        print("✅ Función ejecutada correctamente")
        print(f"📊 Registros obtenidos: {len(resultado['datos'])}")
        print(f"📋 Columnas: {len(resultado['columnas'])}")
        if 'error' in resultado:
            print(f"⚠️ Error reportado: {resultado['error']}")
    except Exception as e:
        print(f"❌ Error al ejecutar función: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python test_debug_plan.py <plan_id>")
        sys.exit(1)

    plan_id = int(sys.argv[1])

    app = create_app()
    with app.app_context():
        diagnosticar_plan(plan_id)
