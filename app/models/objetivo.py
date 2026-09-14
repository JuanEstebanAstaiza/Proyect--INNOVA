
from app import db
from app.utils.fechas import ahora_utc


class Objetivo(db.Model):
    __tablename__ = 'objetivos'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)

    # Clasificación del objetivo
    tipo = db.Column(db.String(50), nullable=False)  # estrategico, operativo, tactico
    area = db.Column(db.String(100))  # economia, educacion, salud, infraestructura, etc.
    prioridad = db.Column(db.String(20), default='media')  # baja, media, alta

    # Estado y progreso
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, en_progreso, completado, cancelado
    progreso_actual = db.Column(db.Float, default=0.0)  # porcentaje 0-100

    # Relaciones
    plan_id = db.Column(db.Integer, db.ForeignKey('planes_desarrollo.id'), nullable=False)
    plan = db.relationship('PlanDesarrollo', backref=db.backref('objetivos', lazy=True, cascade='all, delete-orphan'))

    # Fechas
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=ahora_utc)
    updated_at = db.Column(db.DateTime, default=ahora_utc, onupdate=ahora_utc)

    # Metadatos
    responsable = db.Column(db.String(100))
    presupuesto_asignado = db.Column(db.Float, default=0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.tipo not in ['estrategico', 'operativo', 'tactico']:
            self.tipo = 'operativo'
        if self.prioridad not in ['baja', 'media', 'alta']:
            self.prioridad = 'media'
        if self.estado not in ['pendiente', 'en_progreso', 'completado', 'cancelado']:
            self.estado = 'pendiente'

    def get_progreso(self):
        """Calcula el progreso basado en las metas completadas"""
        metas = self.metas
        if not metas:
            return self.progreso_actual

        metas_completadas = sum(1 for meta in metas if meta.estado == 'completado')
        if metas_completadas > 0:
            progreso_metas = (metas_completadas / len(metas)) * 100
            # Promedio entre progreso manual y progreso de metas
            return (self.progreso_actual + progreso_metas) / 2
        return self.progreso_actual

    def actualizar_progreso(self):
        """Actualiza el progreso del objetivo"""
        self.progreso_actual = self.get_progreso()
        db.session.commit()

    def __repr__(self):
        return f'<Objetivo {self.titulo} - {self.plan.titulo}>'
