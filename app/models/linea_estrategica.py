from app import db
from datetime import datetime

class LineaEstrategica(db.Model):
    __tablename__ = 'lineas_estrategicas'

    id = db.Column(db.Integer, primary_key=True)
    cod_linea = db.Column(db.Integer, nullable=False, unique=True)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)

    # Relación con el plan de desarrollo
    plan_id = db.Column(db.Integer, db.ForeignKey('planes_desarrollo.id'), nullable=False)
    plan = db.relationship('PlanDesarrollo', backref=db.backref('lineas_estrategicas', lazy=True, cascade='all, delete-orphan'))

    # Estado y timestamps
    estado = db.Column(db.String(20), default='activo')  # activo, inactivo
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadatos
    prioridad = db.Column(db.String(20), default='media')  # baja, media, alta, critica
    presupuesto_asignado = db.Column(db.Float, default=0.0)

    def __init__(self, **kwargs):
        super(LineaEstrategica, self).__init__(**kwargs)
        if self.estado not in ['activo', 'inactivo']:
            self.estado = 'activo'
        if self.prioridad not in ['baja', 'media', 'alta', 'critica']:
            self.prioridad = 'media'

    def get_progreso_general(self):
        """Calcula el progreso general de la línea estratégica basado en sus componentes"""
        componentes = self.componentes
        if not componentes:
            return 0.0

        total_progreso = sum(componente.get_progreso() for componente in componentes)
        return total_progreso / len(componentes)

    def get_presupuesto_ejecutado(self):
        """Calcula el presupuesto ejecutado de todos los componentes"""
        componentes = self.componentes
        return sum(componente.get_presupuesto_ejecutado() for componente in componentes)

    def __repr__(self):
        return f'<LineaEstrategica {self.cod_linea} - {self.nombre}>'
