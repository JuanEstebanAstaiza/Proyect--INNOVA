"""Traducción de nombres de columna a campos del modelo, y escritura de celdas."""

import pytest

from app.services.edicion_celda import (
    ValorInvalido,
    campo_trimestral_de,
    es_columna_trimestral,
    trimestre_de,
)


class TestLecturaDelNombreDeColumna:

    @pytest.mark.parametrize(('columna', 'esperado'), [
        ('ejecucion_1_trimestre', 1),
        ('cumplimiento_3_trimestre', 3),
        # Con split('_')[1] esta daba 'impactada' y el dato nunca se guardaba.
        ('poblacion_impactada_2_trimestre', 2),
        ('observacion_4_trimestre', 4),
        ('meta_2024', None),
        ('nombre', None),
        ('', None),
    ])
    def test_extrae_el_trimestre(self, columna, esperado):
        assert trimestre_de(columna) == esperado

    @pytest.mark.parametrize(('columna', 'campo'), [
        ('ejecucion_1_trimestre', 'ejecucion_trimestral'),
        ('cumplimiento_1_trimestre', 'cumplimiento_trimestral'),
        ('poblacion_impactada_1_trimestre', 'poblacion_impactada_trimestral'),
        ('observacion_1_trimestre', 'observacion_trimestral'),
    ])
    def test_traduce_al_campo_del_modelo(self, columna, campo):
        assert campo_trimestral_de(columna)[0] == campo

    def test_reconoce_las_columnas_trimestrales(self):
        assert es_columna_trimestral('poblacion_impactada_2_trimestre') is True
        assert es_columna_trimestral('meta_2024') is False


class TestEscrituraDeCeldas:
    """POST /planes/<id>/editar-celda-excel"""

    @staticmethod
    def _editar(cliente, plan_id, indicador_id, columna, valor):
        return cliente.post(f'/planes/{plan_id}/editar-celda-excel', data={
            'indicator_id': str(indicador_id),
            'column_name': columna,
            'new_value': valor,
            'justification': 'Registro del seguimiento trimestral',
        })

    def test_guarda_la_ejecucion_de_un_trimestre(self, app, admin, datos):
        from app.models import EjecucionTrimestral

        indicador_id = datos['indicadores'][1]
        respuesta = self._editar(admin, datos['plan_id'], indicador_id,
                                 'ejecucion_2_trimestre', '25')
        assert respuesta.status_code == 200

        with app.app_context():
            registro = EjecucionTrimestral.query.filter_by(
                indicador_id=indicador_id, anio=2024, trimestre=2).first()
            assert registro is not None
            assert registro.ejecucion_trimestral == pytest.approx(25.0)

    def test_recalcula_el_cumplimiento_al_guardar_la_ejecucion(self, app, admin, datos):
        """La meta del año es 40; ejecutar 10 debe dar 25 % de cumplimiento."""
        from app.models import EjecucionTrimestral

        indicador_id = datos['indicadores'][2]
        self._editar(admin, datos['plan_id'], indicador_id, 'ejecucion_3_trimestre', '10')

        with app.app_context():
            registro = EjecucionTrimestral.query.filter_by(
                indicador_id=indicador_id, anio=2024, trimestre=3).first()
            assert registro.cumplimiento_trimestral == pytest.approx(25.0)

    def test_guarda_la_poblacion_impactada(self, app, admin, datos):
        """Esta columna nunca llegaba a guardarse y la respuesta decía que sí."""
        from app.models import EjecucionTrimestral

        indicador_id = datos['indicadores'][1]
        respuesta = self._editar(admin, datos['plan_id'], indicador_id,
                                 'poblacion_impactada_3_trimestre', '1500')
        assert respuesta.status_code == 200

        with app.app_context():
            registro = EjecucionTrimestral.query.filter_by(
                indicador_id=indicador_id, anio=2024, trimestre=3).first()
            assert registro is not None
            assert registro.poblacion_impactada_trimestral == 1500

    def test_guarda_la_observacion_del_trimestre(self, app, admin, datos):
        from app.models import EjecucionTrimestral

        indicador_id = datos['indicadores'][2]
        self._editar(admin, datos['plan_id'], indicador_id,
                     'observacion_4_trimestre', 'Obra entregada en diciembre')

        with app.app_context():
            registro = EjecucionTrimestral.query.filter_by(
                indicador_id=indicador_id, anio=2024, trimestre=4).first()
            assert registro.observacion_trimestral == 'Obra entregada en diciembre'

    def test_guarda_la_meta_del_indicador(self, app, admin, datos):
        from app import db
        from app.models import IndicadorProducto

        indicador_id = datos['indicadores'][1]
        self._editar(admin, datos['plan_id'], indicador_id, 'meta_2024', '75.5')

        with app.app_context():
            assert db.session.get(IndicadorProducto, indicador_id).meta_2024 == pytest.approx(75.5)

    def test_rechaza_un_numero_mal_escrito(self, app, admin, datos):
        """Antes se guardaba 0.0 en silencio, falseando la cifra."""
        from app import db
        from app.models import IndicadorProducto

        indicador_id = datos['indicadores'][1]
        with app.app_context():
            antes = db.session.get(IndicadorProducto, indicador_id).meta_2024

        respuesta = self._editar(admin, datos['plan_id'], indicador_id, 'meta_2024', '1.5OO')
        assert respuesta.status_code == 400
        assert 'no es un número válido' in respuesta.get_json()['error']

        with app.app_context():
            assert db.session.get(IndicadorProducto, indicador_id).meta_2024 == pytest.approx(antes)

    def test_un_rol_sin_permiso_de_columna_recibe_403(self, sesion, datos):
        """El Editor de Ejecución no puede tocar la estructura del plan."""
        cliente = sesion('ejecucion')
        respuesta = self._editar(cliente, datos['plan_id'], datos['indicadores'][0],
                                 'nombre', 'Renombrado sin permiso')
        assert respuesta.status_code == 403

    def test_el_editor_de_ejecucion_si_registra_su_trimestre(self, sesion, datos):
        cliente = sesion('ejecucion')
        respuesta = self._editar(cliente, datos['plan_id'], datos['indicadores'][0],
                                 'ejecucion_1_trimestre', '12')
        assert respuesta.status_code == 200


def test_valor_invalido_es_un_error_de_valor():
    assert issubclass(ValorInvalido, ValueError)
