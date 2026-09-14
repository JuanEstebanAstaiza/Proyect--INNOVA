"""Aislamiento entre entidades territoriales.

Un plan pertenece al municipio, no a la persona que lo creó: todos los
funcionarios de esa alcaldía deben verlo y ninguno de otra.
"""

import pytest

from tests.conftest import CLAVE


@pytest.fixture
def otro_municipio(app, datos):
    """Un usuario y un plan de una alcaldía distinta."""
    from app import db
    from app.models import PlanDesarrollo, Role, User, UserRole

    with app.app_context():
        forastero = User(
            username='forastero', email='forastero@otra.gov.co',
            first_name='Otro', last_name='Municipio',
            municipality='Palmira', department='Valle del Cauca',
            legacy_role='admin',
        )
        forastero.password = CLAVE
        db.session.add(forastero)
        db.session.commit()

        rol = Role.query.filter_by(name='Administrador').first()
        db.session.add(UserRole(user_id=forastero.id, role_id=rol.id, assigned_by=forastero.id))

        plan = PlanDesarrollo(titulo='Plan de Palmira', anio_inicio=2024, anio_fin=2027,
                              municipio_id=forastero.id)
        db.session.add(plan)
        db.session.commit()

        identificadores = {'usuario_id': forastero.id, 'plan_id': plan.id}

    yield identificadores

    with app.app_context():
        plan = db.session.get(PlanDesarrollo, identificadores['plan_id'])
        usuario = db.session.get(User, identificadores['usuario_id'])
        UserRole.query.filter_by(user_id=usuario.id).delete()
        db.session.delete(plan)
        db.session.delete(usuario)
        db.session.commit()


@pytest.fixture
def companiero(app, datos):
    """Otro funcionario del MISMO municipio que no creó el plan."""
    from app import db
    from app.models import Role, User, UserRole

    with app.app_context():
        usuario = User(
            username='control_interno', email='control@ejemplo.gov.co',
            first_name='Control', last_name='Interno',
            municipality='Municipio de Pruebas', department='Valle del Cauca',
            legacy_role='viewer',
        )
        usuario.password = CLAVE
        db.session.add(usuario)
        db.session.commit()

        rol = Role.query.filter_by(name='Visualizador').first()
        db.session.add(UserRole(user_id=usuario.id, role_id=rol.id, assigned_by=usuario.id))
        db.session.commit()
        identificador = usuario.id

    yield identificador

    with app.app_context():
        UserRole.query.filter_by(user_id=identificador).delete()
        db.session.delete(db.session.get(User, identificador))
        db.session.commit()


def _cliente_de(app, user_id):
    cliente = app.test_client()
    with cliente.session_transaction() as sesion:
        sesion['_user_id'] = str(user_id)
        sesion['_fresh'] = True
    return cliente


class TestMismoMunicipio:

    def test_un_companiero_ve_el_plan_que_creo_otro(self, app, datos, companiero):
        """El caso que motivó el cambio: Control Interno debe ver el plan de Planeación."""
        cliente = _cliente_de(app, companiero)
        assert cliente.get(f'/planes/{datos["plan_id"]}').status_code == 200
        assert cliente.get(f'/planes/{datos["plan_id"]}/excel').status_code == 200

    def test_el_plan_aparece_en_su_listado(self, app, datos, companiero):
        cuerpo = _cliente_de(app, companiero).get('/planes/').get_data(as_text=True)
        assert 'Plan de Desarrollo de Pruebas' in cuerpo

    def test_el_plan_activo_del_municipio_llega_al_dashboard(self, app, companiero):
        cuerpo = _cliente_de(app, companiero).get('/dashboard').get_data(as_text=True)
        assert 'Plan de Desarrollo de Pruebas' in cuerpo


class TestMunicipioAjeno:

    def test_no_se_ve_el_plan_de_otra_alcaldia(self, app, datos, otro_municipio):
        """Ni siquiera un administrador ve el plan de otro municipio."""
        cliente = _cliente_de(app, datos['usuarios']['admin'])
        respuesta = cliente.get(f'/planes/{otro_municipio["plan_id"]}')
        assert respuesta.status_code == 302

    def test_el_listado_no_incluye_planes_ajenos(self, app, datos, otro_municipio):
        cliente = _cliente_de(app, datos['usuarios']['admin'])
        cuerpo = cliente.get('/planes/').get_data(as_text=True)
        assert 'Plan de Palmira' not in cuerpo

    def test_el_forastero_solo_ve_el_suyo(self, app, datos, otro_municipio):
        cliente = _cliente_de(app, otro_municipio['usuario_id'])
        cuerpo = cliente.get('/planes/').get_data(as_text=True)
        assert 'Plan de Palmira' in cuerpo
        assert 'Plan de Desarrollo de Pruebas' not in cuerpo

    def test_no_se_importa_un_excel_sobre_un_plan_ajeno(self, app, datos, otro_municipio):
        """Importar apuntaba a cualquier plan por id, sin comprobar el municipio."""
        import io

        cliente = _cliente_de(app, datos['usuarios']['admin'])
        respuesta = cliente.post(
            f'/planes/{otro_municipio["plan_id"]}/importar-excel',
            data={'excel_file': (io.BytesIO(b'PK'), 'plan.xlsx')},
            content_type='multipart/form-data',
        )
        assert respuesta.status_code == 404

    def test_no_se_listan_las_lineas_de_un_plan_ajeno(self, app, datos, otro_municipio):
        cliente = _cliente_de(app, datos['usuarios']['admin'])
        assert cliente.get(f'/planes/{otro_municipio["plan_id"]}/lineas').status_code == 404

    def test_no_se_exporta_un_plan_ajeno(self, app, datos, otro_municipio):
        cliente = _cliente_de(app, datos['usuarios']['admin'])
        respuesta = cliente.get(f'/planes/{otro_municipio["plan_id"]}/exportar-excel')
        assert respuesta.status_code in (302, 404)


class TestConsultasDelModelo:

    def test_visibles_para_filtra_por_municipio(self, app, datos, otro_municipio):
        from app import db
        from app.models import PlanDesarrollo, User

        with app.app_context():
            local = db.session.get(User, datos['usuarios']['admin'])
            forastero = db.session.get(User, otro_municipio['usuario_id'])

            titulos_locales = {p.titulo for p in PlanDesarrollo.visibles_para(local)}
            titulos_ajenos = {p.titulo for p in PlanDesarrollo.visibles_para(forastero)}

            assert 'Plan de Palmira' not in titulos_locales
            assert titulos_ajenos == {'Plan de Palmira'}

    def test_es_visible_para_responde_correctamente(self, app, datos, otro_municipio):
        from app import db
        from app.models import PlanDesarrollo, User

        with app.app_context():
            plan_local = db.session.get(PlanDesarrollo, datos['plan_id'])
            local = db.session.get(User, datos['usuarios']['admin'])
            forastero = db.session.get(User, otro_municipio['usuario_id'])

            assert plan_local.es_visible_para(local) is True
            assert plan_local.es_visible_para(forastero) is False

    def test_el_plan_activo_se_busca_en_el_municipio(self, app, datos, companiero):
        from app import db
        from app.models import PlanDesarrollo, User

        with app.app_context():
            usuario = db.session.get(User, companiero)
            activo = PlanDesarrollo.get_plan_activo(usuario)
            assert activo is not None
            assert activo.id == datos['plan_id']
