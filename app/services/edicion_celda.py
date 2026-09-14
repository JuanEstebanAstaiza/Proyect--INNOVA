"""Lectura y escritura de una celda de la matriz del plan.

La vista Excel identifica cada celda por el nombre de columna que usa la
plantilla HTML (`meta_2024`, `ejecucion_3_trimestre`,
`poblacion_impactada_2_trimestre`...). Aquí se traduce ese nombre al campo real
del modelo, se valida el dato y se escribe.
"""

import re

from app import db
from app.models import EjecucionTrimestral
from app.services.matriz_plan import ANIO_SEGUIMIENTO

# Campos del indicador que deben guardarse como número.
CAMPOS_NUMERICOS_INDICADOR = ('linea_base', 'meta_cuatrienio', 'meta_2024')

# Prefijo de columna -> (campo de EjecucionTrimestral, conversión)
CAMPOS_TRIMESTRALES = {
    'ejecucion_': ('ejecucion_trimestral', float),
    'cumplimiento_': ('cumplimiento_trimestral', float),
    'poblacion_impactada_': ('poblacion_impactada_trimestral', int),
    'observacion_': ('observacion_trimestral', str),
}

# El número de trimestre va justo antes de '_trimestre'. Extraerlo con
# split('_')[1] fallaba en 'poblacion_impactada_2_trimestre', donde esa
# posición es 'impactada': la población impactada nunca llegaba a guardarse.
_TRIMESTRE = re.compile(r'_(\d)_trimestre$')


class ValorInvalido(ValueError):
    """El valor recibido no puede convertirse al tipo que espera la columna."""


def trimestre_de(nombre_columna):
    """Devuelve el número de trimestre de una columna, o None si no lleva."""
    encontrado = _TRIMESTRE.search(nombre_columna or '')
    return int(encontrado.group(1)) if encontrado else None


def campo_trimestral_de(nombre_columna):
    """Devuelve (campo del modelo, conversión) para una columna trimestral."""
    for prefijo, destino in CAMPOS_TRIMESTRALES.items():
        if nombre_columna.startswith(prefijo):
            return destino
    return None


def es_columna_trimestral(nombre_columna):
    return bool(campo_trimestral_de(nombre_columna)) and trimestre_de(nombre_columna) is not None


def _convertir(valor, conversion, nombre_columna):
    if conversion is str:
        return valor if valor is not None else ''
    if valor in (None, ''):
        return conversion(0)
    try:
        # Se pasa por float primero para aceptar '12.0' en columnas enteras.
        return conversion(float(valor))
    except (TypeError, ValueError) as exc:
        raise ValorInvalido(
            f"'{valor}' no es un número válido para la columna '{nombre_columna}'"
        ) from exc


def _buscar_ejecucion(indicador, trimestre, anio):
    return EjecucionTrimestral.query.filter_by(
        indicador_id=indicador.id, anio=anio, trimestre=trimestre,
    ).first()


def valor_actual(indicador, nombre_columna, anio=ANIO_SEGUIMIENTO):
    """Devuelve el valor que tiene ahora la celda, o None si no está definida."""
    if indicador is None:
        return None

    if hasattr(indicador, nombre_columna):
        return getattr(indicador, nombre_columna)

    destino = campo_trimestral_de(nombre_columna)
    trimestre = trimestre_de(nombre_columna)
    if destino and trimestre:
        ejecucion = _buscar_ejecucion(indicador, trimestre, anio)
        if ejecucion:
            return getattr(ejecucion, destino[0])

    return None


