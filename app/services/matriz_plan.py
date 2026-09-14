"""Recorrido de la matriz del Plan de Desarrollo.

La matriz del PDM lleva **una fila por indicador de producto**, repitiendo en
cada fila los datos de la jerarquía superior. Este módulo concentra ese
recorrido para que la vista Excel y la exportación no lo dupliquen: cuando
estaban duplicados, ambos tomaban solo el primer indicador de cada proyecto y el
resto del plan desaparecía.
"""

from typing import NamedTuple

# El seguimiento trimestral que muestra la matriz. El plan cubre 2024-2027,
# pero las columnas de la plantilla oficial son las del primer año.
ANIO_SEGUIMIENTO = 2024

TRIMESTRES = (1, 2, 3, 4)

# Encabezados de la plantilla oficial, en orden. Se conservan las erratas del
# archivo original ('RESPOSABLE', 'ITRIMESTRE') para que los Excel que ya usan
# las entidades sigan importándose sin retoques.
COLUMNAS_ESTRUCTURA = (
    'CÓD LINEA', 'LINEAS ESTRATEGICAS', 'CÓD COMPONENTE', 'COMPONENTES',
    'CÓD PROGRAMA', 'PROGRAMA PDM', 'DEPENDENCIA RESPOSABLE', 'BPIM',
    'NOMBRE PROYECTO',
)

COLUMNAS_INDICADOR = (
    'INDICADORES', 'CÓD INDICADOR DE PRODUCTO', 'INDICADOR DE PRODUCTO',
    'TIPO DE INDICADOR', 'LINEA BASE', 'SENTIDO', 'TIPOLOGÍA', 'UNIDAD',
    'META CUATRIENIO (2024-2027)', 'META 2024',
)


class FilaPlan(NamedTuple):
    """Una fila de la matriz: el camino completo hasta un indicador."""

    linea: object
    componente: object
    programa: object
    proyecto: object
    indicador: object | None
    ejecuciones: list


def recorrer_plan(plan, anio=ANIO_SEGUIMIENTO):
    """Genera una `FilaPlan` por cada indicador de producto del plan.

    Un proyecto sin indicadores produce una fila con `indicador=None`, para que
    no desaparezca de la matriz.
    """
    for linea in plan.lineas_estrategicas:
        for componente in linea.componentes:
            for programa in componente.programas:
                for proyecto in programa.proyectos:
                    for indicador in (proyecto.indicadores or [None]):
                        ejecuciones = (
                            indicador.get_ejecuciones_por_anio(anio) if indicador else []
                        )
                        yield FilaPlan(linea, componente, programa, proyecto,
                                       indicador, ejecuciones)


def _ejecucion_del_trimestre(ejecuciones, trimestre):
    return next((e for e in ejecuciones if e.trimestre == trimestre), None)


def valores_de_fila(fila):
    """Convierte una `FilaPlan` en valores planos, con claves neutras.

    Cada vista se encarga después de ponerles el nombre de columna que necesita
    (encabezado del Excel o clave para la plantilla HTML).
    """
    indicador = fila.indicador

    datos = {
        'cod_linea': fila.linea.cod_linea,
        'linea': fila.linea.nombre,
        'cod_componente': fila.componente.cod_componente,
        'componente': fila.componente.nombre,
        'cod_programa': fila.programa.cod_programa,
        'programa': fila.programa.nombre,
        'dependencia_responsable': fila.programa.dependencia_responsable or '',
        'bpim': fila.programa.bpim or '',
        'proyecto': fila.proyecto.nombre,
        'indicador': indicador.nombre if indicador else '',
        'cod_indicador': indicador.cod_indicador if indicador else '',
        'tipo_indicador': indicador.tipo_indicador if indicador else '',
        'linea_base': indicador.linea_base if indicador else 0.0,
        'sentido': indicador.sentido if indicador else '',
        'tipologia': indicador.tipologia if indicador else '',
        'unidad': indicador.unidad if indicador else '',
        'meta_cuatrienio': indicador.meta_cuatrienio if indicador else 0.0,
        'meta_2024': indicador.meta_2024 if indicador else 0.0,
        'indicador_id': indicador.id if indicador else None,
    }

    ejecucion, cumplimiento, poblacion, observacion = {}, {}, {}, {}
    for trimestre in TRIMESTRES:
        registro = _ejecucion_del_trimestre(fila.ejecuciones, trimestre)
        ejecucion[trimestre] = registro.ejecucion_trimestral if registro else 0.0
        cumplimiento[trimestre] = registro.cumplimiento_trimestral if registro else 0.0
        poblacion[trimestre] = registro.poblacion_impactada_trimestral if registro else 0
        observacion[trimestre] = registro.observacion_trimestral if registro else ''

    datos['ejecucion'] = ejecucion
    datos['cumplimiento'] = cumplimiento
    datos['poblacion'] = poblacion
    datos['observacion'] = observacion

    # Los acumulados se calculan al vuelo a partir de los cuatro trimestres.
    ejecucion_acumulada = sum(ejecucion.values())
    meta = datos['meta_2024'] or 0.0
    datos['ejecucion_acumulada'] = ejecucion_acumulada
    datos['cumplimiento_acumulado'] = (
        ejecucion_acumulada / meta * 100 if meta > 0 else 0.0
    )
    datos['poblacion_acumulada'] = sum(poblacion.values())

    return datos


