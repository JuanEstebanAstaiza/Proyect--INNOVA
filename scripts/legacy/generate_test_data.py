#!/usr/bin/env python3
"""
Script simplificado para generar datos de prueba del Plan de Desarrollo
"""

import os
import sys
import random
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    User, PlanDesarrollo, LineaEstrategica, Componente, Programa, Proyecto,
    Actividad, IndicadorProducto, EjecucionTrimestral
)

class TestDataGenerator:
    """Generador simplificado de datos de prueba"""

    def __init__(self):
        self.app = create_app()
        self.app.app_context().push()

    def clear_existing_plan_data(self):
        """Limpia datos de planes existentes"""
        try:
            EjecucionTrimestral.query.delete()
            IndicadorProducto.query.delete()
            Actividad.query.delete()
            Proyecto.query.delete()
            Programa.query.delete()
            Componente.query.delete()
            LineaEstrategica.query.delete()
            PlanDesarrollo.query.delete()
            db.session.commit()
            print("🧹 Datos de planes limpiados")
        except Exception as e:
            print(f"⚠️  Error limpiando: {str(e)}")
            db.session.rollback()

    def create_admin_user(self):
        """Crea usuario admin si no existe"""
        admin = User.query.filter_by(email='admin@test.com').first()
        if not admin:
            admin = User(
                username='admin_test_data',
                email='admin@test.com',
                password='admin123',
                municipality='Municipio Test',
                department='Departamento Test',
                first_name='Admin',
                last_name='Sistema',
                position='Administrador'
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin creado")
        return admin

    def create_test_plan(self, admin):
        """Crea un plan de desarrollo simple"""
        plan = PlanDesarrollo(
            titulo='Plan de Desarrollo TEST 2024-2027',
            descripcion='Plan de prueba para desarrollo y testing',
            anio_inicio=2024,
            anio_fin=2027,
            estado='activo',
            municipio=admin,
            presupuesto_total=100000000.00,
            prioridad='alta'
        )
        db.session.add(plan)
        db.session.commit()
        print(f"✅ Plan creado: {plan.titulo}")
        return plan

    def create_test_lineas(self, plan):
        """Crea líneas estratégicas de prueba"""
        lineas = []
        lineas_data = [
            (1, 'Desarrollo Económico'),
            (2, 'Infraestructura'),
            (3, 'Desarrollo Social'),
            (4, 'Gestión Ambiental')
        ]

        for cod, nombre in lineas_data:
            linea = LineaEstrategica(
                cod_linea=cod,
                nombre=nombre,
                descripcion=f'Descripción de {nombre}',
                plan=plan,
                estado='activo',
                prioridad='media',
                presupuesto_asignado=random.uniform(10000000, 30000000)
            )
            db.session.add(linea)
            lineas.append(linea)
            print(f"  📍 Línea {cod}: {nombre}")

        db.session.commit()
        return lineas

    def create_test_componentes(self, lineas):
        """Crea componentes de prueba"""
        componentes = []
        comp_counter = 1

        for linea in lineas:
            # 2-3 componentes por línea
            num_comp = random.randint(2, 3)

            for i in range(num_comp):
                componente = Componente(
                    cod_componente=float(f"{linea.cod_linea}.{i+1}"),
                    nombre=f"Componente {comp_counter}",
                    descripcion=f"Descripción del componente {comp_counter}",
                    linea_estrategica=linea,
                    estado='activo',
                    prioridad='media',
                    presupuesto_asignado=random.uniform(5000000, 15000000)
                )
                db.session.add(componente)
                componentes.append(componente)
                comp_counter += 1
                print(f"    🧩 Componente {componente.cod_componente}: {componente.nombre}")

        db.session.commit()
        return componentes

    def create_test_programas(self, componentes):
        """Crea programas de prueba"""
        programas = []
        prog_counter = 1

        for componente in componentes:
            # 1-2 programas por componente
            num_prog = random.randint(1, 2)

            for i in range(num_prog):
                programa = Programa(
                    cod_programa=f"{componente.cod_componente}.{i+1}",
                    nombre=f"Programa {prog_counter}",
                    descripcion=f"Descripción del programa {prog_counter}",
                    componente=componente,
                    estado='activo',
                    presupuesto_asignado=random.uniform(2000000, 8000000),
                    dependencia_responsable='Dependencia Test',
                    bpim='BPIM Test'
                )
                db.session.add(programa)
                programas.append(programa)
                prog_counter += 1
                print(f"      📋 Programa {programa.cod_programa}: {programa.nombre}")

        db.session.commit()
        return programas

    def create_test_proyectos(self, programas):
        """Crea proyectos de prueba"""
        proyectos = []
        proj_counter = 1

        for programa in programas:
            # 2-3 proyectos por programa
            num_proj = random.randint(2, 3)

            for i in range(num_proj):
                proyecto = Proyecto(
                    nombre=f"Proyecto {proj_counter}",
                    descripcion=f"Descripción del proyecto {proj_counter}",
                    programa=programa,
                    estado='en_ejecucion',
                    presupuesto_total=random.uniform(500000, 2000000),
                    presupuesto_ejecutado=random.uniform(100000, 500000),
                    fecha_inicio=datetime(2024, 1, 1),
                    fecha_fin=datetime(2025, 12, 31),
                    responsable_ejecucion='Responsable Test',
                    ubicacion='Ubicación Test',
                    sector='Sector Test'
                )
                db.session.add(proyecto)
                proyectos.append(proyecto)
                proj_counter += 1
                print(f"        🎯 Proyecto {proj_counter}: {proyecto.nombre}")

        db.session.commit()
        return proyectos

    def create_test_indicadores(self, proyectos):
        """Crea indicadores de prueba"""
        indicadores = []
        ind_counter = 1
        admin = User.query.filter_by(email='admin@test.com').first() or User.query.filter_by(username='admin_test_data').first()

        for proyecto in proyectos:
            # 3-5 indicadores por proyecto
            num_ind = random.randint(3, 5)

            for i in range(num_ind):
                indicador = IndicadorProducto(
                    cod_indicador=f"IND-{proyecto.id}-{i+1}",
                    nombre=f"Indicador {ind_counter}",
                    descripcion=f"Descripción del indicador {ind_counter}",
                    tipo_indicador='Producto',
                    linea_base=random.uniform(0, 100),
                    sentido='positivo',
                    tipologia='Económico',
                    unidad='Unidades',
                    meta_cuatrienio=random.uniform(500, 2000),
                    meta_2024=random.uniform(100, 500),
                    proyecto=proyecto,
                    estado='activo'
                )
                db.session.add(indicador)
                indicadores.append(indicador)
                ind_counter += 1
                print(f"          📊 Indicador {indicador.cod_indicador}: {indicador.nombre}")

        db.session.commit()
        return indicadores

    def create_test_ejecuciones(self, indicadores):
        """Crea ejecuciones trimestrales de prueba"""
        ejecuciones = []
        admin = User.query.filter_by(email='admin@test.com').first() or User.query.filter_by(username='admin_test_data').first()

        for indicador in indicadores:
            # 4 trimestres para 2024
            for trimestre in range(1, 5):
                ejecucion = EjecucionTrimestral(
                    anio=2024,
                    trimestre=trimestre,
                    ejecucion_trimestral=random.uniform(10, 100),
                    ejecucion_acumulada=random.uniform(50, 400),
                    cumplimiento_trimestral=random.uniform(20, 120),
                    cumplimiento_acumulado=random.uniform(30, 150),
                    poblacion_impactada_trimestral=random.randint(50, 300),
                    poblacion_impactada_acumulada=random.randint(200, 1000),
                    presupuesto_ejecutado_trimestral=random.uniform(5000, 25000),
                    presupuesto_ejecutado_acumulado=random.uniform(20000, 100000),
                    observacion_trimestral='Ejecución normal del trimestre',
                    indicador=indicador,
                    proyecto=indicador.proyecto,
                    usuario=admin,
                    fuente_informacion='Sistema Test',
                    verificado=True
                )
                db.session.add(ejecucion)
                ejecuciones.append(ejecucion)
                print(f"            📈 T{trimestre}/2024: {round(ejecucion.ejecucion_trimestral, 1)}")

        db.session.commit()
        return ejecuciones

    def generate_test_data(self):
        """Genera todos los datos de prueba"""
        print("🧪 GENERADOR DE DATOS DE PRUEBA")
        print("=" * 50)

        try:
            # Limpiar datos existentes
            self.clear_existing_plan_data()

            # Crear jerarquía
            admin = self.create_admin_user()
            plan = self.create_test_plan(admin)
            lineas = self.create_test_lineas(plan)
            componentes = self.create_test_componentes(lineas)
            programas = self.create_test_programas(componentes)
            proyectos = self.create_test_proyectos(programas)
            indicadores = self.create_test_indicadores(proyectos)
            ejecuciones = self.create_test_ejecuciones(indicadores)

            # Estadísticas
            stats = {
                'Plan': 1,
                'Líneas': len(lineas),
                'Componentes': len(componentes),
                'Programas': len(programas),
                'Proyectos': len(proyectos),
                'Indicadores': len(indicadores),
                'Ejecuciones': len(ejecuciones)
            }

            print("\n" + "=" * 50)
            print("✅ DATOS DE PRUEBA GENERADOS")
            print("=" * 50)

            print("\n📊 ESTADÍSTICAS:")
            for key, value in stats.items():
                print(f"  {key}: {value}")

            total = sum(stats.values())
            print(f"\n🎯 TOTAL DE REGISTROS: {total}")
            print("✅ OBJETIVO SUPERADO: Más de 100 registros generados!")

            return True

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            db.session.rollback()
            return False

def main():
    """Función principal"""
    generator = TestDataGenerator()
    success = generator.generate_test_data()

    if success:
        print("\n🎉 ¡Datos de prueba generados exitosamente!")
        print("💡 Ahora puedes ejecutar la aplicación y explorar los datos.")
    else:
        print("\n❌ Error generando datos de prueba.")
        sys.exit(1)

if __name__ == "__main__":
    main()
