"""Fecha y hora actuales en UTC.

`datetime.utcnow()` está obsoleto desde Python 3.12 y desaparecerá en una
versión futura. Su sustituto directo, `datetime.now(timezone.utc)`, devuelve un
valor **con** zona horaria, y las columnas de la base guardan valores *sin*
ella: mezclarlos hace que cualquier resta entre fechas falle con
``TypeError: can't subtract offset-naive and offset-aware datetimes``.

`ahora_utc()` calcula la hora en UTC de la forma moderna y le quita la zona,
de modo que el valor sigue siendo comparable con todo lo ya almacenado.
"""

from datetime import UTC, datetime

__all__ = ['ahora_utc']


def ahora_utc():
    """Devuelve la hora actual en UTC, sin zona horaria (como `utcnow`)."""
    return datetime.now(UTC).replace(tzinfo=None)
