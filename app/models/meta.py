from app import db
from datetime import datetime

class Meta(db.Model):
    __tablename__ = 'metas'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)

    # Tipo de meta
    tipo_meta = db.Column(db.String(50), nullable=False)  # cuantitativa, cualitativa, temporal

    # Valores para metas cuantitativas
    valor_actual = db.Column(db.Float, default=0.0)
    valor_objetivo = db.Column(db.Float, default=0.0)
    unidad_medida = db.Column(db.String(50))  # %, km, personas, etc.

    # Valores para metas cualitativas
    descripcion_actual = db.Column(db.Text)
    descripcion_objetivo = db.Column(db.Text)

    # Estado y progreso
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, en_progreso, completado, cancelado
    progreso_actual = db.Column(db.Float, default=0.0)  # porcentaje 0-100

    # Relaciones
    objetivo_id = db.Column(db.Integer, db.ForeignKey('objetivos.id'), nullable=False)
    objetivo = db.relationship('Objetivo', backref=db.backref('metas', lazy=True, cascade='all, delete-orphan'))

    # Fechas
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadatos
    responsable = db.Column(db.String(100))
    costo_estimado = db.Column(db.Float, default=0.0)

    def __init__(self, **kwargs):
        super(Meta, self).__init__(**kwargs)
        if self.tipo_meta not in ['cuantitativa', 'cualitativa', 'temporal']:
            self.tipo_meta = 'cuantitativa'
        if self.estado not in ['pendiente', 'en_progreso', 'completado', 'cancelado']:
            self.estado = 'pendiente'

    def get_progreso(self):
        """Calcula el progreso de la meta"""
        if self.tipo_meta == 'cuantitativa' and self.valor_objetivo > 0:
            return min((self.valor_actual / self.valor_objetivo) * 100, 100)
        return self.progreso_actual

    def actualizar_progreso(self):
        """Actualiza el progreso de la meta"""
        self.progreso_actual = self.get_progreso()
        db.session.commit()

    def esta_completada(self):
        """Verifica si la meta está completada"""
        if self.tipo_meta == 'cuantitativa':
            return self.valor_actual >= self.valor_objetivo
        return self.estado == 'completado'

    def __repr__(self):
        return f'<Meta {self.titulo} - {self.objetivo.titulo}>'
