"""Las tres capas de control de acceso: rol, columna y fila."""

import pytest


@pytest.fixture
def usuarios(app, datos):
    """Instancias de User dentro de un contexto de aplicación."""
    from app import db
    from app.models import User

    with app.app_context():
        yield {clave: db.session.get(User, identificador)
               for clave, identificador in datos['usuarios'].items()}


class TestRoles:

    def test_el_administrador_se_reconoce_como_tal(self, usuarios):
        assert usuarios['admin'].is_admin() is True
        assert usuarios['viewer'].is_admin() is False

    def test_los_editores_se_reconocen_como_editores(self, usuarios):
        assert usuarios['editor'].is_editor() is True
        assert usuarios['ejecucion'].is_editor() is True
        assert usuarios['viewer'].is_editor() is False

    def test_has_role_no_distingue_mayusculas(self, usuarios):
        assert usuarios['admin'].has_role('administrador') is True
        assert usuarios['admin'].has_role('ADMINISTRADOR') is True
        assert usuarios['admin'].has_role('Visualizador') is False

    def test_sin_roles_asignados_se_usa_el_rol_legacy(self, app):
        """`legacy_role` es el respaldo cuando el usuario no tiene UserRole."""
        from app import db
        from app.models import User

        with app.app_context():
            suelto = User(username='suelto', email='suelto@ejemplo.gov.co',
                          first_name='Sin', last_name='Roles', municipality='X',
                          department='Y', legacy_role='admin')
            suelto.password = 'Clave.Segura123'
            db.session.add(suelto)
            db.session.commit()

            assert suelto.active_roles == []
            assert suelto.is_admin() is True

            db.session.delete(suelto)
            db.session.commit()


class TestPermisosDeColumna:

    def test_el_administrador_puede_editar_cualquier_columna(self, usuarios):
        for columna in ('META 2024', 'CÓD LINEA', 'DEPENDENCIA RESPOSABLE'):
            assert usuarios['admin'].can_edit_column(columna) is True

    def test_el_visualizador_no_puede_editar_ninguna(self, usuarios):
        for columna in ('META 2024', 'EJECUCIÓN I TRIMESTRE ', 'LINEAS ESTRATEGICAS'):
            assert usuarios['viewer'].can_edit_column(columna) is False

    def test_el_visualizador_si_puede_verlas_todas(self, usuarios):
        for columna in ('META 2024', 'EJECUCIÓN I TRIMESTRE ', 'LINEAS ESTRATEGICAS'):
            assert usuarios['viewer'].can_view_column(columna) is True

    def test_el_editor_de_ejecucion_solo_toca_su_ambito(self, usuarios):
        editor = usuarios['ejecucion']
        assert editor.can_edit_column('EJECUCIÓN I TRIMESTRE ') is True
        assert editor.can_edit_column('% CUMPLIMIENTO I TRIMESTRE') is True
        assert editor.can_edit_column('POBLACIÓN IMPACTADA POR SECTOR I TRIMESTRE') is True
        # La estructura del plan no le corresponde.
        assert editor.can_edit_column('LINEAS ESTRATEGICAS') is False
        assert editor.can_edit_column('CÓD LINEA') is False

    def test_el_editor_general_no_edita_la_dependencia_responsable(self, usuarios):
        """La columna real dice 'RESPOSABLE', sin la N: la regla debe cubrir ambas grafías."""
        assert usuarios['editor'].can_edit_column('DEPENDENCIA RESPOSABLE') is False

    def test_el_editor_general_edita_las_metas(self, usuarios):
        assert usuarios['editor'].can_edit_column('META 2024') is True
        assert usuarios['editor'].can_edit_column('INDICADOR DE PRODUCTO') is True


class TestPermisosDeFila:

    def test_el_administrador_no_necesita_permiso_de_fila(self, usuarios, datos):
        assert usuarios['admin'].can_edit_row(datos['indicadores'][0], datos['plan_id']) is True

    def test_sin_permiso_de_fila_un_visualizador_no_edita(self, usuarios, datos):
        assert usuarios['viewer'].can_edit_row(datos['indicadores'][0], datos['plan_id']) is False

    def test_un_permiso_de_fila_habilita_solo_su_rama(self, app, datos):
        """Un permiso sobre un indicador no alcanza a los demás del mismo proyecto."""
        from app import db
        from app.models import RowPermission, User

        with app.app_context():
            visualizador = db.session.get(User, datos['usuarios']['viewer'])
            permiso = RowPermission(
                user_id=visualizador.id,
                plan_id=datos['plan_id'],
                indicador_id=datos['indicadores'][0],
                permission_scope='indicador',
                can_view=True,
                can_edit=True,
                assigned_by=datos['usuarios']['admin'],
            )
            db.session.add(permiso)
            db.session.commit()

            try:
                assert visualizador.can_edit_row(datos['indicadores'][0], datos['plan_id']) is True
                assert visualizador.can_edit_row(datos['indicadores'][1], datos['plan_id']) is False
            finally:
                db.session.delete(permiso)
                db.session.commit()


class TestAislamientoEntreRoles:

    def test_un_visualizador_no_entra_en_el_panel_de_administracion(self, sesion):
        assert sesion('viewer').get('/admin/users').status_code == 302

    def test_un_editor_tampoco_entra_en_el_panel(self, sesion):
        assert sesion('editor').get('/admin/roles').status_code == 302

    def test_un_visualizador_si_consulta_el_plan(self, sesion, datos):
        assert sesion('viewer').get(f'/planes/{datos["plan_id"]}/excel').status_code == 200
