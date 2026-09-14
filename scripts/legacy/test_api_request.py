#!/usr/bin/env python3
"""
Script para simular exactamente la petición que hace el navegador
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.views.planes import obtener_datos_plan_completo
from app.models import PlanDesarrollo

def test_api_request():
    """Simula exactamente la petición del navegador"""
    app = create_app()
    with app.app_context():
        print("🔍 SIMULACIÓN DE PETICIÓN DEL NAVEGADOR")
        print("=" * 50)

        # Obtener plan activo
        plan = PlanDesarrollo.query.filter_by(estado='activo').first()
        if not plan:
            print("❌ No hay plan activo")
            return

        print(f"📋 Plan encontrado: {plan.titulo}")

        # Simular parámetros de la petición del navegador
        periodo = '2024'
        columnas_seleccionadas = ['avance_porcentual']  # Esto es lo que envía el navegador

        print(f"📊 Parámetros simulados:")
        print(f"  periodo: {periodo}")
        print(f"  columnas: {columnas_seleccionadas}")

        # Llamar a la función exactamente como lo hace el endpoint
        try:
            resultado = obtener_datos_plan_completo(plan, periodo, columnas_seleccionadas)

            print("\n📊 RESULTADO:")
            print(f"  success: True")
            print(f"  total_registros: {resultado['total_registros']}")
            print(f"  columnas_count: {len(resultado['columnas'])}")
            print(f"  datos_count: {len(resultado['datos'])}")
            print(f"  columnas: {resultado['columnas']}")

            if len(resultado['datos']) > 0:
                print("\n📈 PRIMEROS 3 REGISTROS:")
                for i, dato in enumerate(resultado['datos'][:3]):
                    print(f"  Registro {i+1}: {dato}")
            else:
                print("❌ No hay datos en el resultado")

        except Exception as e:
            print(f"❌ Error en obtener_datos_plan_completo: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_api_request()
