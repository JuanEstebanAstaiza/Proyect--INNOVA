#!/usr/bin/env python3
"""
Script para inicializar la base de datos con datos de ejemplo
"""

from app import create_app, db
from app.models import (
    User, PlanDesarrollo, LineaEstrategica, Componente,
    Programa, Proyecto, IndicadorProducto, EjecucionTrimestral,
    ActivityLog, ActiveSession
)
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_sample_data():
    """Crear datos de ejemplo para testing"""

    # Crear usuarios de ejemplo con diferentes roles
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

    editor_user = User(
        username='editor',
        email='editor@alcaldia.com',
        first_name='Editor',
        last_name='Ejemplo',
        position='Editor de Planes',
        municipality='Municipio de Ejemplo',
        department='Departamento de Ejemplo',
        role='editor'
    )
    editor_user.password = 'editor123'
    db.session.add(editor_user)

    viewer_user = User(
        username='viewer',
        email='viewer@alcaldia.com',
        first_name='Visualizador',
        last_name='Ejemplo',
        position='Analista de Datos',
        municipality='Municipio de Ejemplo',
        department='Departamento de Ejemplo',
        role='viewer'
    )
    viewer_user.password = 'viewer123'
    db.session.add(viewer_user)

    db.session.commit()

    # Crear algunos registros de actividad de ejemplo
    ActivityLog.log_activity(
        'login',
        'Inicio de sesión del administrador',
        '127.0.0.1',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        user_id=admin_user.id
    )

    ActivityLog.log_activity(
        'create_plan',
        'Creación del Plan de Desarrollo Municipal 2024-2027',
        '127.0.0.1',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        user_id=admin_user.id
    )

    ActivityLog.log_activity(
        'login',
        'Inicio de sesión del editor',
        '192.168.1.100',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        user_id=editor_user.id
    )

    # Crear sesión activa de ejemplo
    active_session = ActiveSession(
        user_id=admin_user.id,
        session_id='sample_session_123',
        ip_address='127.0.0.1',
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )
    db.session.add(active_session)
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
    print("\nUsuarios de prueba creados:")
    print("\n👑 ADMINISTRADOR:")
    print("  Usuario: admin")
    print("  Contraseña: admin123")
    print("  Email: admin@alcaldia.com")
    print("  Rol: Administrador del Sistema")
    print("\n✏️ EDITOR:")
    print("  Usuario: editor")
    print("  Contraseña: editor123")
    print("  Email: editor@alcaldia.com")
    print("  Rol: Editor de Planes")
    print("\n👁️ VISUALIZADOR:")
    print("  Usuario: viewer")
    print("  Contraseña: viewer123")
    print("  Email: viewer@alcaldia.com")
    print("  Rol: Analista de Datos")
    print("\n🔗 Acceso al Panel de Administrador:")
    print("  Solo el usuario 'admin' puede acceder al panel de administración")
    print("  URL: /admin/dashboard")

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
