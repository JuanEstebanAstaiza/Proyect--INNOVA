"""La aplicación arranca, siembra sus roles y todas las plantillas compilan."""

import pytest


def test_la_aplicacion_se_crea(app):
    assert app is not None
    assert app.config['TESTING'] is True


def test_se_registran_los_cinco_blueprints(app):
    assert set(app.blueprints) == {'auth', 'main', 'planes', 'admin', 'audit'}


def test_todas_las_plantillas_compilan(app):
    """Una plantilla con un {% endfor %} de más rompía /admin/users/<id>/temp-password."""
    entorno = app.jinja_env
    plantillas = entorno.list_templates()
    assert len(plantillas) > 40

    errores = []
    for nombre in plantillas:
        try:
            entorno.get_template(nombre)
        except Exception as exc:
            errores.append(f'{nombre}: {exc}')

    assert not errores, 'Plantillas que no compilan:\n' + '\n'.join(errores)


def test_una_base_nueva_recibe_los_roles_por_defecto(contexto):
    """Antes fallaba: ColumnPermission no estaba importado en role.py."""
    from app.models import Role

    roles = {rol.name for rol in Role.query.all()}
    assert roles == {
        'Administrador', 'Editor General', 'Editor de Ejecución',
        'Editor de Metas', 'Visualizador',
    }


@pytest.mark.parametrize(
    ('nombre_rol', 'editables_esperadas'),
    [('Administrador', 37), ('Visualizador', 0)],
)
def test_cada_rol_tiene_las_37_columnas(contexto, nombre_rol, editables_esperadas):
    """Los roles de sistema también necesitan sus permisos de columna."""
    from app.models import Role

    rol = Role.query.filter_by(name=nombre_rol).first()
    assert len(rol.column_permissions) == 37
    assert len(rol.get_viewable_columns()) == 37
    assert len(rol.get_editable_columns()) == editables_esperadas


def test_el_editor_general_puede_editar_casi_todo(contexto):
    from app.models import Role

    rol = Role.query.filter_by(name='Editor General').first()
    editables = rol.get_editable_columns()
    assert len(editables) > 30
    assert 'DEPENDENCIA RESPOSABLE' not in editables


def test_las_categorias_de_columna_se_asignan_con_tildes(contexto):
    """'POBLACIÓN' y 'OBSERVACIÓN' llevan tilde y caían en la categoría 'ejecucion'."""
    from app.models import ColumnPermission, Role

    rol = Role.query.filter_by(name='Administrador').first()
    por_nombre = {p.column_name: p.category for p in rol.column_permissions}

    assert por_nombre['POBLACIÓN IMPACTADA POR SECTOR I TRIMESTRE'] == 'poblacion'
    assert por_nombre['OBSERVACIÓN AL CUMPLIMIENTO II TRIMESTRE'] == 'observaciones'
    assert por_nombre['EJECUCIÓN I TRIMESTRE '] == 'ejecucion'
    assert por_nombre['% CUMPLIMIENTO I TRIMESTRE'] == 'cumplimiento'

    # La categoría se deduce aunque el nombre llegue vacío.
    assert ColumnPermission(column_name='').category == 'general'


def test_los_directorios_de_trabajo_existen(app):
    import os

    assert os.path.isdir(app.config['UPLOAD_FOLDER'])
    assert os.path.isdir(app.config['AUDIT_FILES_PATH'])
