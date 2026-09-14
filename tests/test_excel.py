"""Vista de matriz, exportación, importación y edición de celdas con auditoría."""

import io

import pytest

openpyxl = pytest.importorskip('openpyxl')


def test_la_vista_excel_responde(admin, datos):
    respuesta = admin.get(f'/planes/{datos["plan_id"]}/excel')
    assert respuesta.status_code == 200


def test_la_matriz_muestra_una_fila_por_indicador(admin, datos):
    """Antes se tomaba `proyecto.indicadores[0]` y se perdía el resto del plan."""
    cuerpo = admin.get(f'/planes/{datos["plan_id"]}/excel').get_data(as_text=True)
    for numero in (1, 2, 3):
        assert f'Indicador de producto {numero}' in cuerpo


def _exportar(cliente, plan_id):
    respuesta = cliente.get(f'/planes/{plan_id}/exportar-excel')
    assert respuesta.status_code == 200
    assert 'spreadsheet' in respuesta.headers['Content-Type']
    return respuesta.get_data()


def test_la_exportacion_devuelve_un_xlsx_legible(admin, datos):
    libro = openpyxl.load_workbook(io.BytesIO(_exportar(admin, datos['plan_id'])))
    assert libro.active.title == 'Plan Desarrollo'


def test_la_exportacion_incluye_todos_los_indicadores(admin, datos):
    """Tres indicadores en un mismo proyecto deben dar tres filas más el encabezado."""
    hoja = openpyxl.load_workbook(io.BytesIO(_exportar(admin, datos['plan_id']))).active
    assert hoja.max_row == len(datos['indicadores']) + 1

    encabezados = [c.value for c in hoja[1]]
    nombres = {hoja.cell(row=f, column=encabezados.index('INDICADOR DE PRODUCTO') + 1).value
               for f in range(2, hoja.max_row + 1)}
    assert nombres == {f'Indicador de producto {n}' for n in (1, 2, 3)}


def test_la_exportacion_conserva_las_columnas_de_la_matriz(admin, datos):
    hoja = openpyxl.load_workbook(io.BytesIO(_exportar(admin, datos['plan_id']))).active
    encabezados = {c.value for c in hoja[1]}

    for columna in ('CÓD LINEA', 'LINEAS ESTRATEGICAS', 'CÓD COMPONENTE', 'PROGRAMA PDM',
                    'NOMBRE PROYECTO', 'INDICADOR DE PRODUCTO', 'META CUATRIENIO (2024-2027)',
                    'META 2024', 'EJECUCIÓN ACUMULADA', '% CUMPLIMIENTO ACUMULADO'):
        assert columna in encabezados, columna


def test_la_exportacion_calcula_la_ejecucion_acumulada(app, admin, datos):
    """La columna acumulada debe ser la suma de los cuatro trimestres."""
    from app.models import EjecucionTrimestral

    indicador_id = datos['indicadores'][0]
    with app.app_context():
        esperado = sum(e.ejecucion_trimestral or 0.0 for e in
                       EjecucionTrimestral.query.filter_by(indicador_id=indicador_id, anio=2024))

    hoja = openpyxl.load_workbook(io.BytesIO(_exportar(admin, datos['plan_id']))).active
    encabezados = [c.value for c in hoja[1]]
    col_codigo = encabezados.index('CÓD INDICADOR DE PRODUCTO') + 1
    col_acumulada = encabezados.index('EJECUCIÓN ACUMULADA') + 1

    for fila in range(2, hoja.max_row + 1):
        if hoja.cell(row=fila, column=col_codigo).value == 'IND-001':
            assert hoja.cell(row=fila, column=col_acumulada).value == pytest.approx(esperado)
            return
    pytest.fail('no se encontró la fila del primer indicador')


def test_la_importacion_acepta_lo_que_produce_la_exportacion(admin, datos):
    """Ida y vuelta: lo exportado debe volver a entrar sin perder filas."""
    contenido = _exportar(admin, datos['plan_id'])
    respuesta = admin.post(
        f'/planes/{datos["plan_id"]}/importar-excel',
        data={'excel_file': (io.BytesIO(contenido), 'plan.xlsx')},
        content_type='multipart/form-data', follow_redirects=True,
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.get_data(as_text=True)
    assert f'{len(datos["indicadores"])} filas' in cuerpo


def test_la_importacion_rechaza_un_archivo_que_no_es_excel(admin, datos):
    respuesta = admin.post(
        f'/planes/{datos["plan_id"]}/importar-excel',
        data={'excel_file': (io.BytesIO(b'no soy un excel'), 'notas.txt')},
        content_type='multipart/form-data', follow_redirects=True,
    )
    assert 'debe ser un Excel' in respuesta.get_data(as_text=True)


def test_la_importacion_avisa_si_no_llega_archivo(admin, datos):
    respuesta = admin.post(f'/planes/{datos["plan_id"]}/importar-excel',
                           data={}, follow_redirects=True)
    assert 'No se encontró el archivo' in respuesta.get_data(as_text=True)


class TestEdicionDeCelda:
    """POST /planes/<id>/editar-celda-excel"""

    @staticmethod
    def _editar(cliente, plan_id, indicador_id, valor, columna='nombre'):
        return cliente.post(f'/planes/{plan_id}/editar-celda-excel', data={
            'indicator_id': str(indicador_id),
            'column_name': columna,
            'new_value': valor,
            'justification': 'Ajuste solicitado por la Secretaría de Planeación',
        })

    def test_guarda_el_valor_nuevo(self, app, admin, datos):
        from app import db
        from app.models import IndicadorProducto

        indicador_id = datos['indicadores'][1]
        respuesta = self._editar(admin, datos['plan_id'], indicador_id, 'Valor verificado')

        assert respuesta.status_code == 200
        assert respuesta.get_json()['success'] is True

        with app.app_context():
            assert db.session.get(IndicadorProducto, indicador_id).nombre == 'Valor verificado'

    def test_deja_registro_de_la_justificacion(self, app, admin, datos):
        from app.models import EditJustification

        indicador_id = datos['indicadores'][2]
        self._editar(admin, datos['plan_id'], indicador_id, 'Con justificación')

        with app.app_context():
            registro = (EditJustification.query
                        .filter_by(indicador_id=indicador_id)
                        .order_by(EditJustification.id.desc()).first())
            assert registro is not None
            assert registro.new_value == 'Con justificación'
            assert 'Planeación' in registro.justification

    def test_exige_justificacion(self, admin, datos):
        respuesta = admin.post(f'/planes/{datos["plan_id"]}/editar-celda-excel', data={
            'indicator_id': str(datos['indicadores'][0]),
            'column_name': 'nombre',
            'new_value': 'Sin motivo',
        })
        assert respuesta.status_code == 400
        assert respuesta.get_json()['success'] is False

    def test_no_permite_editar_un_indicador_de_otro_plan(self, app, admin, datos):
        """Respondía «editada exitosamente» sin guardar nada."""
        from app import db
        from app.models import IndicadorProducto

        ajeno = datos['indicador_ajeno_id']
        respuesta = self._editar(admin, datos['plan_id'], ajeno, 'Secuestrado')

        assert respuesta.status_code == 404
        assert respuesta.get_json()['success'] is False

        with app.app_context():
            assert db.session.get(IndicadorProducto, ajeno).nombre == 'Indicador ajeno'

    def test_rechaza_un_indicador_inexistente(self, admin, datos):
        respuesta = self._editar(admin, datos['plan_id'], 999999, 'Fantasma')
        assert respuesta.status_code == 404
