#!/usr/bin/env python3
"""
Script para actualizar el plan de desarrollo activo con datos sintéticos realistas
"""

import os
import sys

# Permite ejecutar este script desde cualquier directorio: anade la raiz del
# proyecto al sys.path para poder importar el paquete `app`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# La consola de Windows usa cp1252 y no puede imprimir acentos ni simbolos.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, 'reconfigure'):
        _stream.reconfigure(encoding='utf-8', errors='replace')

import random
from datetime import date

from app import create_app
from app.models import (
    Actividad,
    Componente,
    EjecucionTrimestral,
    IndicadorProducto,
    LineaEstrategica,
    PlanDesarrollo,
    Programa,
    Proyecto,
)


def update_active_plan_data():
    """REHACER completamente el plan de desarrollo activo con datos realistas"""

    print("🚀 Iniciando REHACER completo del plan de desarrollo activo...")

    app = create_app()
    with app.app_context():
        from app import db

        # Encontrar el plan activo
        plan = PlanDesarrollo.query.filter_by(estado='activo').first()
        if not plan:
            print("❌ No se encontró un plan activo")
            return

        print(f"📋 Plan encontrado: {plan.titulo}")
        print(f"📅 Período: {plan.anio_inicio}-{plan.anio_fin}")
        print("🗑️  Eliminando datos existentes...")

        # Eliminar TODOS los datos relacionados con el plan de manera ordenada (de abajo hacia arriba)
        try:
            # Obtener todas las líneas estratégicas del plan
            lineas = LineaEstrategica.query.filter_by(plan_id=plan.id).all()

            for linea in lineas:
                print(f"  Eliminando línea estratégica: {linea.nombre}")

                for componente in linea.componentes:
                    print(f"    Eliminando componente: {componente.nombre}")

                    for programa in componente.programas:
                        print(f"      Eliminando programa: {programa.nombre}")

                        for proyecto in programa.proyectos:
                            print(f"        Eliminando proyecto: {proyecto.nombre}")

                            # Eliminar ejecuciones trimestrales del proyecto
                            for indicador in proyecto.indicadores:
                                ejecuciones = EjecucionTrimestral.query.filter_by(indicador_id=indicador.id).all()
                                for ejecucion in ejecuciones:
                                    db.session.delete(ejecucion)

                            # Eliminar indicadores y actividades
                            for indicador in proyecto.indicadores:
                                db.session.delete(indicador)

                            for actividad in proyecto.actividades:
                                db.session.delete(actividad)

                            db.session.delete(proyecto)

                        db.session.delete(programa)

                    db.session.delete(componente)

                db.session.delete(linea)

            db.session.commit()
            print("✅ Todos los datos existentes eliminados correctamente")

        except Exception as e:
            print(f"❌ Error al eliminar datos existentes: {e}")
            db.session.rollback()
            return

        # Definir líneas estratégicas realistas
        lineas_data = [
            {
                'cod_linea': 1,
                'nombre': 'Desarrollo Económico Sostenible',
                'descripcion': 'Promover el crecimiento económico inclusivo y sostenible mediante el fortalecimiento de sectores productivos locales',
                'prioridad': 'critica',
                'presupuesto_base': 25000000  # $25M
            },
            {
                'cod_linea': 2,
                'nombre': 'Infraestructura y Servicios Básicos',
                'descripcion': 'Mejorar la calidad de vida mediante la expansión y mantenimiento de infraestructura esencial',
                'prioridad': 'alta',
                'presupuesto_base': 30000000  # $30M
            },
            {
                'cod_linea': 3,
                'nombre': 'Desarrollo Social e Inclusión',
                'descripcion': 'Fomentar la inclusión social, educación y desarrollo humano integral',
                'prioridad': 'alta',
                'presupuesto_base': 20000000  # $20M
            },
            {
                'cod_linea': 4,
                'nombre': 'Gestión Ambiental y Sostenibilidad',
                'descripcion': 'Proteger el medio ambiente y promover prácticas sostenibles de desarrollo',
                'prioridad': 'media',
                'presupuesto_base': 15000000  # $15M
            }
        ]

        # Actualizar presupuesto total del plan
        plan.presupuesto_total = sum(linea['presupuesto_base'] for linea in lineas_data)
        print(f"💰 Presupuesto total del plan: ${plan.presupuesto_total:,.0f}")

        # Actualizar líneas estratégicas
        for i, linea_data in enumerate(lineas_data):
            if i < len(plan.lineas_estrategicas):
                linea = plan.lineas_estrategicas[i]
            else:
                linea = LineaEstrategica(plan_id=plan.id)

            linea.cod_linea = linea_data['cod_linea']
            linea.nombre = linea_data['nombre']
            linea.descripcion = linea_data['descripcion']
            linea.prioridad = linea_data['prioridad']
            linea.presupuesto_asignado = linea_data['presupuesto_base']
            linea.estado = 'activo'

            if linea not in plan.lineas_estrategicas:
                plan.lineas_estrategicas.append(linea)

            print(f"✅ Línea {linea.cod_linea}: {linea.nombre}")
            print(f"   💰 Presupuesto: ${linea.presupuesto_asignado:,.0f}")

            # Crear componentes para cada línea
            componentes_data = [
                {
                    'cod_componente': float(f"{linea.cod_linea}.{j+1}"),
                    'nombre': f"Componente {j+1} - {linea.nombre[:30]}...",
                    'presupuesto_factor': 0.4 if j == 0 else (0.35 if j == 1 else 0.25)
                } for j in range(2 if linea.cod_linea in [1, 4] else 3)
            ]

            # Actualizar componentes
            for j, comp_data in enumerate(componentes_data):
                if j < len(linea.componentes):
                    componente = linea.componentes[j]
                else:
                    componente = Componente(linea_estrategica_id=linea.id)

                componente.cod_componente = comp_data['cod_componente']
                componente.nombre = comp_data['nombre']
                componente.prioridad = linea.prioridad
                componente.presupuesto_asignado = int(linea.presupuesto_asignado * comp_data['presupuesto_factor'])
                componente.estado = 'activo'

                if componente not in linea.componentes:
                    linea.componentes.append(componente)

                print(f"   🏭 Componente {componente.cod_componente}: {componente.nombre}")
                print(f"      💰 Presupuesto: ${componente.presupuesto_asignado:,.0f}")

                # Crear programas para cada componente
                programas_data = [
                    {
                        'cod_programa': f"PDM-{int(componente.cod_componente*10):02d}-{k+1}",
                        'nombre': f"Programa {k+1} - {componente.nombre[:25]}...",
                        'bpim': f"BPIM-{random.randint(100, 999)}",
                        'presupuesto_factor': 0.6 if k == 0 else 0.4
                    } for k in range(1 if componente.cod_componente in [1.1, 2.1, 3.1] else 2)
                ]

                # Actualizar programas
                for k, prog_data in enumerate(programas_data):
                    if k < len(componente.programas):
                        programa = componente.programas[k]
                    else:
                        programa = Programa(componente_id=componente.id)

                    programa.cod_programa = prog_data['cod_programa']
                    programa.nombre = prog_data['nombre']
                    programa.dependencia_responsable = f"Secretaría {random.choice(['de Planeación', 'de Hacienda', 'de Desarrollo', 'de Infraestructura'])}"
                    programa.bpim = prog_data['bpim']
                    programa.presupuesto_asignado = int(componente.presupuesto_asignado * prog_data['presupuesto_factor'])
                    programa.estado = 'activo'

                    if programa not in componente.programas:
                        componente.programas.append(programa)

                    print(f"      📋 Programa {programa.cod_programa}: {programa.nombre}")
                    print(f"         💰 Presupuesto: ${programa.presupuesto_asignado:,.0f}")

                    # Crear proyectos para cada programa
                    proyectos_data = [
                        {
                            'nombre': f"Proyecto {m+1} - {programa.nombre[:20]}...",
                            'presupuesto_factor': 0.5 if m == 0 else (0.3 if m == 1 else 0.2),
                            'estado': random.choice(['en_ejecucion', 'completado', 'planificado'])
                        } for m in range(2 if programa.cod_programa.endswith('-1') else 3)
                    ]

                    # Actualizar proyectos
                    for m, proy_data in enumerate(proyectos_data):
                        if m < len(programa.proyectos):
                            proyecto = programa.proyectos[m]
                        else:
                            proyecto = Proyecto(programa_id=programa.id)

                        proyecto.nombre = proy_data['nombre']
                        proyecto.descripcion = f"Descripción detallada del {proy_data['nombre']}"
                        proyecto.estado = proy_data['estado']
                        proyecto.presupuesto_total = int(programa.presupuesto_asignado * proy_data['presupuesto_factor'])
                        proyecto.presupuesto_ejecutado = int(proyecto.presupuesto_total * random.uniform(0.1, 0.9)) if proyecto.estado in ['en_ejecucion', 'completado'] else 0
                        proyecto.fecha_inicio = date(2024, random.randint(1, 6), random.randint(1, 28))
                        proyecto.fecha_fin = date(2025, random.randint(7, 12), random.randint(1, 28))
                        proyecto.ubicacion = f"Barrio {random.choice(['Centro', 'Norte', 'Sur', 'Oriente', 'Poniente'])}"
                        proyecto.sector = random.choice(['Infraestructura', 'Educación', 'Salud', 'Medio Ambiente', 'Desarrollo Económico'])

                        if proyecto not in programa.proyectos:
                            programa.proyectos.append(proyecto)

                        print(f"         🏗️ Proyecto: {proyecto.nombre}")
                        print(f"            💰 Presupuesto: ${proyecto.presupuesto_total:,.0f}")
                        print(f"            📊 Estado: {proyecto.estado}")

                        # Crear indicadores para cada proyecto
                        indicadores_data = [
                            {
                                'cod_indicador': f"IND-{int(proyecto.programa.componente.cod_componente*100):03d}-{n+1}",
                                'nombre': f"Indicador {n+1} - {random.choice(['Cobertura', 'Eficiencia', 'Calidad', 'Satisfacción', 'Alcance'])} del Proyecto",
                                'tipo_indicador': random.choice(['proceso', 'resultado', 'impacto']),
                                'sentido': random.choice(['positivo', 'positivo', 'positivo', 'negativo']),
                                'unidad': random.choice(['%', 'personas', 'km', 'unidades', 'servicios'])
                            } for n in range(2 if proyecto.nombre.endswith('...') else 3)
                        ]

                        # Actualizar indicadores
                        for n, ind_data in enumerate(indicadores_data):
                            if n < len(proyecto.indicadores):
                                indicador = proyecto.indicadores[n]
                            else:
                                indicador = IndicadorProducto(proyecto_id=proyecto.id)

                            indicador.cod_indicador = ind_data['cod_indicador']
                            indicador.nombre = ind_data['nombre']
                            indicador.descripcion = f"Indicador de medición para {ind_data['nombre']}"
                            indicador.tipo_indicador = ind_data['tipo_indicador']
                            indicador.sentido = ind_data['sentido']
                            indicador.unidad = ind_data['unidad']
                            indicador.linea_base = random.uniform(10, 50)
                            indicador.meta_cuatrienio = random.uniform(70, 150)  # Aumenté el rango para tener metas más grandes
                            indicador.meta_2024 = indicador.meta_cuatrienio * 0.25
                            indicador.estado = 'activo'

                            if indicador not in proyecto.indicadores:
                                proyecto.indicadores.append(indicador)

                            # Crear ejecuciones trimestrales con metas y ejecuciones realistas
                            meta_trimestral = indicador.meta_2024 / 4

                            ejecucion_acumulada = indicador.linea_base
                            for trimestre in range(1, 5):
                                ejecucion = EjecucionTrimestral.query.filter_by(
                                    indicador_id=indicador.id,
                                    anio=2024,
                                    trimestre=trimestre
                                ).first()

                                if not ejecucion:
                                    ejecucion = EjecucionTrimestral(
                                        indicador_id=indicador.id,
                                        anio=2024,
                                        trimestre=trimestre,
                                        usuario_id=1  # Usuario administrador por defecto
                                    )

                                # Calcular la meta trimestral (25% del año)
                                ejecucion.meta_trimestral = meta_trimestral

                                # Calcular la ejecución trimestral con variación realista
                                if trimestre == 1:
                                    # Para T1, la ejecución es desde la línea base
                                    ejecucion_trimestral = meta_trimestral * random.uniform(0.85, 1.15)
                                else:
                                    # Para trimestres siguientes, agregar variación
                                    ejecucion_trimestral = meta_trimestral * random.uniform(0.90, 1.10)

                                # Acumular la ejecución
                                ejecucion_acumulada += ejecucion_trimestral
                                ejecucion.ejecucion_acumulada = ejecucion_acumulada

                                # Calcular cumplimiento trimestral
                                cumplimiento_trimestral = (ejecucion_trimestral / meta_trimestral) * 100
                                ejecucion.cumplimiento_trimestral = cumplimiento_trimestral

                                # Fecha de medición
                                mes = trimestre * 3
                                if mes > 12:
                                    mes = 12
                                ejecucion.fecha_medicion = date(2024, mes, random.randint(1, 28))

                                if ejecucion not in indicador.ejecuciones_trimestrales:
                                    indicador.ejecuciones_trimestrales.append(ejecucion)

                        # Crear actividades para cada proyecto
                        actividades_data = [
                            {
                                'nombre': f"Actividad {o+1} - {random.choice(['Planificación', 'Ejecución', 'Seguimiento', 'Evaluación', 'Capacitación'])}",
                                'tipo_actividad': random.choice(['construcción', 'capacitación', 'compra', 'consultoría', 'supervisión']),
                                'estado': random.choice(['planificada', 'en_progreso', 'completada']),
                                'prioridad': random.choice(['media', 'alta', 'media'])
                            } for o in range(3 if proyecto.nombre.endswith('...') else 4)
                        ]

                        # Actualizar actividades
                        for o, act_data in enumerate(actividades_data):
                            if o < len(proyecto.actividades):
                                actividad = proyecto.actividades[o]
                            else:
                                actividad = Actividad(proyecto_id=proyecto.id)

                            actividad.nombre = act_data['nombre']
                            actividad.descripcion = f"Descripción de {act_data['nombre']}"
                            actividad.tipo_actividad = act_data['tipo_actividad']
                            actividad.estado = act_data['estado']
                            actividad.prioridad = act_data['prioridad']
                            actividad.presupuesto_asignado = int(proyecto.presupuesto_total * random.uniform(0.1, 0.3) / len(actividades_data))
                            actividad.presupuesto_ejecutado = int(actividad.presupuesto_asignado * random.uniform(0.1, 0.9)) if actividad.estado == 'completada' else 0
                            actividad.progreso_porcentual = random.uniform(10, 100) if actividad.estado in ['en_progreso', 'completada'] else 0

                            if actividad not in proyecto.actividades:
                                proyecto.actividades.append(actividad)

        # Guardar todos los cambios
        try:
            from app import db
            db.session.commit()
            print("✅ Todos los datos del plan han sido actualizados exitosamente!")
            print("📊 Resumen final:")
            print(f"   📋 Líneas estratégicas: {len(plan.lineas_estrategicas)}")
            print(f"   🏭 Componentes totales: {sum(len(linea.componentes) for linea in plan.lineas_estrategicas)}")
            print(f"   📋 Programas totales: {sum(len(c.programas) for linea in plan.lineas_estrategicas for c in linea.componentes)}")
            print(f"   🏗️ Proyectos totales: {sum(len(p.proyectos) for linea in plan.lineas_estrategicas for c in linea.componentes for p in c.programas)}")
            print(f"   📈 Indicadores totales: {sum(len(p.indicadores) for linea in plan.lineas_estrategicas for c in linea.componentes for pr in c.programas for p in pr.proyectos)}")
            print(f"   ⚙️ Actividades totales: {sum(len(p.actividades) for linea in plan.lineas_estrategicas for c in linea.componentes for pr in c.programas for p in pr.proyectos)}")
            print(f"   💰 Presupuesto total: ${plan.presupuesto_total:,.0f}")

        except Exception as e:
            print(f"❌ Error al guardar los cambios: {e}")
            db.session.rollback()

if __name__ == "__main__":
    update_active_plan_data()
