
from app import db
from app.utils.fechas import ahora_utc


class Actividad(db.Model):
    __tablename__ = 'actividades'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)

    # Relación con proyecto
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyectos.id'), nullable=False)
    proyecto = db.relationship('Proyecto', backref=db.backref('actividades', lazy=True, cascade='all, delete-orphan'))

    # Estado y fechas
    estado = db.Column(db.String(20), default='planificada')  # planificada, en_progreso, completada, suspendida, cancelada
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)

    # Metadatos
    tipo_actividad = db.Column(db.String(100))  # construcción, capacitación, compra, etc.
    prioridad = db.Column(db.String(20), default='media')  # baja, media, alta, critica
    presupuesto_asignado = db.Column(db.Float, default=0.0)
    presupuesto_ejecutado = db.Column(db.Float, default=0.0)

    # Responsables
    responsable_ejecucion = db.Column(db.String(200))
    responsable_supervision = db.Column(db.String(200))

    # Progreso y seguimiento
    progreso_porcentual = db.Column(db.Float, default=0.0)  # 0-100
    observaciones = db.Column(db.Text)

    # Timestamps
    created_at = db.Column(db.DateTime, default=ahora_utc)
    updated_at = db.Column(db.DateTime, default=ahora_utc, onupdate=ahora_utc)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.estado not in ['planificada', 'en_progreso', 'completada', 'suspendida', 'cancelada']:
            self.estado = 'planificada'
        if self.prioridad not in ['baja', 'media', 'alta', 'critica']:
            self.prioridad = 'media'

    def get_presupuesto_restante(self):
        """Calcula el presupuesto restante"""
        return self.presupuesto_asignado - self.presupuesto_ejecutado

    def actualizar_progreso(self, nuevo_progreso):
        """Actualiza el progreso de la actividad"""
        if 0 <= nuevo_progreso <= 100:
            self.progreso_porcentual = nuevo_progreso
            db.session.commit()
            return True
        return False

    def marcar_completada(self):
        """Marca la actividad como completada"""
        self.estado = 'completada'
        self.progreso_porcentual = 100.0
        db.session.commit()

    def __repr__(self):
        return f'<Actividad {self.nombre} - {self.estado}>'
