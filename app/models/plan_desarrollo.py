from app import db
from datetime import datetime

class PlanDesarrollo(db.Model):
    __tablename__ = 'planes_desarrollo'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    anio_inicio = db.Column(db.Integer, nullable=False)
    anio_fin = db.Column(db.Integer, nullable=False)

    # Estado del plan
    estado = db.Column(db.String(20), default='borrador')  # borrador, activo, finalizado, cancelado

    # Relaciones
    municipio_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    municipio = db.relationship('User', backref=db.backref('planes_desarrollo', lazy=True))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadatos
    presupuesto_total = db.Column(db.Float, default=0.0)
    prioridad = db.Column(db.String(20), default='media')  # baja, media, alta, critica

    def __init__(self, **kwargs):
        super(PlanDesarrollo, self).__init__(**kwargs)
        if self.estado not in ['borrador', 'activo', 'finalizado', 'cancelado']:
            self.estado = 'borrador'
        if self.prioridad not in ['baja', 'media', 'alta', 'critica']:
            self.prioridad = 'media'

    def get_duracion(self):
        """Retorna la duración del plan en años"""
        return self.anio_fin - self.anio_inicio + 1

    def get_progreso_general(self):
        """Calcula el progreso general del plan basado en los objetivos"""
        objetivos = self.objetivos
        if not objetivos:
            return 0.0

        total_progreso = sum(obj.get_progreso() for obj in objetivos)
        return total_progreso / len(objetivos)

    def __repr__(self):
        return f'<PlanDesarrollo {self.titulo} - {self.municipio.municipality}>'
