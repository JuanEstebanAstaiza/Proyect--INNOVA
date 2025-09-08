#!/usr/bin/env python3
"""
Script para inicializar la base de datos con datos de ejemplo
"""

from app import create_app, db
from app.models import (
    User, PlanDesarrollo, LineaEstrategica, Componente,
    Programa, Proyecto, IndicadorProducto, EjecucionTrimestral
)
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_sample_data():
    """Crear datos de ejemplo para testing"""

    # Crear usuario administrador de ejemplo
    admin_user = User(
        username='admin',
        email='admin@alcaldia.com',
        first_name='Administrador',
        last_name='Sistema',
        position='Administrador del Sistema',
        municipality='Municipio de Ejemplo',
        department='Departamento de Ejemplo',
        role='admin'
    )
    admin_user.password = 'admin123'
    db.session.add(admin_user)
    db.session.commit()

    # Crear plan de desarrollo
    plan = PlanDesarrollo(
        titulo='Plan de Desarrollo Municipal 2024-2027',
        descripcion='Plan integral para el desarrollo sostenible del municipio',
        anio_inicio=2024,
        anio_fin=2027,
        presupuesto_total=10000000.00,
        prioridad='alta',
        municipio=admin_user
    )
    db.session.add(plan)
    db.session.commit()

    # Crear línea estratégica
    linea1 = LineaEstrategica(
        cod_linea=1,
        nombre='Desarrollo Económico Sostenible',
        descripcion='Fomentar el crecimiento económico inclusivo y sostenible',
        plan=plan,
        presupuesto_asignado=3000000.00
    )
    db.session.add(linea1)
    db.session.commit()

    # Crear componente
    componente1 = Componente(
        cod_componente=1.1,
        nombre='Fortalecimiento del Sector Productivo',
        descripcion='Apoyo a emprendimientos y MIPYMES',
        linea_estrategica=linea1,
        presupuesto_asignado=1500000.00
    )
    db.session.add(componente1)
    db.session.commit()

    # Crear programa
    programa1 = Programa(
        cod_programa='PDM-001',
        nombre='Programa de Apoyo a Emprendimientos',
        descripcion='Capacitación y financiamiento para nuevos emprendedores',
        dependencia_responsable='Dirección de Desarrollo Económico',
        componente=componente1,
        bpim='BPIM-2024-001'
    )
    db.session.add(programa1)
    db.session.commit()

    # Crear proyecto
    proyecto1 = Proyecto(
        nombre='Centro de Emprendimiento Municipal',
        descripcion='Construcción e implementación de un centro para apoyar emprendedores',
        programa=programa1,
        presupuesto_total=500000.00,
        ubicacion='Centro de la Ciudad',
        sector='Economía',
        responsable_ejecucion='Ing. María González',
        fecha_inicio=datetime(2024, 3, 1).date(),
        fecha_fin=datetime(2024, 12, 31).date()
    )
    db.session.add(proyecto1)
    db.session.commit()

    # Crear indicador de producto
    indicador1 = IndicadorProducto(
        cod_indicador='IP-001',
        nombre='Número de emprendedores capacitados',
        descripcion='Total de emprendedores que reciben capacitación técnica',
        tipo_indicador='Resultado',
        linea_base=50.0,
        sentido='positivo',
        tipologia='Cuantitativo',
        unidad='personas',
        meta_cuatrienio=500.0,
        meta_2024=150.0,
        proyecto=proyecto1
    )
    db.session.add(indicador1)
    db.session.commit()

    # Crear ejecución trimestral de ejemplo
    ejecucion1 = EjecucionTrimestral(
        anio=2024,
        trimestre=1,
        ejecucion_trimestral=35.0,
        ejecucion_acumulada=35.0,
        cumplimiento_trimestral=23.33,
        cumplimiento_acumulado=23.33,
        poblacion_impactada_trimestral=35,
        poblacion_impactada_acumulada=35,
        presupuesto_ejecutado_trimestral=87500.00,
        presupuesto_ejecutado_acumulado=87500.00,
        observacion_trimestral='Inicio satisfactorio del programa. Se capacitaron 35 emprendedores en temas básicos.',
        indicador=indicador1,
        proyecto=proyecto1,
        usuario=admin_user
    )
    db.session.add(ejecucion1)
    db.session.commit()

    print("✅ Datos de ejemplo creados exitosamente!")
    print("\nUsuario administrador:")
    print("  Usuario: admin")
    print("  Contraseña: admin123")
    print("  Email: admin@alcaldia.com")

def init_database():
    """Inicializar la base de datos"""
    app = create_app()

    with app.app_context():
        print("🔄 Creando tablas de la base de datos...")
        db.create_all()
        print("✅ Tablas creadas exitosamente!")

        # Verificar si ya existen datos
        if User.query.count() == 0:
            print("🔄 Creando datos de ejemplo...")
            create_sample_data()
        else:
            print("ℹ️  Los datos ya existen en la base de datos")

if __name__ == '__main__':
    init_database()