def aplicar_valor(indicador, nombre_columna, nuevo_valor, usuario_id,
                  anio=ANIO_SEGUIMIENTO):
    """Escribe el valor en el modelo correspondiente.

    Devuelve True si la celda se pudo asignar. Lanza `ValorInvalido` si el dato
    no encaja con el tipo de la columna, en lugar de guardar un cero silencioso.
    """
    if indicador is None:
        return False

    # --- Campo directo del indicador ---
    if hasattr(indicador, nombre_columna):
        if nombre_columna in CAMPOS_NUMERICOS_INDICADOR:
            setattr(indicador, nombre_columna, _convertir(nuevo_valor, float, nombre_columna))
        else:
            setattr(indicador, nombre_columna, nuevo_valor)
        return True

    # --- Campo de la ejecución trimestral ---
    destino = campo_trimestral_de(nombre_columna)
    trimestre = trimestre_de(nombre_columna)
    if not destino or not trimestre:
        return False

    campo, conversion = destino
    valor = _convertir(nuevo_valor, conversion, nombre_columna)

    ejecucion = _buscar_ejecucion(indicador, trimestre, anio)
    if ejecucion is None:
        ejecucion = EjecucionTrimestral(
            indicador_id=indicador.id,
            proyecto_id=indicador.proyecto_id,
            usuario_id=usuario_id,
            anio=anio,
            trimestre=trimestre,
        )
        db.session.add(ejecucion)

    setattr(ejecucion, campo, valor)

    # Al registrar la ejecución del trimestre, el cumplimiento se recalcula
    # contra la meta del año.
    if campo == 'ejecucion_trimestral' and (indicador.meta_2024 or 0) > 0:
        ejecucion.cumplimiento_trimestral = valor / indicador.meta_2024 * 100

    return True

# ---------------------------------------------------------------------------
# Traducción al nombre de columna de la matriz
#
# La plantilla HTML nombra las celdas en minúsculas ('meta_2024',
# 'ejecucion_1_trimestre'), pero los permisos de rol se guardan con el
# encabezado literal del Excel oficial ('META 2024', 'EJECUCIÓN I TRIMESTRE ').
# Sin esta traducción el permiso de columna nunca coincidía y no se aplicaba.
# ---------------------------------------------------------------------------

ROMANOS = {1: 'I', 2: 'II', 3: 'III', 4: 'IV'}

# Campos directos del indicador.
COLUMNAS_DEL_INDICADOR = {
    'nombre': 'INDICADOR DE PRODUCTO',
    'indicador_de_producto': 'INDICADOR DE PRODUCTO',
    'cod_indicador': 'CÓD INDICADOR DE PRODUCTO',
    'tipo_indicador': 'TIPO DE INDICADOR',
    'linea_base': 'LINEA BASE',
    'sentido': 'SENTIDO',
    'tipologia': 'TIPOLOGÍA',
    'unidad': 'UNIDAD',
    'meta_cuatrienio': 'META CUATRIENIO (2024-2027)',
    'meta_2024': 'META 2024',
}


def columna_de_la_matriz(nombre_columna):
    """Traduce la clave de la plantilla al encabezado del Excel, o None."""
    if nombre_columna in COLUMNAS_DEL_INDICADOR:
        return COLUMNAS_DEL_INDICADOR[nombre_columna]

    trimestre = trimestre_de(nombre_columna)
    if not trimestre:
        return None
    romano = ROMANOS[trimestre]

    if nombre_columna.startswith('ejecucion_'):
        return f'EJECUCIÓN {romano} TRIMESTRE '      # el encabezado lleva espacio final
    if nombre_columna.startswith('cumplimiento_'):
        return f'% CUMPLIMIENTO {romano} TRIMESTRE'
    if nombre_columna.startswith('poblacion_impactada_'):
        return f'POBLACIÓN IMPACTADA POR SECTOR {romano} TRIMESTRE'
    if nombre_columna.startswith('observacion_'):
        # En el Excel original el primer trimestre va pegado: 'ITRIMESTRE'.
        if trimestre == 1:
            return 'OBSERVACIÓN AL CUMPLIMIENTO ITRIMESTRE'
        return f'OBSERVACIÓN AL CUMPLIMIENTO {romano} TRIMESTRE'

    return None


def puede_editar(usuario, nombre_columna):
    """Indica si el usuario tiene permiso sobre la columna que quiere editar."""
    columna = columna_de_la_matriz(nombre_columna)
    if columna is not None:
        return usuario.can_edit_column(columna)

    # Columna fuera de la matriz oficial (por ejemplo 'descripcion'): se exige
    # al menos rol de edición.
    return usuario.is_admin() or usuario.is_editor()
