#!/usr/bin/env python3
"""
Script para verificar el contenido de la base de datos
"""

import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    User, PlanDesarrollo, LineaEstrategica, Componente, Programa, Proyecto,
    Actividad, IndicadorProducto, EjecucionTrimestral
)

def check_database():
    """Verifica el contenido actual de la base de datos"""
    app = create_app()
    app.app_context().push()

    print("🔍 VERIFICANDO CONTENIDO DE LA BASE DE DATOS")
    print("=" * 60)

    # Verificar usuarios
    users = User.query.all()
    print(f"👥 Usuarios: {len(users)}")
    for user in users:
        print(f"  - {user.username} ({user.email}) - {user.municipality}")
    print()

    # Verificar planes de desarrollo
    plans = PlanDesarrollo.query.all()
    print(f"📋 Planes de Desarrollo: {len(plans)}")
    for plan in plans:
        print(f"  - {plan.titulo} ({plan.anio_inicio}-{plan.anio_fin}) - Estado: {plan.estado}")
        print(f"    Municipio: {plan.municipio.municipality if plan.municipio else 'N/A'}")
    print()

    # Verificar líneas estratégicas
    lineas = LineaEstrategica.query.all()
    print(f"📍 Líneas Estratégicas: {len(lineas)}")
    for linea in lineas:
        print(f"  - {linea.cod_linea}: {linea.nombre}")
        print(f"    Plan: {linea.plan.titulo if linea.plan else 'N/A'}")
    print()

    # Verificar componentes
    componentes = Componente.query.all()
    print(f"🧩 Componentes: {len(componentes)}")
    for componente in componentes:
        print(f"  - {componente.cod_componente}: {componente.nombre}")
        print(f"    Línea: {componente.linea_estrategica.nombre if componente.linea_estrategica else 'N/A'}")
    print()

    # Verificar programas
    programas = Programa.query.all()
    print(f"📁 Programas: {len(programas)}")
    for programa in programas:
        print(f"  - {programa.cod_programa}: {programa.nombre}")
        print(f"    Componente: {programa.componente.nombre if programa.componente else 'N/A'}")
    print()

    # Verificar proyectos
    proyectos = Proyecto.query.all()
    print(f"🎯 Proyectos: {len(proyectos)}")
    for proyecto in proyectos:
        print(f"  - {proyecto.nombre[:50]}...")
        print(f"    Programa: {proyecto.programa.nombre if proyecto.programa else 'N/A'}")
        print(f"    Estado: {proyecto.estado}")
    print()

    # Verificar indicadores
    indicadores = IndicadorProducto.query.all()
    print(f"📊 Indicadores: {len(indicadores)}")
    for indicador in indicadores[:5]:  # Mostrar solo los primeros 5
        print(f"  - {indicador.cod_indicador}: {indicador.nombre[:40]}...")
        print(f"    Proyecto: {indicador.proyecto.nombre[:30] if indicador.proyecto else 'N/A'}...")
        print(f"    Meta 2024: {indicador.meta_2024}")
    if len(indicadores) > 5:
        print(f"  ... y {len(indicadores) - 5} más")
    print()

    # Verificar ejecuciones
    ejecuciones = EjecucionTrimestral.query.all()
    print(f"📈 Ejecuciones Trimestrales: {len(ejecuciones)}")
    if ejecuciones:
        # Mostrar estadísticas por año y trimestre
        anios = {}
        for ejec in ejecuciones:
            key = f"{ejec.anio}-T{ejec.trimestre}"
            if key not in anios:
                anios[key] = 0
            anios[key] += 1

        print("  Estadísticas por período:")
        for periodo, count in sorted(anios.items()):
            print(f"    {periodo}: {count} registros")
    print()

    # Verificar actividades
    actividades = Actividad.query.all()
    print(f"✅ Actividades: {len(actividades)}")
    for actividad in actividades[:3]:  # Mostrar solo las primeras 3
        print(f"  - {actividad.nombre[:40]}...")
        print(f"    Proyecto: {actividad.proyecto.nombre[:30] if actividad.proyecto else 'N/A'}...")
    if len(actividades) > 3:
        print(f"  ... y {len(actividades) - 3} más")
    print()

    # Resumen total
    print("📊 RESUMEN TOTAL:")
    print("=" * 60)
    total_registros = (
        len(users) + len(plans) + len(lineas) + len(componentes) +
        len(programas) + len(proyectos) + len(actividades) +
        len(indicadores) + len(ejecuciones)
    )

    print(f"Total de registros en BD: {total_registros}")
    print(f"- Usuarios: {len(users)}")
    print(f"- Planes: {len(plans)}")
    print(f"- Líneas: {len(lineas)}")
    print(f"- Componentes: {len(componentes)}")
    print(f"- Programas: {len(programas)}")
    print(f"- Proyectos: {len(proyectos)}")
    print(f"- Actividades: {len(actividades)}")
    print(f"- Indicadores: {len(indicadores)}")
    print(f"- Ejecuciones: {len(ejecuciones)}")

if __name__ == "__main__":
    check_database()
