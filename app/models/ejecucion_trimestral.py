from datetime import datetime

from app import db
from app.utils.fechas import ahora_utc


class EjecucionTrimestral(db.Model):
    __tablename__ = 'ejecuciones_trimestrales'

    id = db.Column(db.Integer, primary_key=True)

    # Período
    anio = db.Column(db.Integer, nullable=False)
    trimestre = db.Column(db.Integer, nullable=False)  # 1, 2, 3, 4

    # Ejecución física
    ejecucion_trimestral = db.Column(db.Float, default=0.0)  # EJECUCIÓN I TRIMESTRE, etc.
    ejecucion_acumulada = db.Column(db.Float, default=0.0)  # EJECUCIÓN ACUMULADA

    # Cumplimiento porcentual
    cumplimiento_trimestral = db.Column(db.Float, default=0.0)  # % CUMPLIMIENTO I TRIMESTRE, etc.
    cumplimiento_acumulado = db.Column(db.Float, default=0.0)  # % CUMPLIMIENTO ACUMULADO

    # Población impactada
    poblacion_impactada_trimestral = db.Column(db.Integer, default=0)  # POBLACIÓN IMPACTADA POR SECTOR I TRIMESTRE
    poblacion_impactada_acumulada = db.Column(db.Integer, default=0)  # Total acumulado

    # Presupuesto ejecutado
    presupuesto_ejecutado_trimestral = db.Column(db.Float, default=0.0)
    presupuesto_ejecutado_acumulado = db.Column(db.Float, default=0.0)

    # Observaciones
    observacion_trimestral = db.Column(db.Text)  # OBSERVACIÓN AL CUMPLIMIENTO I TRIMESTRE, etc.
    observacion_acumulada = db.Column(db.Text)  # Observaciones generales

    # Relaciones
    indicador_id = db.Column(db.Integer, db.ForeignKey('indicadores_producto.id'), nullable=True)
    indicador = db.relationship('IndicadorProducto', backref=db.backref('ejecuciones_trimestrales', lazy=True, cascade='all, delete-orphan'))

    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyectos.id'), nullable=True)
    proyecto = db.relationship('Proyecto', backref=db.backref('ejecuciones_trimestrales', lazy=True, cascade='all, delete-orphan'))

    # Usuario que registró la ejecución
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    usuario = db.relationship('User', backref=db.backref('ejecuciones_registradas', lazy=True))

    # Timestamps
    fecha_registro = db.Column(db.DateTime, default=ahora_utc)
    fecha_actualizacion = db.Column(db.DateTime, default=ahora_utc, onupdate=ahora_utc)

    # Metadatos
    fuente_informacion = db.Column(db.String(200))
    verificado = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not (1 <= self.trimestre <= 4):
            raise ValueError("El trimestre debe estar entre 1 y 4")

    @staticmethod
    def get_trimestre_actual():
        """Retorna el trimestre actual basado en la fecha"""
        now = datetime.now()
        month = now.month
        if month <= 3:
            return 1
        elif month <= 6:
            return 2
        elif month <= 9:
            return 3
        else:
            return 4

    def get_periodo_str(self):
        """Retorna una representación en string del período"""
        trimestres = {
            1: "I Trimestre",
            2: "II Trimestre",
            3: "III Trimestre",
            4: "IV Trimestre"
        }
        return f"{trimestres.get(self.trimestre, 'N/A')} {self.anio}"

    def calcular_cumplimiento(self):
        """Calcula automáticamente el porcentaje de cumplimiento"""
        if self.indicador and self.indicador.meta_cuatrienio > 0:
            self.cumplimiento_trimestral = (self.ejecucion_trimestral / self.indicador.meta_cuatrienio) * 100
            # Nota: El cumplimiento acumulado debería calcularse considerando metas acumuladas

    def __repr__(self):
        return f'<EjecucionTrimestral {self.get_periodo_str()} - Indicador: {self.indicador.nombre if self.indicador else "N/A"}>'
