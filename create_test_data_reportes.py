#!/usr/bin/env python3
"""
Script para crear datos de prueba completos para el sistema de reportes BI
"""

from app import create_app, db
from app.models.user import User
from app.models.plan_desarrollo import PlanDesarrollo
from app.models.linea_estrategica import LineaEstrategica
from app.models.componente import Componente
from app.models.programa import Programa
from app.models.proyecto import Proyecto
from app.models.indicador_producto import IndicadorProducto
from app.models.ejecucion_trimestral import EjecucionTrimestral
from datetime import datetime

app = create_app()

def create_test_data():
    """Crear datos de prueba completos para el sistema de reportes"""

    with app.app_context():
        print("🧪 CREANDO DATOS DE PRUEBA PARA REPORTES BI")
        print("=" * 50)

        # Verificar usuario admin
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("❌ No hay usuario admin. Creando...")
            admin = User(
                username='admin',
                first_name='Administrador',
                last_name='Sistema',
                email='admin@alcaldias.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuario admin creado")

        # Crear plan de desarrollo activo
        plan_activo = PlanDesarrollo.query.filter_by(
            municipio=admin,
            estado='activo'
        ).first()

        if plan_activo:
            print(f"⚠️  Ya existe un plan activo: {plan_activo.titulo}")
            print("   Eliminando datos existentes para recrear...")
            # Limpiar datos existentes
            EjecucionTrimestral.query.delete()
            IndicadorProducto.query.delete()
            Proyecto.query.delete()
            Programa.query.delete()
            Componente.query.delete()
            LineaEstrategica.query.delete()
            db.session.delete(plan_activo)
            db.session.commit()

        print("🏗️  Creando plan de desarrollo activo...")

        # Crear plan de desarrollo
        plan = PlanDesarrollo(
            titulo="Plan de Desarrollo Municipal 2024-2027",
            descripcion="Plan integral para el desarrollo sostenible del municipio",
            municipio=admin,
            presupuesto_total=250000000,  # 250 millones
            anio_inicio=2024,
            anio_fin=2027,
            estado='activo'
        )
        db.session.add(plan)
        db.session.commit()
        print(f"✅ Plan creado: {plan.titulo} (ID: {plan.id})")

        # Crear líneas estratégicas
        lineas_data = [
            ("Desarrollo Económico", "Fomentar el crecimiento económico sostenible", 80000000),
            ("Infraestructura Básica", "Mejorar la infraestructura municipal", 90000000),
            ("Desarrollo Social", "Promover el bienestar social", 50000000),
            ("Medio Ambiente", "Proteger y preservar el medio ambiente", 30000000)
        ]

        lineas = []
        for nombre, descripcion, presupuesto in lineas_data:
            linea = LineaEstrategica(
                nombre=nombre,
                descripcion=descripcion,
                presupuesto_asignado=presupuesto,
                plan=plan
            )
            db.session.add(linea)
            lineas.append(linea)
        db.session.commit()
        print(f"✅ {len(lineas)} líneas estratégicas creadas")

        # Crear componentes por línea estratégica
        componentes_data = [
            # Desarrollo Económico
            ("Empleo y Emprendimiento", "Generar oportunidades de empleo", 40000000, lineas[0]),
            ("Turismo", "Desarrollar el sector turístico", 25000000, lineas[0]),
            ("Comercio Local", "Fomentar el comercio local", 15000000, lineas[0]),

            # Infraestructura Básica
            ("Vialidad", "Mejorar la red vial", 45000000, lineas[1]),
            ("Agua y Saneamiento", "Sistema de agua potable", 30000000, lineas[1]),
            ("Energía", "Infraestructura energética", 15000000, lineas[1]),

            # Desarrollo Social
            ("Educación", "Mejorar la calidad educativa", 25000000, lineas[2]),
            ("Salud", "Acceso a servicios de salud", 20000000, lineas[2]),
            ("Deporte y Cultura", "Actividades recreativas", 5000000, lineas[2]),

            # Medio Ambiente
            ("Gestión de Residuos", "Sistema de recolección", 15000000, lineas[3]),
            ("Áreas Verdes", "Parques y espacios públicos", 10000000, lineas[3]),
            ("Recursos Hídricos", "Protección de cuencas", 5000000, lineas[3])
        ]

        componentes = []
        for nombre, descripcion, presupuesto, linea in componentes_data:
            componente = Componente(
                nombre=nombre,
                descripcion=descripcion,
                presupuesto_asignado=presupuesto,
                linea_estrategica=linea
            )
            db.session.add(componente)
            componentes.append(componente)
        db.session.commit()
        print(f"✅ {len(componentes)} componentes creados")

        # Crear programas por componente
        programas_data = [
            # Empleo y Emprendimiento
            ("Programa Jóvenes al Trabajo", "Inserción laboral juvenil", 20000000, componentes[0]),
            ("Centro de Emprendimiento", "Apoyo a emprendedores", 15000000, componentes[0]),
            ("Capacitación Laboral", "Formación profesional", 5000000, componentes[0]),

            # Turismo
            ("Rutas Turísticas", "Desarrollo de circuitos turísticos", 15000000, componentes[1]),
            ("Promoción Turística", "Campañas de marketing", 10000000, componentes[1]),

            # Agua y Saneamiento
            ("Sistema de Acueducto", "Red de distribución de agua", 20000000, componentes[4]),
            ("Tratamiento de Aguas", "Planta de tratamiento", 10000000, componentes[4]),

            # Educación
            ("Programa de Alfabetización", "Reducción del analfabetismo", 15000000, componentes[6]),
            ("Infraestructura Educativa", "Construcción de escuelas", 10000000, componentes[6]),

            # Salud
            ("Centro de Salud Rural", "Atención primaria", 12000000, componentes[7]),
            ("Programa de Vacunación", "Cobertura vacunal", 8000000, componentes[7]),

            # Gestión de Residuos
            ("Recolección Selectiva", "Separación en origen", 10000000, componentes[9]),
            ("Planta de Tratamiento", "Procesamiento de residuos", 5000000, componentes[9])
        ]

        programas = []
        for nombre, descripcion, presupuesto, componente in programas_data:
            programa = Programa(
                nombre=nombre,
                descripcion=descripcion,
                presupuesto_asignado=presupuesto,
                componente=componente
            )
            db.session.add(programa)
            programas.append(programa)
        db.session.commit()
        print(f"✅ {len(programas)} programas creados")

        # Crear proyectos por programa
        proyectos_data = [
            # Programa Jóvenes al Trabajo
            ("Bolsa de Empleo Juvenil", "Conexión empleadores-jóvenes", 12000000, programas[0]),
            ("Programa de Pasantías", "Experiencia laboral", 8000000, programas[0]),

            # Centro de Emprendimiento
            ("Incubadora de Negocios", "Espacio coworking", 10000000, programas[1]),
            ("Fondo de Emprendimiento", "Apoyo financiero", 5000000, programas[1]),

            # Sistema de Acueducto
            ("Red de Distribución", "Tubería principal", 15000000, programas[5]),
            ("Pozos de Agua", "Captación de agua", 5000000, programas[5]),

            # Programa de Alfabetización
            ("Campaña de Alfabetización", "Clases nocturnas", 10000000, programas[7]),
            ("Material Didáctico", "Libros y recursos", 5000000, programas[7]),

            # Centro de Salud Rural
            ("Construcción Centro Médico", "Edificio sanitario", 8000000, programas[8]),
            ("Equipamiento Médico", "Instrumental y mobiliario", 4000000, programas[8]),

            # Recolección Selectiva
            ("Contenedores Inteligentes", "Puntos de recolección", 7000000, programas[10]),
            ("Programa de Educación", "Concienciación ambiental", 3000000, programas[10])
        ]

        proyectos = []
        for nombre, descripcion, presupuesto, programa in proyectos_data:
            proyecto = Proyecto(
                nombre=nombre,
                descripcion=descripcion,
                presupuesto_asignado=presupuesto,
                programa=programa
            )
            db.session.add(proyecto)
            proyectos.append(proyecto)
        db.session.commit()
        print(f"✅ {len(proyectos)} proyectos creados")

        # Crear indicadores por proyecto
        indicadores_data = [
            # Proyecto Bolsa de Empleo Juvenil
            ("Empleo juvenil", "% de jóvenes empleados (18-25 años)", 60, 55, 58, proyectos[0]),
            ("Inserción laboral", "Número de jóvenes colocados", 500, 450, 480, proyectos[0]),

            # Proyecto Incubadora de Negocios
            ("Emprendimientos creados", "Número de nuevos negocios", 25, 22, 24, proyectos[2]),
            ("Empleos generados", "Nuevos puestos de trabajo", 75, 68, 72, proyectos[2]),

            # Proyecto Red de Distribución
            ("Cobertura de agua potable", "% de población con acceso", 85, 82, 84, proyectos[4]),
            ("Calidad del agua", "Cumplimiento estándares OMS", 95, 93, 94, proyectos[4]),

            # Proyecto Campaña de Alfabetización
            ("Tasa de alfabetización", "% población alfabetizada", 95, 93, 94, proyectos[6]),
            ("Participantes atendidos", "Número de estudiantes", 1200, 1150, 1180, proyectos[6]),

            # Proyecto Construcción Centro Médico
            ("Cobertura sanitaria", "% población con acceso", 90, 87, 89, proyectos[8]),
            ("Consultas médicas", "Número mensual promedio", 2500, 2350, 2450, proyectos[8]),

            # Proyecto Contenedores Inteligentes
            ("Recolección selectiva", "% residuos reciclados", 70, 65, 68, proyectos[10]),
            ("Participación ciudadana", "% hogares participando", 60, 55, 58, proyectos[10]),

            # Más indicadores para completar datos
            ("Acceso a vivienda digna", "% familias con vivienda adecuada", 75, 72, 74, proyectos[1]),
            ("Reducción de pobreza", "% disminución extrema pobreza", 45, 42, 44, proyectos[3]),
            ("Cobertura eléctrica", "% hogares con energía", 95, 93, 94, proyectos[5]),
            ("Acceso a internet", "% población conectada", 80, 76, 78, proyectos[7]),
            ("Cobertura sanitaria rural", "% comunidades atendidas", 85, 82, 84, proyectos[9]),
            ("Áreas verdes por habitante", "m² per cápita", 15, 14, 14.5, proyectos[11])
        ]

        indicadores = []
        for nombre, descripcion, meta_2024, ejecucion_q1, ejecucion_q2, proyecto in indicadores_data:
            indicador = IndicadorProducto(
                nombre=nombre,
                descripcion=descripcion,
                meta_2024=meta_2024,
                ejecucion_q1=ejecucion_q1,
                ejecucion_q2=ejecucion_q2,
                proyecto=proyecto
            )
            db.session.add(indicador)
            indicadores.append(indicador)
        db.session.commit()
        print(f"✅ {len(indicadores)} indicadores creados")

        # Crear datos de ejecución trimestral para algunos indicadores
        ejecuciones_data = [
            # Indicador Empleo juvenil - 2024
            (indicadores[0], 2024, 1, 45, "Primer trimestre con buen desempeño"),
            (indicadores[0], 2024, 2, 55, "Incremento en colocaciones"),
            (indicadores[0], 2024, 3, 58, "Meta trimestral superada"),

            # Indicador Cobertura agua potable - 2024
            (indicadores[4], 2024, 1, 78, "Expansión red de distribución"),
            (indicadores[4], 2024, 2, 82, "Conexiones nuevas realizadas"),
            (indicadores[4], 2024, 3, 84, "Mantenimiento preventivo completado"),

            # Indicador Tasa alfabetización - 2024
            (indicadores[6], 2024, 1, 90, "Inicio programa intensivo"),
            (indicadores[6], 2024, 2, 93, "Participación creciente"),
            (indicadores[6], 2024, 3, 94, "Resultados superiores a lo esperado"),

            # Indicador Cobertura sanitaria - 2024
            (indicadores[8], 2024, 1, 82, "Centro médico operativo"),
            (indicadores[8], 2024, 2, 87, "Equipo médico completo"),
            (indicadores[8], 2024, 3, 89, "Programa preventivo implementado")
        ]

        for indicador, anio, trimestre, valor, observaciones in ejecuciones_data:
            ejecucion = EjecucionTrimestral(
                indicador=indicador,
                anio=anio,
                trimestre=trimestre,
                valor_ejecutado=valor,
                observaciones=observaciones
            )
            db.session.add(ejecucion)
        db.session.commit()
        print(f"✅ {len(ejecuciones_data)} registros de ejecución trimestral creados")

        print("\n🎯 RESUMEN DE DATOS CREADOS:")
        print("=" * 40)
        print(f"📋 Plan Activo: {plan.titulo}")
        print(f"🏛️  Líneas Estratégicas: {len(lineas)}")
        print(f"🔧 Componentes: {len(componentes)}")
        print(f"📚 Programas: {len(programas)}")
        print(f"🚀 Proyectos: {len(proyectos)}")
        print(f"📊 Indicadores: {len(indicadores)}")
        print(f"📈 Ejecuciones: {len(ejecuciones_data)}")
        print(f"💰 Presupuesto Total: ${plan.presupuesto_total:,.0f}")
        print(f"✅ Estado: {plan.estado}")

        print("\n🧪 PRUEBA EL SISTEMA:")
        print("1. Inicia la aplicación: python run.py")
        print("2. Ve a http://localhost:5000")
        print("3. Login: admin / admin123")
        print("4. Ve a Reportes desde Dashboard")
        print("5. Prueba los diferentes tipos de análisis")
        print("6. Verifica que los gráficos se carguen correctamente")
        print("7. Revisa la tabla de datos detallados")

        print("\n✅ ¡DATOS DE PRUEBA CREADOS EXITOSAMENTE!")
        print("   El sistema de reportes BI está listo para pruebas completas.")

if __name__ == '__main__':
    create_test_data()
