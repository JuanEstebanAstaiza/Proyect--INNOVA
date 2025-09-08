from app import db
from datetime import datetime

class Componente(db.Model):
    __tablename__ = 'componentes'

    id = db.Column(db.Integer, primary_key=True)
    cod_componente = db.Column(db.Float, nullable=False)  # Puede ser decimal según el diccionario
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)

    # Relación con línea estratégica
    linea_estrategica_id = db.Column(db.Integer, db.ForeignKey('lineas_estrategicas.id'), nullable=False)
    linea_estrategica = db.relationship('LineaEstrategica', backref=db.backref('componentes', lazy=True, cascade='all, delete-orphan'))

    # Estado y timestamps
    estado = db.Column(db.String(20), default='activo')  # activo, inactivo
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadatos
    prioridad = db.Column(db.String(20), default='media')  # baja, media, alta, critica
    presupuesto_asignado = db.Column(db.Float, default=0.0)

    def __init__(self, **kwargs):
        super(Componente, self).__init__(**kwargs)
        if self.estado not in ['activo', 'inactivo']:
            self.estado = 'activo'
        if self.prioridad not in ['baja', 'media', 'alta', 'critica']:
            self.prioridad = 'media'

    def get_progreso(self):
        """Calcula el progreso del componente basado en sus programas"""
        programas = self.programas
        if not programas:
            return 0.0

        total_progreso = sum(programa.get_progreso() for programa in programas)
        return total_progreso / len(programas)

    def get_presupuesto_ejecutado(self):
        """Calcula el presupuesto ejecutado de todos los programas"""
        programas = self.programas
        return sum(programa.get_presupuesto_ejecutado() for programa in programas)

    def __repr__(self):
        return f'<Componente {self.cod_componente} - {self.nombre}>'
