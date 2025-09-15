#!/usr/bin/env python3
"""
Script para diagnosticar el problema con los indicadores y su progreso
"""
from app import create_app
from app.models import Proyecto, IndicadorProducto, EjecucionTrimestral

def debug_indicadores():
    """Diagnosticar el problema con los indicadores"""
    print("🔧 Diagnosticando problema con indicadores...")

    app = create_app()
    with app.app_context():
        # Buscar proyectos con indicadores
        proyectos = Proyecto.query.filter(Proyecto.indicadores.any()).all()

        print(f"📊 Proyectos encontrados: {len(proyectos)}")

        for proyecto in proyectos:
            print(f"\n🏗️ Proyecto: {proyecto.nombre}")
            print(f"   📈 Indicadores: {len(proyecto.indicadores)}")

            total_progreso = 0
            indicadores_validos = 0

            for indicador in proyecto.indicadores:
                print(f"\n   📊 Indicador: {indicador.nombre}")
                print(f"      🆔 ID: {indicador.id}")
                print(f"      🎯 Meta cuatrienio: {indicador.meta_cuatrienio}")
                print(f"      📍 Línea base: {indicador.linea_base}")

                # Obtener ejecuciones
                ejecuciones = indicador.get_ejecuciones_por_anio(2024)
                print(f"      📋 Ejecuciones 2024: {len(ejecuciones)}")

                if ejecuciones:
                    for ejec in sorted(ejecuciones, key=lambda x: x.trimestre):
                        print(f"         T{ejec.trimestre}: {ejec.ejecucion_acumulada}")

                # Calcular progreso
                progreso = indicador.get_progreso_porcentual()
                print(f"      📊 Progreso calculado: {progreso}%")

                # Verificar la última ejecución
                ultima_ejecucion = indicador.get_ultima_ejecucion()
                if ultima_ejecucion:
                    print(f"      📅 Última ejecución: T{ultima_ejecucion.trimestre} {ultima_ejecucion.anio}")
                    print(f"         Valor acumulado: {ultima_ejecucion.ejecucion_acumulada}")
                else:
                    print("      ❌ No tiene última ejecución")

                if progreso > 0:
                    total_progreso += progreso
                    indicadores_validos += 1

            # Calcular promedio
            if indicadores_validos > 0:
                promedio_real = total_progreso / indicadores_validos
                print(f"\n   📊 Promedio real: {promedio_real:.1f}%")
                print(f"   ✅ Indicadores válidos: {indicadores_validos}/{len(proyecto.indicadores)}")
            else:
                print(f"\n   ❌ No hay indicadores con progreso válido")

if __name__ == "__main__":
    debug_indicadores()
