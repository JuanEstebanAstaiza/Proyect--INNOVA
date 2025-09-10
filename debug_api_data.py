#!/usr/bin/env python3
"""
Script de debug detallado para verificar qué está pasando con la función obtener_datos_plan_completo
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import PlanDesarrollo, IndicadorProducto

def debug_obtener_datos():
    """Debug detallado de la función obtener_datos_plan_completo"""
    app = create_app()
    with app.app_context():
        print("🔍 DEBUG DETALLADO DE obtener_datos_plan_completo")
        print("=" * 60)

        # Obtener plan activo
        plan = PlanDesarrollo.query.filter_by(estado='activo').first()
        if not plan:
            print("❌ No hay plan activo")
            return

        print(f"📋 Plan encontrado: {plan.titulo} (ID: {plan.id})")

        # Verificar líneas estratégicas
        lineas_count = len(plan.lineas_estrategicas)
        print(f"🏗️ Líneas estratégicas: {lineas_count}")

        if lineas_count == 0:
            print("❌ El plan no tiene líneas estratégicas")
            return

        # Obtener indicadores
        indicadores_plan = IndicadorProducto.query.filter(IndicadorProducto.estado.in_(['activo', 'en_ejecucion'])).all()
        print(f"📊 Total indicadores en BD: {len(indicadores_plan)}")

        # Procesar una línea estratégica como ejemplo
        linea = plan.lineas_estrategicas[0]  # Primera línea
        print(f"\n📍 Procesando línea estratégica: {linea.nombre} (Estado: {linea.estado})")

        if linea.estado not in ['activo', 'en_ejecucion']:
            print(f"❌ Línea no operativa: {linea.estado}")
            return

        # Verificar componentes
        componentes_count = len(linea.componentes)
        print(f"🏛️ Componentes en línea: {componentes_count}")

        if componentes_count == 0:
            print("❌ La línea no tiene componentes")
            return

        # Procesar primer componente
        componente = linea.componentes[0]
        print(f"🏛️ Procesando componente: {componente.nombre} (Estado: {componente.estado})")

        if componente.estado not in ['activo', 'en_ejecucion']:
            print(f"❌ Componente no operativo: {componente.estado}")
            return

        # Verificar programas
        programas_count = len(componente.programas)
        print(f"📋 Programas en componente: {programas_count}")

        if programas_count == 0:
            print("❌ El componente no tiene programas")
            return

        # Procesar primer programa
        programa = componente.programas[0]
        print(f"📋 Procesando programa: {programa.nombre} (Estado: {programa.estado})")

        if programa.estado not in ['activo', 'en_ejecucion']:
            print(f"❌ Programa no operativo: {programa.estado}")
            return

        # Verificar proyectos
        proyectos_count = len(programa.proyectos)
        print(f"📁 Proyectos en programa: {proyectos_count}")

        if proyectos_count == 0:
            print("❌ El programa no tiene proyectos")
            return

        # Procesar primer proyecto
        proyecto = programa.proyectos[0]
        print(f"📁 Procesando proyecto: {proyecto.nombre} (Estado: {proyecto.estado})")

        if proyecto.estado not in ['activo', 'en_ejecucion']:
            print(f"❌ Proyecto no operativo: {proyecto.estado}")
            return

        # Verificar indicadores del proyecto
        indicadores_proyecto = [ind for ind in proyecto.indicadores if ind.estado in ['activo', 'en_ejecucion']]
        print(f"📊 Indicadores en proyecto: {len(indicadores_proyecto)}")

        if len(indicadores_proyecto) == 0:
            print("❌ El proyecto no tiene indicadores operativos")
            return

        # Procesar primer indicador
        indicador = indicadores_proyecto[0]
        print(f"📊 Procesando indicador: {indicador.nombre} (ID: {indicador.id}, Estado: {indicador.estado})")

        # Verificar ejecuciones
        try:
            ejecuciones = indicador.get_ejecuciones_por_anio(2024)
            print(f"📅 Ejecuciones en 2024: {len(ejecuciones)}")

            for ejec in ejecuciones[:3]:  # Mostrar primeras 3
                print(f"  Q{ejec.trimestre}: {ejec.ejecucion_trimestral}")

            # Verificar última ejecución
            ultima = indicador.get_ultima_ejecucion()
            if ultima:
                print(f"📈 Última ejecución acumulada: {ultima.ejecucion_acumulada}")
            else:
                print("❌ No hay última ejecución")

            # Verificar progreso
            progreso = indicador.get_progreso_porcentual()
            print(f"📊 Progreso porcentual: {progreso}")

        except Exception as e:
            print(f"❌ Error procesando ejecuciones: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_obtener_datos()
