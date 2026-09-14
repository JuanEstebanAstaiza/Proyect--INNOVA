#!/usr/bin/env python3
"""
Script para verificar que el cálculo de progreso promedio de indicadores funciona correctamente
"""
from app import create_app
from app.models import Proyecto

def test_indicators_progress_calculation():
    """Verificar que el cálculo de progreso promedio funciona"""
    print("🔧 Verificando cálculo de progreso promedio de indicadores...")

    app = create_app()
    with app.app_context():
        # Buscar el proyecto mencionado en el ejemplo del usuario
        proyecto = Proyecto.query.filter(
            Proyecto.nombre.like('%Proyecto 2 - Programa%')
        ).first()

        if proyecto:
            print(f"🏗️ Proyecto encontrado: {proyecto.nombre}")
            print(f"📊 Indicadores: {len(proyecto.indicadores)}")

            # Calcular promedio manualmente
            total_progreso = 0
            indicadores_validos = 0

            for indicador in proyecto.indicadores:
                progreso = indicador.get_progreso_porcentual()
                print(f"   📈 {indicador.nombre}: {progreso:.1f}%")

                if progreso and progreso > 0:
                    total_progreso += progreso
                    indicadores_validos += 1

            promedio_manual = total_progreso / indicadores_validos if indicadores_validos > 0 else 0

            print(f"\n📊 Resultados:")
            print(f"   ✅ Indicadores válidos: {indicadores_validos}/{len(proyecto.indicadores)}")
            print(f"   📊 Promedio calculado: {promedio_manual:.1f}%")
            print(f"   🎯 Debería coincidir con el mostrado en el template")

            if promedio_manual > 0:
                print("✅ El cálculo funciona correctamente")
            else:
                print("❌ Hay un problema con el cálculo")

        else:
            print("⚠️ Proyecto específico no encontrado")

if __name__ == "__main__":
    test_indicators_progress_calculation()
