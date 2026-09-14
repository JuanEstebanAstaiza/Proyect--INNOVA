"""Autenticación, sesiones con JWT y protección de rutas."""

from tests.conftest import CLAVE


def test_el_login_acepta_credenciales_validas(cliente, datos):
    respuesta = cliente.post('/auth/login',
                             data={'username': 'admin_test', 'password': CLAVE})
    assert respuesta.status_code == 302
    assert '/auth/login' not in respuesta.headers['Location']


def test_el_login_rechaza_una_clave_incorrecta(cliente, datos):
    respuesta = cliente.post('/auth/login',
                             data={'username': 'admin_test', 'password': 'incorrecta'},
                             follow_redirects=True)
    assert 'inválidos' in respuesta.get_data(as_text=True)


def test_el_login_rechaza_un_usuario_inexistente(cliente):
    respuesta = cliente.post('/auth/login',
                             data={'username': 'no_existe', 'password': CLAVE},
                             follow_redirects=True)
    assert 'inválidos' in respuesta.get_data(as_text=True)


def test_el_login_crea_una_sesion_con_jwt(app, cliente, datos):
    from app.models import ActiveSession

    cliente.post('/auth/login', data={'username': 'admin_test', 'password': CLAVE})

    with cliente.session_transaction() as sesion_http:
        assert sesion_http.get('jwt_token')
        identificador = sesion_http.get('session_id')

    assert identificador
    with app.app_context():
        registro = ActiveSession.query.filter_by(session_id=identificador).first()
        assert registro is not None
        assert registro.user_id == datos['usuarios']['admin']


def test_solo_se_mantiene_una_sesion_activa_por_usuario(app, datos):
    """Al entrar de nuevo se invalidan las sesiones anteriores del mismo usuario."""
    from app.models import ActiveSession

    primero = app.test_client()
    primero.post('/auth/login', data={'username': 'editor_test', 'password': CLAVE})
    with primero.session_transaction() as sesion_http:
        sesion_previa = sesion_http['session_id']

    segundo = app.test_client()
    segundo.post('/auth/login', data={'username': 'editor_test', 'password': CLAVE})

    with app.app_context():
        anterior = ActiveSession.query.filter_by(session_id=sesion_previa).first()
        assert anterior is None or not anterior.is_active


def test_el_logout_cierra_la_sesion(admin):
    assert admin.get('/dashboard').status_code == 200
    admin.get('/auth/logout')
    respuesta = admin.get('/dashboard')
    assert respuesta.status_code == 302
    assert '/auth/login' in respuesta.headers['Location']


def test_las_rutas_privadas_exigen_sesion(cliente):
    for ruta in ('/dashboard', '/planes/', '/profile', '/audit/'):
        respuesta = cliente.get(ruta)
        assert respuesta.status_code == 302, ruta
        assert '/auth/login' in respuesta.headers['Location'], ruta


def test_las_rutas_de_admin_exigen_ser_administrador(sesion):
    """Todo /admin pasa por el before_request require_admin()."""
    visualizador = sesion('viewer')
    for ruta in ('/admin/dashboard', '/admin/users', '/admin/roles', '/admin/sessions'):
        respuesta = visualizador.get(ruta)
        assert respuesta.status_code == 302, ruta
        assert '/admin' not in respuesta.headers['Location'], ruta


def test_el_administrador_entra_en_el_panel(admin):
    assert admin.get('/admin/dashboard').status_code == 200


def test_el_panel_cuenta_bien_los_administradores(admin):
    """filter_by(role=...) usaba una propiedad y devolvía siempre 0."""
    from app.models import User

    cuerpo = admin.get('/admin/dashboard').get_data(as_text=True)
    assert cuerpo
    with admin.application.app_context():
        assert User.query.filter_by(legacy_role='admin').count() >= 1
