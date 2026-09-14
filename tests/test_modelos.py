"""Comportamiento de los modelos: progreso, estado del plan y utilidades."""

import pytest


class TestProgresoDelPlan:

    def test_el_progreso_del_plan_promedia_sus_lineas(self, app, datos):
        """Se apoyaba en `self.objetivos`, un modelo que ya no se registra."""
        from app import db
        from app.models import PlanDesarrollo

        with app.app_context():
            plan = db.session.get(PlanDesarrollo, datos['plan_id'])
            progreso = plan.get_progreso_general()

        assert isinstance(progreso, float)
        assert 0.0 <= progreso <= 100.0

    def test_un_plan_sin_lineas_tiene_progreso_cero(self, app, datos):
        from app import db
        from app.models import PlanDesarrollo

        with app.app_context():
            vacio = PlanDesarrollo(titulo='Plan vacío', anio_inicio=2024, anio_fin=2027,
                                   municipio_id=datos['usuarios']['admin'])
            db.session.add(vacio)
            db.session.commit()
            try:
                assert vacio.get_progreso_general() == 0.0
            finally:
                db.session.delete(vacio)
                db.session.commit()

    def test_la_duracion_cuenta_los_dos_extremos(self, app, datos):
        from app import db
        from app.models import PlanDesarrollo

        with app.app_context():
            plan = db.session.get(PlanDesarrollo, datos['plan_id'])
            assert plan.get_duracion() == 4  # 2024, 2025, 2026 y 2027


class TestEstadoDelPlan:

    def test_activar_un_plan_desactiva_los_demas_del_municipio(self, app, datos):
        from app import db
        from app.models import PlanDesarrollo

        with app.app_context():
            otro = PlanDesarrollo(titulo='Segundo plan', anio_inicio=2024, anio_fin=2027,
                                  municipio_id=datos['usuarios']['admin'])
            db.session.add(otro)
            db.session.commit()

            try:
                otro.activar()
                db.session.refresh(otro)
                anterior = db.session.get(PlanDesarrollo, datos['plan_id'])
                db.session.refresh(anterior)

                assert otro.estado == 'activo'
                assert anterior.estado == 'borrador'
            finally:
                otro.estado = 'borrador'
                anterior = db.session.get(PlanDesarrollo, datos['plan_id'])
                anterior.estado = 'activo'
                db.session.delete(otro)
                db.session.commit()

    def test_el_estado_se_normaliza_al_crear(self, contexto):
        from app.models import PlanDesarrollo

        plan = PlanDesarrollo(titulo='X', anio_inicio=2024, anio_fin=2027,
                              municipio_id=1, estado='inventado')
        assert plan.estado == 'borrador'


class TestDocumento:

    @pytest.mark.parametrize(('bytes_', 'esperado'), [
        (0, '0.0 B'),
        (512, '512.0 B'),
        (1024, '1.0 KB'),
        (1536, '1.5 KB'),
        (1024 * 1024, '1.0 MB'),
        (5 * 1024 * 1024, '5.0 MB'),
        (2 * 1024 ** 3, '2.0 GB'),
    ])
    def test_el_tamano_se_muestra_legible(self, contexto, bytes_, esperado):
        """Devolvía la cadena literal '.1f' en lugar del tamaño."""
        from app.models import Documento

        documento = Documento(
            titulo='Acta', nombre_original='acta.pdf', nombre_archivo='acta.pdf',
            ruta_archivo='/tmp/acta.pdf', tamano=bytes_, tipo_mime='application/pdf',
            extension='pdf', tipo_documento='informe', usuario_id=1,
        )
        assert documento.get_tamano_legible() == esperado

    def test_consultar_el_tamano_no_lo_modifica(self, contexto):
        """El bucle dividía self.tamano y corrompía el valor guardado."""
        from app.models import Documento

        documento = Documento(
            titulo='Acta', nombre_original='acta.pdf', nombre_archivo='acta.pdf',
            ruta_archivo='/tmp/acta.pdf', tamano=5_242_880, tipo_mime='application/pdf',
            extension='pdf', tipo_documento='informe', usuario_id=1,
        )
        documento.get_tamano_legible()
        documento.get_tamano_legible()
        assert documento.tamano == 5_242_880


class TestEjecucionTrimestral:

    def test_el_periodo_se_describe_con_el_trimestre(self, app, datos):
        from app.models import EjecucionTrimestral

        with app.app_context():
            registro = EjecucionTrimestral.query.filter_by(
                indicador_id=datos['indicadores'][0], trimestre=1).first()
            assert '2024' in registro.get_periodo_str()