def fila_para_exportacion(fila):
    """Devuelve la fila con los encabezados exactos de la plantilla oficial."""
    v = valores_de_fila(fila)

    registro = {
        'CÓD LINEA': v['cod_linea'],
        'LINEAS ESTRATEGICAS': v['linea'],
        'CÓD COMPONENTE': v['cod_componente'],
        'COMPONENTES': v['componente'],
        'CÓD PROGRAMA': v['cod_programa'],
        'PROGRAMA PDM': v['programa'],
        'DEPENDENCIA RESPOSABLE': v['dependencia_responsable'],
        'BPIM': v['bpim'],
        'NOMBRE PROYECTO': v['proyecto'],
        'INDICADORES': v['indicador'],
        'CÓD INDICADOR DE PRODUCTO': v['cod_indicador'],
        'INDICADOR DE PRODUCTO': v['indicador'],
        'TIPO DE INDICADOR': v['tipo_indicador'],
        'LINEA BASE': v['linea_base'],
        'SENTIDO': v['sentido'],
        'TIPOLOGÍA': v['tipologia'],
        'UNIDAD': v['unidad'],
        'META CUATRIENIO (2024-2027)': v['meta_cuatrienio'],
        'META 2024': v['meta_2024'],
    }

    for trimestre in TRIMESTRES:
        registro[f'EJECUCIÓN {trimestre} TRIMESTRE'] = v['ejecucion'][trimestre]
        registro[f'% CUMPLIMIENTO {trimestre} TRIMESTRE'] = v['cumplimiento'][trimestre]
        registro[f'POBLACIÓN IMPACTADA POR SECTOR {trimestre} TRIMESTRE'] = v['poblacion'][trimestre]
        registro[f'OBSERVACIÓN AL CUMPLIMIENTO {trimestre}TRIMESTRE'] = v['observacion'][trimestre]

    registro['EJECUCIÓN ACUMULADA'] = v['ejecucion_acumulada']
    registro['% CUMPLIMIENTO ACUMULADO'] = v['cumplimiento_acumulado']
    registro['POBLACIÓN IMPACTADA ACUMULADA'] = v['poblacion_acumulada']
    registro['OBSERVACIÓN ACUMULADA'] = 'Consolidado anual'

    return registro


def fila_para_vista(fila):
    """Devuelve la fila con las claves que espera la plantilla `excel_view.html`."""
    v = valores_de_fila(fila)

    registro = {
        'cod_linea': v['cod_linea'],
        'lineas_estrategicas': v['linea'],
        'cod_componente': v['cod_componente'],
        'componentes': v['componente'],
        'cod_programa': v['cod_programa'],
        'programa_pdm': v['programa'],
        'dependencia_responsable': v['dependencia_responsable'],
        'bpim': v['bpim'],
        'nombre_proyecto': v['proyecto'],
        'indicadores': v['indicador'],
        'cod_indicador_de_producto': v['cod_indicador'],
        'indicador_de_producto': v['indicador'],
        'tipo_de_indicador': v['tipo_indicador'],
        'linea_base': v['linea_base'],
        'sentido': v['sentido'],
        'tipologia': v['tipologia'],
        'unidad': v['unidad'],
        'meta_cuatrienio': v['meta_cuatrienio'],
        'meta_2024': v['meta_2024'],
    }

    for trimestre in TRIMESTRES:
        registro[f'ejecucion_{trimestre}_trimestre'] = v['ejecucion'][trimestre]
        registro[f'cumplimiento_{trimestre}_trimestre'] = v['cumplimiento'][trimestre]
        registro[f'poblacion_impactada_{trimestre}_trimestre'] = v['poblacion'][trimestre]
        registro[f'observacion_{trimestre}_trimestre'] = v['observacion'][trimestre]

    registro['ejecucion_acumulada'] = v['ejecucion_acumulada']
    registro['cumplimiento_acumulado'] = v['cumplimiento_acumulado']
    registro['poblacion_impactada_acumulada'] = v['poblacion_acumulada']
    registro['observacion_acumulada'] = 'Consolidado anual'

    return registro
