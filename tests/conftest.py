"""Fixtures compartidas por la suite de pruebas.

Cada sesión de pruebas trabaja contra una base SQLite temporal creada desde
cero, de modo que las pruebas nunca tocan `instance/alcaldias_dev.db`.
"""

import contextlib
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CLAVE = 'Prueba.Segura123'


@pytest.fixture(scope='session')
def app():
    """Aplicación Flask configurada para pruebas, con una base temporal."""
    fd, ruta = tempfile.mkstemp(suffix='.db', prefix='innova_test_')
    os.close(fd)
    os.environ['DATABASE_URL'] = 'sqlite:///' + ruta.replace('\\', '/')

    from app import create_app, db, initialize_default_roles

    aplicacion = create_app('testing')
    aplicacion.config.update(WTF_CSRF_ENABLED=False, SERVER_NAME=None)

    # El esquema ya no se crea al arrancar la aplicación: se pide aquí igual
    # que haría `flask init-db`.
    with aplicacion.app_context():
        db.create_all()
        initialize_default_roles()

    yield aplicacion

    os.environ.pop('DATABASE_URL', None)
    with contextlib.suppress(OSError):
        os.unlink(ruta)


@pytest.fixture(scope='session')
def _datos(app):
    """Siembra un plan completo y un usuario por rol. Se ejecuta una sola vez."""
    from app import db
    from app.models import (
        Componente,
        EjecucionTrimestral,
        IndicadorProducto,
        LineaEstrategica,
        PlanDesarrollo,
        Programa,
        Proyecto,
        Role,
        User,
        UserRole,
    )

    with app.app_context():
        def crear_usuario(username, rol_nombre, legacy):
            usuario = User(
                username=username,
                email=f'{username}@ejemplo.gov.co',
                first_name=username.capitalize(),
                last_name='Pruebas',
                municipality='Municipio de Pruebas',
                department='Valle del Cauca',
                legacy_role=legacy,
            )
            usuario.password = CLAVE
            db.session.add(usuario)
            db.session.commit()

            rol = Role.query.filter_by(name=rol_nombre).first()
            db.session.add(UserRole(user_id=usuario.id, role_id=rol.id, assigned_by=usuario.id))
            db.session.commit()
            return usuario.id

        ids = {
            'admin': crear_usuario('admin_test', 'Administrador', 'admin'),
            'editor': crear_usuario('editor_test', 'Editor General', 'editor'),
            'ejecucion': crear_usuario('ejecucion_test', 'Editor de Ejecución', 'viewer'),
            'viewer': crear_usuario('viewer_test', 'Visualizador', 'viewer'),
        }

        plan = PlanDesarrollo(
            titulo='Plan de Desarrollo de Pruebas 2024-2027',
            descripcion='Plan usado por la suite de pruebas',
            anio_inicio=2024,
            anio_fin=2027,
            municipio_id=ids['admin'],
            estado='activo',
        )
        db.session.add(plan)
        db.session.commit()

        linea = LineaEstrategica(cod_linea=1, nombre='Línea de Pruebas', plan_id=plan.id)
        db.session.add(linea)
        db.session.commit()

        componente = Componente(cod_componente=1.1, nombre='Componente de Pruebas',
                                linea_estrategica_id=linea.id)
        db.session.add(componente)
        db.session.commit()

        programa = Programa(cod_programa='PDM-001', nombre='Programa de Pruebas',
                            componente_id=componente.id, dependencia_responsable='Planeación',
                            bpim='BPIM-001')
        db.session.add(programa)
        db.session.commit()

        proyecto = Proyecto(nombre='Proyecto de Pruebas', programa_id=programa.id)
        db.session.add(proyecto)
        db.session.commit()

        # Tres indicadores en el mismo proyecto: la matriz debe mostrar tres filas.
        indicadores = []
        for numero in (1, 2, 3):
            indicador = IndicadorProducto(
                cod_indicador=f'IND-{numero:03d}',
                nombre=f'Indicador de producto {numero}',
                proyecto_id=proyecto.id,
                unidad='Número',
                linea_base=0.0,
                meta_cuatrienio=100.0,
                meta_2024=40.0,
            )
            db.session.add(indicador)
            db.session.commit()
            indicadores.append(indicador.id)

        # Ejecución de los cuatro trimestres del primer indicador.
        for trimestre in (1, 2, 3, 4):
            db.session.add(EjecucionTrimestral(
                indicador_id=indicadores[0], anio=2024, trimestre=trimestre,
                ejecucion_trimestral=10.0, cumplimiento_trimestral=25.0,
                poblacion_impactada_trimestral=100, usuario_id=ids['admin'],
            ))
        db.session.commit()

        # Un plan aparte, para comprobar el aislamiento entre planes.
        plan_ajeno = PlanDesarrollo(titulo='Plan Ajeno', anio_inicio=2024, anio_fin=2027,
                                    municipio_id=ids['admin'])
        db.session.add(plan_ajeno)
        db.session.commit()
        linea_ajena = LineaEstrategica(cod_linea=9, nombre='Línea ajena', plan_id=plan_ajeno.id)
        db.session.add(linea_ajena)
        db.session.commit()
        comp_ajeno = Componente(cod_componente=9.1, nombre='Comp ajeno',
                                linea_estrategica_id=linea_ajena.id)
        db.session.add(comp_ajeno)
        db.session.commit()
        prog_ajeno = Programa(cod_programa='PDM-999', nombre='Prog ajeno',
                              componente_id=comp_ajeno.id)
        db.session.add(prog_ajeno)
        db.session.commit()
        proy_ajeno = Proyecto(nombre='Proy ajeno', programa_id=prog_ajeno.id)
        db.session.add(proy_ajeno)
        db.session.commit()
        ind_ajeno = IndicadorProducto(cod_indicador='IND-999', nombre='Indicador ajeno',
                                      proyecto_id=proy_ajeno.id, meta_2024=10.0)
        db.session.add(ind_ajeno)
        db.session.commit()

        return {
            'usuarios': ids,
            'plan_id': plan.id,
            'linea_id': linea.id,
            'componente_id': componente.id,
            'programa_id': programa.id,
            'proyecto_id': proyecto.id,
            'indicadores': indicadores,
            'plan_ajeno_id': plan_ajeno.id,
            'indicador_ajeno_id': ind_ajeno.id,
        }


@pytest.fixture
def datos(_datos):
    """Identificadores de los datos sembrados."""
    return _datos


@pytest.fixture
def contexto(app):
    """Contexto de aplicación activo, para pruebas que usan los modelos."""
    with app.app_context():
        yield


@pytest.fixture
def cliente(app):
    """Cliente HTTP sin autenticar."""
    return app.test_client()


@pytest.fixture
def sesion(app, datos):
    """Devuelve una función que entrega un cliente autenticado como el rol pedido."""
    def _entrar(rol='admin'):
        cliente = app.test_client()
        with cliente.session_transaction() as sesion_http:
            sesion_http['_user_id'] = str(datos['usuarios'][rol])
            sesion_http['_fresh'] = True
        return cliente

    return _entrar


@pytest.fixture
def admin(sesion):
    """Cliente autenticado como administrador."""
    return sesion('admin')
