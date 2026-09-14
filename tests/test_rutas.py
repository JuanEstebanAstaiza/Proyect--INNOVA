"""Recorre todas las rutas GET autenticado como administrador.

Es la red de seguridad más amplia de la suite: detecta errores 500, plantillas
rotas y consultas mal construidas en cualquier vista del sistema.
"""

import re

import pytest

MARCADOR = re.compile(r'<(?:[a-z]+:)?([a-zA-Z_]+)>')

# Rutas que cambian el estado de la sesión o del plan y no deben recorrerse aquí.
EXCLUIDAS = {'auth.logout', 'planes.activar_plan', 'planes.desactivar_plan'}


def _construir_url(regla, valores):
    return MARCADOR.sub(lambda m: str(valores.get(m.group(1), 1)), str(regla))


def _reglas_get(app):
    return sorted(
        (r for r in app.url_map.iter_rules()
         if 'GET' in r.methods and r.endpoint != 'static' and r.endpoint not in EXCLUIDAS),
        key=str,
    )


@pytest.fixture
def valores(datos, app):
    with app.app_context():
        from app.models import Role
        rol = Role.query.first()

    return {
        'plan_id': datos['plan_id'],
        'linea_id': datos['linea_id'],
        'componente_id': datos['componente_id'],
        'programa_id': datos['programa_id'],
        'proyecto_id': datos['proyecto_id'],
        'indicador_id': datos['indicadores'][0],
        'user_id': datos['usuarios']['admin'],
        'role_id': rol.id,
        'permission_id': 1,
        'session_id': 1,
        'actividad_id': 1,
        'documento_id': 1,
        'entity_type': 'linea',
        'municipality': 'Municipio de Pruebas',
        'filename': 'inexistente.txt',
    }


def test_ninguna_ruta_get_devuelve_error_de_servidor(app, admin, valores):
    fallos = []

    for regla in _reglas_get(app):
        url = _construir_url(regla, valores)
        try:
            respuesta = admin.get(url)
        except Exception as exc:
            fallos.append(f'{url} ({regla.endpoint}) lanzó {type(exc).__name__}: {exc}')
            continue

        if respuesta.status_code >= 500:
            fallos.append(f'{url} ({regla.endpoint}) devolvió {respuesta.status_code}')

    assert not fallos, 'Rutas con error de servidor:\n' + '\n'.join(fallos)


def test_la_mayoria_de_rutas_get_responden_correctamente(app, admin, valores):
    """Además de no fallar, la mayor parte debe devolver contenido."""
    reglas = _reglas_get(app)
    correctas = sum(1 for r in reglas if admin.get(_construir_url(r, valores)).status_code < 400)
    assert correctas >= len(reglas) * 0.85, f'solo {correctas} de {len(reglas)} respondieron bien'


@pytest.mark.parametrize('ruta', [
    '/dashboard', '/planes/', '/profile', '/profile/edit', '/profile/change-password',
    '/admin/dashboard', '/admin/users', '/admin/roles', '/admin/user-roles',
    '/admin/sessions', '/admin/activities', '/admin/row-permissions',
    '/admin/user-row-permissions', '/admin/roles/guide', '/admin/smtp-config',
    '/audit/', '/audit/files', '/audit/admin',
])
def test_las_paginas_principales_responden_200(admin, valores, ruta):
    assert admin.get(ruta).status_code == 200


def test_las_paginas_del_plan_responden_200(admin, datos):
    rutas = [
        f'/planes/{datos["plan_id"]}',
        f'/planes/{datos["plan_id"]}/lineas',
        f'/planes/{datos["plan_id"]}/excel',
        f'/planes/{datos["plan_id"]}/documentos',
        f'/planes/lineas/{datos["linea_id"]}/detalles',
        f'/planes/lineas/{datos["linea_id"]}/componentes',
        f'/planes/componentes/{datos["componente_id"]}/detalles',
        f'/planes/componentes/{datos["componente_id"]}/programas',
        f'/planes/programas/{datos["programa_id"]}/detalles',
        f'/planes/programas/{datos["programa_id"]}/proyectos',
        f'/planes/proyectos/{datos["proyecto_id"]}/detalles',
        f'/planes/proyectos/{datos["proyecto_id"]}/indicadores',
    ]
    for ruta in rutas:
        assert admin.get(ruta).status_code == 200, ruta


def test_un_plan_inexistente_redirige_con_aviso(admin):
    """`ver` usa get_plan_or_redirect: avisa y vuelve al listado en vez de dar 404."""
    respuesta = admin.get('/planes/99999')
    assert respuesta.status_code == 302
    assert '/planes' in respuesta.headers['Location']


def test_una_entidad_inexistente_devuelve_404(admin):
    assert admin.get('/planes/lineas/99999/detalles').status_code == 404
    assert admin.get('/planes/proyectos/99999/detalles').status_code == 404
