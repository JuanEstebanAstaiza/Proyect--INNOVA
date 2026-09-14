
from app import db
from app.utils.fechas import ahora_utc


class Indicador(db.Model):
    __tablename__ = 'indicadores'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)

    # Tipo de indicador
    tipo = db.Column(db.String(50), nullable=False)  # proceso, resultado, impacto
    categoria = db.Column(db.String(100))  # economico, social, ambiental, institucional

    # Configuración del indicador
    formula = db.Column(db.Text)  # fórmula de cálculo
    frecuencia_medicion = db.Column(db.String(20), default='mensual')  # diaria, semanal, mensual, trimestral, anual
    unidad_medida = db.Column(db.String(50))

    # Valores objetivo y actual
    valor_base = db.Column(db.Float, default=0.0)  # línea base
    valor_objetivo = db.Column(db.Float, default=0.0)  # valor objetivo
    valor_actual = db.Column(db.Float, default=0.0)  # último valor medido

    # Metas de progreso
    meta_anual = db.Column(db.Float, default=0.0)
    meta_acumulada = db.Column(db.Float, default=0.0)

    # Estado
    estado = db.Column(db.String(20), default='activo')  # activo, inactivo, suspendido

    # Relaciones
    meta_id = db.Column(db.Integer, db.ForeignKey('metas.id'), nullable=False)
    meta = db.relationship('Meta', backref=db.backref('indicadores', lazy=True, cascade='all, delete-orphan'))

    # Fechas
    fecha_ultima_medicion = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=ahora_utc)
    updated_at = db.Column(db.DateTime, default=ahora_utc, onupdate=ahora_utc)

    # Metadatos
    fuente_datos = db.Column(db.String(200))  # fuente de la información
    responsable_medicion = db.Column(db.String(100))
    observaciones = db.Column(db.Text)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.tipo not in ['proceso', 'resultado', 'impacto']:
            self.tipo = 'proceso'
        if self.frecuencia_medicion not in ['diaria', 'semanal', 'mensual', 'trimestral', 'anual']:
            self.frecuencia_medicion = 'mensual'
        if self.estado not in ['activo', 'inactivo', 'suspendido']:
            self.estado = 'activo'

    def get_progreso(self):
        """Calcula el progreso del indicador"""
        if self.valor_objetivo > 0:
            return ((self.valor_actual - self.valor_base) / (self.valor_objetivo - self.valor_base)) * 100
        return 0.0

    def get_tendencia(self):
        """Determina la tendencia del indicador"""
        progreso = self.get_progreso()
        if progreso >= 100:
            return 'alcanzado'
        elif progreso >= 75:
            return 'buena'
        elif progreso >= 50:
            return 'regular'
        elif progreso >= 25:
            return 'preocupante'
        else:
            return 'critica'

    def actualizar_valor(self, nuevo_valor, fecha=None):
        """Actualiza el valor del indicador"""
        self.valor_actual = nuevo_valor
        self.fecha_ultima_medicion = fecha or ahora_utc()
        db.session.commit()

    def __repr__(self):
        return f'<Indicador {self.nombre} - {self.meta.titulo}>'
