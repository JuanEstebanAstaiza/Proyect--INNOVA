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

    def activar(self):
        """Activa este plan y desactiva los demás del mismo municipio"""
        # Primero desactivar todos los planes activos del municipio
        PlanDesarrollo.query.filter_by(
            municipio=self.municipio,
            estado='activo'
        ).update({'estado': 'borrador'})

        # Luego activar este plan
        self.estado = 'activo'
        db.session.commit()

    def desactivar(self):
        """Desactiva este plan"""
        self.estado = 'borrador'
        db.session.commit()

    @classmethod
    def get_plan_activo(cls, municipio):
        """Obtiene el plan activo del municipio, o None si no hay ninguno"""
        return cls.query.filter_by(
            municipio=municipio,
            estado='activo'
        ).first()

    @classmethod
    def get_plan_activo_o_primero(cls, municipio):
        """Obtiene el plan activo, o si no hay ninguno, el más reciente"""
        plan_activo = cls.get_plan_activo(municipio)
        if plan_activo:
            return plan_activo

        # Si no hay plan activo, devolver el más reciente
        return cls.query.filter_by(municipio=municipio).order_by(
            cls.created_at.desc()
        ).first()

    def __repr__(self):
        return f'<PlanDesarrollo {self.titulo} - {self.municipio.municipality}>'
