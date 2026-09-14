#!/usr/bin/env python3
"""
Script simple para crear datos de prueba básicos para el sistema de reportes BI
"""

from app import create_app, db

app = create_app()

def create_simple_test_data():
    """Crear datos de prueba básicos y compatibles con la estructura actual"""

    with app.app_context():
        print("🧪 CREANDO DATOS DE PRUEBA SIMPLES PARA REPORTES BI")
        print("=" * 55)

        # Importar modelos dentro del contexto
        from app.models.user import User
        from app.models.plan_desarrollo import PlanDesarrollo
        from app.models.linea_estrategica import LineaEstrategica
        from app.models.componente import Componente
        from app.models.programa import Programa
        from app.models.proyecto import Proyecto
        from app.models.indicador_producto import IndicadorProducto
        from app.models.ejecucion_trimestral import EjecucionTrimestral

        # Verificar/crear usuario admin
        admin = User.query.filter_by(username='admin').first()
        if not admin:
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

        # Verificar si ya hay un plan activo
        plan_activo = PlanDesarrollo.query.filter_by(
            municipio=admin,
            estado='activo'
        ).first()

        if plan_activo:
            print(f"✅ Ya existe plan activo: {plan_activo.titulo}")
            plan = plan_activo

            # Verificar si ya tiene datos
            lineas_count = LineaEstrategica.query.filter_by(plan=plan).count()
            if lineas_count > 0:
                print(f"✅ El plan ya tiene {lineas_count} líneas estratégicas")
                return
        else:
            # Crear plan básico
            plan = PlanDesarrollo(
                titulo="Plan de Desarrollo Municipal 2024-2027",
                descripcion="Plan integral para el desarrollo sostenible",
                municipio=admin,
                presupuesto_total=100000000,
                anio_inicio=2024,
                anio_fin=2027,
                estado='activo'
            )
            db.session.add(plan)
            db.session.commit()
            print(f"✅ Plan creado: {plan.titulo}")

        print("🏗️ Creando estructura básica...")

        # Crear líneas estratégicas básicas
        lineas_data = [
            (1, "Desarrollo Económico", "Crecimiento económico sostenible"),
            (2, "Infraestructura", "Mejora de infraestructura municipal"),
            (3, "Desarrollo Social", "Bienestar social de la comunidad")
        ]

        lineas = []
        for cod_linea, nombre, descripcion in lineas_data:
            linea = LineaEstrategica(
                cod_linea=cod_linea,
                nombre=nombre,
                descripcion=descripcion,
                plan=plan
            )
            db.session.add(linea)
            lineas.append(linea)
        db.session.commit()
        print(f"✅ {len(lineas)} líneas estratégicas creadas")

        # Crear componentes básicos
        componentes_data = [
            (1.1, "Empleo Juvenil", "Generar oportunidades de empleo", lineas[0]),
            (2.1, "Agua Potable", "Sistema de agua potable", lineas[1]),
            (3.1, "Educación", "Mejora educativa", lineas[2])
        ]

        componentes = []
        for cod_componente, nombre, descripcion, linea in componentes_data:
            componente = Componente(
                cod_componente=cod_componente,
                nombre=nombre,
                descripcion=descripcion,
                linea_estrategica=linea
            )
            db.session.add(componente)
            componentes.append(componente)
        db.session.commit()
        print(f"✅ {len(componentes)} componentes creados")

        # Crear programas básicos
        programas_data = [
            ("P001", "Programa Jóvenes", "Inserción laboral juvenil", componentes[0]),
            ("P002", "Sistema Acueducto", "Red de distribución de agua", componentes[1]),
            ("P003", "Alfabetización", "Reducción del analfabetismo", componentes[2])
        ]

        programas = []
        for cod_programa, nombre, descripcion, componente in programas_data:
            programa = Programa(
                cod_programa=cod_programa,
                nombre=nombre,
                descripcion=descripcion,
                componente=componente
            )
            db.session.add(programa)
            programas.append(programa)
        db.session.commit()
        print(f"✅ {len(programas)} programas creados")

        # Crear proyectos básicos
        proyectos_data = [
            ("Bolsa Empleo", "Conexión empleadores-jóvenes", programas[0]),
            ("Red Agua", "Distribución de agua potable", programas[1]),
            ("Campaña Alfa", "Clases de alfabetización", programas[2])
        ]

        proyectos = []
        for nombre, descripcion, programa in proyectos_data:
            proyecto = Proyecto(
                nombre=nombre,
                descripcion=descripcion,
                programa=programa
            )
            db.session.add(proyecto)
            proyectos.append(proyecto)
        db.session.commit()
        print(f"✅ {len(proyectos)} proyectos creados")

        # Crear indicadores básicos
        indicadores_data = [
            ("Empleo juvenil", "% jóvenes empleados", 60, 55, 58, proyectos[0]),
            ("Cobertura agua", "% con acceso a agua", 85, 82, 84, proyectos[1]),
            ("Tasa alfabetización", "% alfabetizados", 95, 93, 94, proyectos[2]),
            ("Participantes", "N° estudiantes atendidos", 500, 450, 480, proyectos[2])
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

        # Crear algunos datos de ejecución trimestral
        ejecuciones_data = [
            (indicadores[0], 2024, 1, 45, "Primer trimestre"),
            (indicadores[0], 2024, 2, 55, "Segundo trimestre"),
            (indicadores[1], 2024, 1, 78, "Expansión de red"),
            (indicadores[1], 2024, 2, 82, "Conexiones nuevas"),
            (indicadores[2], 2024, 1, 90, "Inicio programa"),
            (indicadores[2], 2024, 2, 93, "Participación creciente")
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
        print(f"✅ {len(ejecuciones_data)} registros de ejecución creados")

        print("\n🎯 DATOS CREADOS:")
        print("=" * 30)
        print(f"📋 Plan: {plan.titulo}")
        print(f"🏛️  Líneas: {len(lineas)}")
        print(f"🔧 Componentes: {len(componentes)}")
        print(f"📚 Programas: {len(programas)}")
        print(f"🚀 Proyectos: {len(proyectos)}")
        print(f"📊 Indicadores: {len(indicadores)}")
        print(f"📈 Ejecuciones: {len(ejecuciones_data)}")

        print("\n🧪 PRUEBA EL SISTEMA:")
        print("1. python run.py")
        print("2. http://localhost:5000")
        print("3. Login: admin / admin123")
        print("4. Dashboard → 'Ver Reportes'")
        print("5. Prueba análisis: General, Ejecución, Presupuesto, etc.")
        print("6. Verifica tabla de datos detallados")
        print("7. Cambia período y tipo de gráfico")

        print("\n✅ ¡DATOS DE PRUEBA LISTOS!")
        print("   Sistema de reportes BI poblado y funcional.")

if __name__ == '__main__':
    create_simple_test_data()
