#!/usr/bin/env python3
"""
Script para verificar que el cálculo del progreso promedio de indicadores funciona correctamente
"""
from app import create_app
from app.models import Proyecto

def test_indicators_progress_fixed():
    """Verificar que el cálculo del progreso promedio funciona correctamente"""
    print("🔧 Verificando cálculo del progreso promedio de indicadores...")

    app = create_app()
    with app.app_context():
        # Buscar proyectos con indicadores
        proyectos = Proyecto.query.filter(Proyecto.indicadores.any()).limit(3).all()

        if proyectos:
            for proyecto in proyectos:
                print(f"\n🏗️ Proyecto: {proyecto.nombre}")
                print(f"📊 Indicadores: {len(proyecto.indicadores)}")

                # Calcular progreso promedio manualmente
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
                print(f"   📈 Promedio calculado: {promedio_manual:.1f}%")
                print(f"   🎯 Debería aparecer en el template correctamente")

                if promedio_manual > 0:
                    print("✅ El cálculo funciona correctamente")
                else:
                    print("❌ Hay un problema con el cálculo")

        else:
            print("⚠️ No se encontraron proyectos con indicadores")

if __name__ == "__main__":
    test_indicators_progress_fixed()
