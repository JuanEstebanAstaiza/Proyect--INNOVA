from app import db
from datetime import datetime

class Proyecto(db.Model):
    __tablename__ = 'proyectos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)  # NOMBRE PROYECTO
    descripcion = db.Column(db.Text)

    # Relación con programa
    programa_id = db.Column(db.Integer, db.ForeignKey('programas.id'), nullable=False)
    programa = db.relationship('Programa', backref=db.backref('proyectos', lazy=True, cascade='all, delete-orphan'))

    # Estado y timestamps
    estado = db.Column(db.String(20), default='planificado')  # planificado, en_ejecucion, completado, suspendido, cancelado
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Fechas del proyecto
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)

    # Metadatos
    presupuesto_total = db.Column(db.Float, default=0.0)
    presupuesto_ejecutado = db.Column(db.Float, default=0.0)

    # Ubicación y sector
    ubicacion = db.Column(db.String(200))
    sector = db.Column(db.String(100))

    # Responsables
    responsable_ejecucion = db.Column(db.String(200))
    responsable_seguimiento = db.Column(db.String(200))

    def __init__(self, **kwargs):
        super(Proyecto, self).__init__(**kwargs)
        if self.estado not in ['planificado', 'en_ejecucion', 'completado', 'suspendido', 'cancelado']:
            self.estado = 'planificado'

    def get_progreso(self):
        """Calcula el progreso del proyecto basado en sus indicadores"""
        indicadores = self.indicadores
        if not indicadores:
            return 0.0

        # Calcular progreso basado en indicadores de producto
        indicadores_producto = [i for i in indicadores if hasattr(i, 'meta_cuatrienio') and i.meta_cuatrienio > 0]
        if indicadores_producto:
            total_progreso = sum(indicador.get_progreso_porcentual() for indicador in indicadores_producto)
            return total_progreso / len(indicadores_producto)

        return 0.0

    def get_presupuesto_ejecutado(self):
        """Retorna el presupuesto ejecutado"""
        return self.presupuesto_ejecutado

    def get_presupuesto_restante(self):
        """Calcula el presupuesto restante"""
        return self.presupuesto_total - self.presupuesto_ejecutado

    def actualizar_presupuesto_ejecutado(self):
        """Actualiza el presupuesto ejecutado basado en la ejecución trimestral"""
        ejecuciones = self.ejecuciones_trimestrales
        total_ejecutado = sum(ejecucion.presupuesto_ejecutado for ejecucion in ejecuciones)
        self.presupuesto_ejecutado = total_ejecutado
        db.session.commit()

    def __repr__(self):
        return f'<Proyecto {self.nombre}>'
