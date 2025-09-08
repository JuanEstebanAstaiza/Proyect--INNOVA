from app import db
from datetime import datetime

class Programa(db.Model):
    __tablename__ = 'programas'

    id = db.Column(db.Integer, primary_key=True)
    cod_programa = db.Column(db.String(50), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)  # PROGRAMA PDM
    descripcion = db.Column(db.Text)

    # Responsable
    dependencia_responsable = db.Column(db.String(200))

    # Relación con componente
    componente_id = db.Column(db.Integer, db.ForeignKey('componentes.id'), nullable=False)
    componente = db.relationship('Componente', backref=db.backref('programas', lazy=True, cascade='all, delete-orphan'))

    # Estado y timestamps
    estado = db.Column(db.String(20), default='activo')  # activo, inactivo
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadatos
    bpim = db.Column(db.String(50))  # BPIM según el diccionario
    presupuesto_asignado = db.Column(db.Float, default=0.0)

    def __init__(self, **kwargs):
        super(Programa, self).__init__(**kwargs)
        if self.estado not in ['activo', 'inactivo']:
            self.estado = 'activo'

    def get_progreso(self):
        """Calcula el progreso del programa basado en sus proyectos"""
        proyectos = self.proyectos
        if not proyectos:
            return 0.0

        total_progreso = sum(proyecto.get_progreso() for proyecto in proyectos)
        return total_progreso / len(proyectos)

    def get_presupuesto_ejecutado(self):
        """Calcula el presupuesto ejecutado de todos los proyectos"""
        proyectos = self.proyectos
        return sum(proyecto.get_presupuesto_ejecutado() for proyecto in proyectos)

    def __repr__(self):
        return f'<Programa {self.cod_programa} - {self.nombre}>'
