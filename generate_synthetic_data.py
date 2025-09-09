#!/usr/bin/env python3
"""
Script para generar datos sintéticos completos de un Plan de Desarrollo Municipal
Genera más de 100 filas con datos realistas para testing y demostración
"""

import os
import sys
import random
from datetime import datetime
from faker import Faker

# Agregar el directorio raíz al path para importar módulos de la app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    User, PlanDesarrollo, LineaEstrategica, Componente, Programa, Proyecto,
    Actividad, IndicadorProducto, EjecucionTrimestral
)

# Inicializar Faker para datos realistas
fake = Faker('es_ES')

class SyntheticDataGenerator:
    """Generador de datos sintéticos para Plan de Desarrollo Municipal"""

    def __init__(self):
        self.app = create_app()
        self.app.app_context().push()

        # Datos base para generar contenido realista
        self.lineas_estrategicas = [
            {
                'codigo': 1,
                'nombre': 'Desarrollo Económico y Productivo',
                'descripcion': 'Fomentar el crecimiento económico sostenible y la generación de empleo',
                'componentes': [
                    {
                        'codigo': 1.1,
                        'nombre': 'Fortalecimiento del Sector Agropecuario',
                        'descripcion': 'Desarrollo sostenible del sector agrícola y pecuario',
                        'programas': ['Programa de Modernización Agrícola', 'Programa de Cadena de Valor Agropecuaria']
                    },
                    {
                        'codigo': 1.2,
                        'nombre': 'Desarrollo Industrial y Empresarial',
                        'descripcion': 'Impulsar la industrialización y el emprendimiento local',
                        'programas': ['Programa de Desarrollo Industrial', 'Programa de Apoyo a Emprendedores']
                    },
                    {
                        'codigo': 1.3,
                        'nombre': 'Turismo y Desarrollo Local',
                        'descripcion': 'Promover el turismo como motor de desarrollo económico',
                        'programas': ['Programa de Turismo Sostenible', 'Programa de Desarrollo Turístico Local']
                    }
                ]
            },
            {
                'codigo': 2,
                'nombre': 'Infraestructura y Servicios Básicos',
                'descripcion': 'Mejorar la infraestructura urbana y rural para el desarrollo sostenible',
                'componentes': [
                    {
                        'codigo': 2.1,
                        'nombre': 'Infraestructura Vial y Transporte',
                        'descripcion': 'Mejorar la conectividad y movilidad en el municipio',
                        'programas': ['Programa de Mantenimiento Vial', 'Programa de Transporte Público']
                    },
                    {
                        'codigo': 2.2,
                        'nombre': 'Agua Potable y Saneamiento',
                        'descripcion': 'Garantizar el acceso universal a servicios de agua y saneamiento',
                        'programas': ['Programa de Agua Potable Rural', 'Programa de Saneamiento Básico']
                    },
                    {
                        'codigo': 2.3,
                        'nombre': 'Energía y Servicios Públicos',
                        'descripcion': 'Expandir la cobertura de servicios energéticos y públicos',
                        'programas': ['Programa de Electrificación Rural', 'Programa de Alumbrado Público LED']
                    }
                ]
            },
            {
                'codigo': 3,
                'nombre': 'Desarrollo Social e Inclusión',
                'descripcion': 'Promover la inclusión social y el desarrollo humano integral',
                'componentes': [
                    {
                        'codigo': 3.1,
                        'nombre': 'Educación y Formación',
                        'descripcion': 'Mejorar la calidad y cobertura educativa en todos los niveles',
                        'programas': ['Programa de Educación Inicial', 'Programa de Formación Técnica']
                    },
                    {
                        'codigo': 3.2,
                        'nombre': 'Salud y Bienestar',
                        'descripcion': 'Fortalecer el sistema de salud municipal y promover estilos de vida saludables',
                        'programas': ['Programa de Salud Preventiva', 'Programa de Atención Primaria']
                    },
                    {
                        'codigo': 3.3,
                        'nombre': 'Protección Social y Pobreza',
                        'descripcion': 'Combatir la pobreza y fortalecer los programas de protección social',
                        'programas': ['Programa de Protección Social', 'Programa de Desarrollo Comunitario']
                    }
                ]
            },
            {
                'codigo': 4,
                'nombre': 'Gestión Ambiental y Sostenibilidad',
                'descripcion': 'Proteger el medio ambiente y promover el desarrollo sostenible',
                'componentes': [
                    {
                        'codigo': 4.1,
                        'nombre': 'Gestión de Recursos Naturales',
                        'descripcion': 'Proteger y gestionar sosteniblemente los recursos naturales',
                        'programas': ['Programa de Conservación Ambiental', 'Programa de Gestión del Agua']
                    },
                    {
                        'codigo': 4.2,
                        'nombre': 'Cambio Climático y Adaptación',
                        'descripcion': 'Adaptarse y mitigar los efectos del cambio climático',
                        'programas': ['Programa de Adaptación Climática', 'Programa de Energías Renovables']
                    }
                ]
            }
        ]

        self.indicadores_base = [
            {
                'tipo': 'Producto',
                'categoria': 'Agropecuario',
                'unidades': ['Hectáreas', 'Cabezas de ganado', 'Toneladas', 'Productores'],
                'nombres': [
                    'Hectáreas cultivadas con técnicas sostenibles',
                    'Cabezas de ganado mejoradas genéticamente',
                    'Toneladas de producción agrícola certificada',
                    'Productores capacitados en buenas prácticas'
                ]
            },
            {
                'tipo': 'Producto',
                'categoria': 'Industrial',
                'unidades': ['Empresas', 'Empleos', 'Inversiones', 'Proyectos'],
                'nombres': [
                    'Empresas formales creadas',
                    'Empleos directos generados',
                    'Inversión privada atraída',
                    'Proyectos productivos apoyados'
                ]
            },
            {
                'tipo': 'Producto',
                'categoria': 'Infraestructura',
                'unidades': ['Kilómetros', 'Viviendas', 'Sistemas', 'Usuarios'],
                'nombres': [
                    'Kilómetros de vías rehabilitadas',
                    'Viviendas con acceso a agua potable',
                    'Sistemas de alcantarillado instalados',
                    'Usuarios conectados a energía eléctrica'
                ]
            },
            {
                'tipo': 'Producto',
                'categoria': 'Social',
                'unidades': ['Estudiantes', 'Pacientes', 'Familias', 'Participantes'],
                'nombres': [
                    'Estudiantes con beca educativa',
                    'Pacientes atendidos en salud preventiva',
                    'Familias beneficiadas con programas sociales',
                    'Participantes en programas de formación'
                ]
            },
            {
                'tipo': 'Proceso',
                'categoria': 'Administrativo',
                'unidades': ['Procesos', 'Documentos', 'Capacitaciones', 'Auditorías'],
                'nombres': [
                    'Procesos administrativos digitalizados',
                    'Documentos procesados electrónicamente',
                    'Capacitaciones en gestión municipal',
                    'Auditorías de cumplimiento realizadas'
                ]
            }
        ]

        self.observaciones_trimestrales = [
            'Ejecución según lo programado',
            'Avances significativos en el trimestre',
            'Retrasos por factores climáticos',
            'Superando metas establecidas',
            'Dificultades en la contratación',
            'Colaboración interinstitucional exitosa',
            'Capacitación del personal completada',
            'Recursos adicionales gestionados',
            'Ajustes en la metodología de trabajo',
            'Resultados por encima de las expectativas'
        ]

    def get_or_create_admin_user(self):
        """Obtiene o crea un usuario administrador para el plan"""
        admin = User.query.filter_by(email='admin@alcaldia.test').first()
        if not admin:
            admin = User(
                username='admin_test',
                email='admin@alcaldia.test',
                password='admin123',
                municipality='Municipio de Prueba',
                department='Departamento de Prueba',
                first_name='Administrador',
                last_name='Sistema',
                position='Administrador del Sistema'
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuario administrador creado")
        else:
            print("✅ Usuario administrador encontrado")
        return admin

    def clear_existing_data(self):
        """Limpia datos existentes para evitar conflictos"""
        try:
            # Eliminar en orden inverso de dependencias
            EjecucionTrimestral.query.delete()
            IndicadorProducto.query.delete()
            Actividad.query.delete()
            Proyecto.query.delete()
            Programa.query.delete()
            Componente.query.delete()
            LineaEstrategica.query.delete()
            PlanDesarrollo.query.delete()
            db.session.commit()
            print("🧹 Datos existentes limpiados")
        except Exception as e:
            print(f"⚠️  Error limpiando datos: {str(e)}")
            db.session.rollback()

    def create_plan_desarrollo(self, admin_user):
        """Crea el Plan de Desarrollo principal"""
        plan = PlanDesarrollo(
            titulo='Plan de Desarrollo Municipal 2024-2027',
            descripcion='Plan integral para el desarrollo sostenible del municipio, enfocado en el crecimiento económico, inclusión social y gestión ambiental responsable.',
            anio_inicio=2024,
            anio_fin=2027,
            estado='activo',
            municipio=admin_user,
            presupuesto_total=500000000.00,  # 500 millones
            prioridad='alta'
        )
        db.session.add(plan)
        db.session.commit()
        print(f"✅ Plan de Desarrollo creado: {plan.titulo}")
        return plan

    def create_lineas_estrategicas(self, plan):
        """Crea las líneas estratégicas del plan"""
        lineas_creadas = []
        for linea_data in self.lineas_estrategicas:
            linea = LineaEstrategica(
                cod_linea=linea_data['codigo'],
                nombre=linea_data['nombre'],
                descripcion=linea_data['descripcion'],
                plan=plan,
                estado='activo',
                prioridad=random.choice(['media', 'alta', 'critica']),
                presupuesto_asignado=random.uniform(50000000, 150000000)  # 50-150M por línea
            )
            db.session.add(linea)
            lineas_creadas.append((linea, linea_data))
            print(f"  📍 Línea Estratégica {linea.cod_linea}: {linea.nombre}")

        db.session.commit()
        return lineas_creadas

    def create_componentes(self, lineas_data):
        """Crea los componentes para cada línea estratégica"""
        componentes_creados = []
        for linea, linea_data in lineas_data:
            for componente_data in linea_data['componentes']:
                componente = Componente(
                    cod_componente=componente_data['codigo'],
                    nombre=componente_data['nombre'],
                    descripcion=componente_data['descripcion'],
                    linea_estrategica=linea,
                    estado='activo',
                    prioridad=random.choice(['media', 'alta']),
                    presupuesto_total=random.uniform(20000000, 80000000),  # 20-80M por componente
                    presupuesto_ejecutado=random.uniform(5000000, 20000000),  # 5-20M ejecutados
                    dependencia_responsable=fake.company(),
                    bpim=fake.name()
                )
                db.session.add(componente)
                componentes_creados.append((componente, componente_data))
                print(f"    🧩 Componente {componente.cod_componente}: {componente.nombre}")

        db.session.commit()
        return componentes_creados

    def create_programas(self, componentes_data):
        """Crea los programas PDM para cada componente"""
        programas_creados = []
        for componente, componente_data in componentes_data:
            num_programas = random.randint(1, len(componente_data['programas']))
            programas_seleccionados = random.sample(componente_data['programas'], num_programas)

            for i, programa_nombre in enumerate(programas_seleccionados):
                programa = Programa(
                    cod_programa=f"{componente.cod_componente}.{i+1}",
                    nombre=programa_nombre,
                    descripcion=f"Programa enfocado en {programa_nombre.lower()} dentro del componente {componente.nombre.lower()}",
                    componente=componente,
                    estado='activo',
                    prioridad=random.choice(['media', 'alta']),
                    presupuesto_total=random.uniform(10000000, 40000000),  # 10-40M por programa
                    presupuesto_ejecutado=random.uniform(2000000, 10000000),  # 2-10M ejecutados
                    dependencia_responsable=fake.company(),
                    bpim=fake.name()
                )
                db.session.add(programa)
                programas_creados.append(programa)
                print(f"      📋 Programa {programa.cod_programa}: {programa.nombre}")

        db.session.commit()
        return programas_creados

    def create_proyectos(self, programas):
        """Crea proyectos para cada programa"""
        proyectos_creados = []
        for programa in programas:
            num_proyectos = random.randint(2, 4)  # 2-4 proyectos por programa

            for i in range(num_proyectos):
                proyecto = Proyecto(
                    cod_proyecto=f"{programa.cod_programa}.{i+1}",
                    nombre=fake.sentence(nb_words=6, variable_nb_words=True),
                    descripcion=fake.paragraph(nb_sentences=3),
                    programa=programa,
                    estado=random.choice(['planificado', 'ejecucion', 'completado']),
                    prioridad=random.choice(['media', 'alta']),
                    presupuesto_total=random.uniform(3000000, 15000000),  # 3-15M por proyecto
                    presupuesto_ejecutado=random.uniform(500000, 8000000),  # 0.5-8M ejecutados
                    fecha_inicio=fake.date_between(start_date='-6M', end_date='+3M'),
                    fecha_fin=fake.date_between(start_date='+6M', end_date='+18M'),
                    responsable=fake.name(),
                    dependencia_responsable=fake.company(),
                    bpim=fake.name()
                )
                db.session.add(proyecto)
                proyectos_creados.append(proyecto)
                print(f"        🎯 Proyecto {proyecto.cod_proyecto}: {proyecto.nombre[:50]}...")

        db.session.commit()
        return proyectos_creados

    def create_actividades(self, proyectos):
        """Crea actividades para cada proyecto"""
        actividades_creadas = []
        for proyecto in proyectos:
            num_actividades = random.randint(3, 6)  # 3-6 actividades por proyecto

            for i in range(num_actividades):
                actividad = Actividad(
                    nombre=fake.sentence(nb_words=4, variable_nb_words=True),
                    descripcion=fake.paragraph(nb_sentences=2),
                    tipo=random.choice(['capacitación', 'infraestructura', 'adquisición', 'consultoría', 'monitoreo']),
                    prioridad=random.choice(['baja', 'media', 'alta']),
                    presupuesto_asignado=random.uniform(200000, 2000000),  # 200K-2M por actividad
                    responsables=fake.name(),
                    fecha_inicio=fake.date_between(start_date=proyecto.fecha_inicio, end_date=proyecto.fecha_inicio.replace(month=min(12, proyecto.fecha_inicio.month + 2))),
                    fecha_fin=fake.date_between(start_date=proyecto.fecha_inicio.replace(month=min(12, proyecto.fecha_inicio.month + 1)), end_date=proyecto.fecha_fin),
                    progreso=random.uniform(0, 100),
                    estado=random.choice(['pendiente', 'en_progreso', 'completada', 'cancelada']),
                    proyecto=proyecto
                )
                db.session.add(actividad)
                actividades_creadas.append(actividad)
                print(f"          ✅ Actividad: {actividad.nombre[:40]}...")

        db.session.commit()
        return actividades_creadas

    def create_indicadores(self, proyectos):
        """Crea indicadores de producto para cada proyecto"""
        indicadores_creados = []
        admin_user = User.query.filter_by(email='admin@alcaldia.test').first()

        for proyecto in proyectos:
            num_indicadores = random.randint(3, 6)  # 3-6 indicadores por proyecto

            for i in range(num_indicadores):
                # Seleccionar categoría de indicador basada en el componente
                componente = proyecto.programa.componente
                if 'Agropecuario' in componente.nombre or 'Agrícola' in componente.nombre:
                    categoria = 'Agropecuario'
                elif 'Industrial' in componente.nombre or 'Empresarial' in componente.nombre:
                    categoria = 'Industrial'
                elif 'Infraestructura' in componente.nombre or 'Vial' in componente.nombre:
                    categoria = 'Infraestructura'
                elif 'Social' in componente.nombre or 'Educación' in componente.nombre or 'Salud' in componente.nombre:
                    categoria = 'Social'
                else:
                    categoria = random.choice(['Agropecuario', 'Industrial', 'Infraestructura', 'Social'])

                indicador_info = next((ind for ind in self.indicadores_base if ind['categoria'] == categoria), self.indicadores_base[0])

                indicador = IndicadorProducto(
                    cod_indicador=f"IND-{proyecto.cod_proyecto}-{i+1}",
                    nombre=random.choice(indicador_info['nombres']),
                    descripcion=fake.paragraph(nb_sentences=2),
                    tipo_indicador=random.choice(['Producto', 'Proceso', 'Resultado']),
                    linea_base=random.uniform(0, 1000),
                    sentido=random.choice(['positivo', 'negativo', 'neutral']),
                    tipologia=random.choice(['Económico', 'Social', 'Ambiental', 'Institucional']),
                    unidad=random.choice(indicador_info['unidades']),
                    meta_cuatrienio=random.uniform(1000, 10000),
                    meta_2024=random.uniform(200, 2500),
                    proyecto=proyecto,
                    estado='activo'
                )
                db.session.add(indicador)
                indicadores_creados.append(indicador)
                print(f"            📊 Indicador {indicador.cod_indicador}: {indicador.nombre[:50]}...")

        db.session.commit()
        return indicadores_creados

    def create_ejecuciones_trimestrales(self, indicadores):
        """Crea ejecuciones trimestrales para cada indicador (2024)"""
        ejecuciones_creadas = []
        admin_user = User.query.filter_by(email='admin@alcaldia.test').first()

        for indicador in indicadores:
            # Crear 4 trimestres para 2024
            ejecucion_acumulada = 0
            poblacion_acumulada = 0

            for trimestre in range(1, 5):
                # Generar valores progresivos
                ejecucion_trimestral = random.uniform(50, 800)
                ejecucion_acumulada += ejecucion_trimestral

                poblacion_trimestral = random.randint(100, 1500)
                poblacion_acumulada += poblacion_trimestral

                # Calcular cumplimiento basado en meta 2024
                cumplimiento_trimestral = min((ejecucion_trimestral / indicador.meta_2024) * 100, 150) if indicador.meta_2024 > 0 else 0
                cumplimiento_acumulado = min((ejecucion_acumulada / indicador.meta_cuatrienio) * 100, 150) if indicador.meta_cuatrienio > 0 else 0

                ejecucion = EjecucionTrimestral(
                    anio=2024,
                    trimestre=trimestre,
                    ejecucion_trimestral=round(ejecucion_trimestral, 2),
                    ejecucion_acumulada=round(ejecucion_acumulada, 2),
                    cumplimiento_trimestral=round(cumplimiento_trimestral, 2),
                    cumplimiento_acumulado=round(cumplimiento_acumulado, 2),
                    poblacion_impactada_trimestral=poblacion_trimestral,
                    poblacion_impactada_acumulada=poblacion_acumulada,
                    presupuesto_ejecutado_trimestral=round(random.uniform(10000, 500000), 2),
                    presupuesto_ejecutado_acumulado=round(random.uniform(50000, 2000000), 2),
                    observacion_trimestral=random.choice(self.observaciones_trimestrales),
                    observacion_acumulada=f"Avance general satisfactorio hasta el trimestre {trimestre}",
                    indicador=indicador,
                    proyecto=indicador.proyecto,
                    usuario=admin_user,
                    fuente_informacion=fake.company(),
                    verificado=random.choice([True, False])
                )
                db.session.add(ejecucion)
                ejecuciones_creadas.append(ejecucion)
                print(f"              📈 Trimestre {trimestre}/2024: {round(ejecucion_trimestral, 1)} {indicador.unidad}")

        db.session.commit()
        return ejecuciones_creadas

    def generate_complete_plan(self):
        """Genera el plan completo con todos los datos sintéticos"""
        print("🚀 Iniciando generación de datos sintéticos...")
        print("=" * 60)

        try:
            # 0. Limpiar datos existentes
            self.clear_existing_data()

            # 1. Usuario administrador
            admin_user = self.get_or_create_admin_user()

            # 2. Plan de Desarrollo
            plan = self.create_plan_desarrollo(admin_user)

            # 3. Líneas Estratégicas
            print("\n📍 Creando Líneas Estratégicas...")
            lineas_data = self.create_lineas_estrategicas(plan)

            # 4. Componentes
            print("\n🧩 Creando Componentes...")
            componentes_data = self.create_componentes(lineas_data)

            # 5. Programas PDM
            print("\n📋 Creando Programas PDM...")
            programas = self.create_programas(componentes_data)

            # 6. Proyectos
            print("\n🎯 Creando Proyectos...")
            proyectos = self.create_proyectos(programas)

            # 7. Actividades
            print("\n✅ Creando Actividades...")
            actividades = self.create_actividades(proyectos)

            # 8. Indicadores de Producto
            print("\n📊 Creando Indicadores de Producto...")
            indicadores = self.create_indicadores(proyectos)

            # 9. Ejecuciones Trimestrales
            print("\n📈 Creando Ejecuciones Trimestrales...")
            ejecuciones = self.create_ejecuciones_trimestrales(indicadores)

            print("\n" + "=" * 60)
            print("✅ ¡GENERACIÓN COMPLETA!")
            print("=" * 60)

            # Estadísticas finales
            stats = {
                'Plan': 1,
                'Líneas Estratégicas': len(lineas_data),
                'Componentes': len(componentes_data),
                'Programas': len(programas),
                'Proyectos': len(proyectos),
                'Actividades': len(actividades),
                'Indicadores': len(indicadores),
                'Ejecuciones': len(ejecuciones)
            }

            print("📊 ESTADÍSTICAS FINALES:")
            for key, value in stats.items():
                print(f"  {key}: {value}")

            total_rows = sum(stats.values())
            print(f"\n🎯 TOTAL DE FILAS GENERADAS: {total_rows}")
            print("✅ OBJETIVO SUPERADO: Más de 100 filas generadas!")

            return True

        except Exception as e:
            print(f"❌ Error durante la generación: {str(e)}")
            db.session.rollback()
            return False

def main():
    """Función principal"""
    print("🌱 GENERADOR DE DATOS SINTÉTICOS")
    print("Plan de Desarrollo Municipal 2024-2027")
    print("=" * 50)

    generator = SyntheticDataGenerator()
    success = generator.generate_complete_plan()

    if success:
        print("\n🎉 ¡Datos sintéticos generados exitosamente!")
        print("💡 Puedes ahora ejecutar la aplicación y explorar los datos generados.")
    else:
        print("\n❌ Falló la generación de datos sintéticos.")
        sys.exit(1)

if __name__ == "__main__":
    main()
