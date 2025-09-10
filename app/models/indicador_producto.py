from app import db
from datetime import datetime

class IndicadorProducto(db.Model):
    __tablename__ = 'indicadores_producto'

    id = db.Column(db.Integer, primary_key=True)
    cod_indicador = db.Column(db.String(50))  # CÓD INDICADOR DE PRODUCTO
    nombre = db.Column(db.String(200), nullable=False)  # INDICADOR DE PRODUCTO
    descripcion = db.Column(db.Text)

    # Características del indicador
    tipo_indicador = db.Column(db.String(100))  # TIPO DE INDICADOR
    linea_base = db.Column(db.Float, default=0.0)  # LINEA BASE
    sentido = db.Column(db.String(50))  # SENTIDO (positivo, negativo, neutral)
    tipologia = db.Column(db.String(100))  # TIPOLOGÍA
    unidad = db.Column(db.String(50))  # UNIDAD

    # Metas
    meta_cuatrienio = db.Column(db.Float, default=0.0)  # META CUATRIENIO (2024-2027)
    meta_2024 = db.Column(db.Float, default=0.0)  # META 2024

    # Relación con proyecto
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyectos.id'), nullable=False)
    proyecto = db.relationship('Proyecto', backref=db.backref('indicadores', lazy=True, cascade='all, delete-orphan'))

    # Estado y timestamps
    estado = db.Column(db.String(20), default='activo')  # activo, inactivo
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, **kwargs):
        super(IndicadorProducto, self).__init__(**kwargs)
        if self.estado not in ['activo', 'inactivo']:
            self.estado = 'activo'
        if self.sentido not in ['positivo', 'negativo', 'neutral']:
            self.sentido = 'positivo'

    def get_progreso_porcentual(self):
        """Calcula el progreso porcentual del indicador"""
        try:
            if not self.meta_cuatrienio or self.meta_cuatrienio <= 0:
                return 0.0

            # Obtener la ejecución acumulada más reciente
            ultima_ejecucion = self.get_ultima_ejecucion()
            if ultima_ejecucion and ultima_ejecucion.ejecucion_acumulada is not None:
                progreso = (ultima_ejecucion.ejecucion_acumulada / self.meta_cuatrienio) * 100
                return min(max(progreso, 0.0), 100.0)

            return 0.0
        except (TypeError, ZeroDivisionError, AttributeError):
            return 0.0

    def get_ultima_ejecucion(self):
        """Obtiene la última ejecución trimestral registrada"""
        from app.models.ejecucion_trimestral import EjecucionTrimestral
        return EjecucionTrimestral.query.filter_by(indicador_id=self.id).order_by(
            db.desc(EjecucionTrimestral.anio),
            db.desc(EjecucionTrimestral.trimestre)
        ).first()

    def get_ejecuciones_por_anio(self, anio):
        """Obtiene todas las ejecuciones de un año específico"""
        from app.models.ejecucion_trimestral import EjecucionTrimestral
        return EjecucionTrimestral.query.filter_by(
            indicador_id=self.id,
            anio=anio
        ).order_by(EjecucionTrimestral.trimestre).all()

    def __repr__(self):
        return f'<IndicadorProducto {self.nombre}>'
