
from app import db
from app.utils.fechas import ahora_utc


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
    created_at = db.Column(db.DateTime, default=ahora_utc)
    updated_at = db.Column(db.DateTime, default=ahora_utc, onupdate=ahora_utc)

    # Metadatos
    presupuesto_total = db.Column(db.Float, default=0.0)
    prioridad = db.Column(db.String(20), default='media')  # baja, media, alta, critica

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.estado not in ['borrador', 'activo', 'finalizado', 'cancelado']:
            self.estado = 'borrador'
        if self.prioridad not in ['baja', 'media', 'alta', 'critica']:
            self.prioridad = 'media'

    def get_duracion(self):
        """Retorna la duración del plan en años"""
        return self.anio_fin - self.anio_inicio + 1

    def get_progreso_general(self):
        """Calcula el progreso general del plan a partir de sus líneas estratégicas.

        Antes se apoyaba en `self.objetivos`, una relación del diseño anterior
        cuyo modelo ya no se registra, de modo que el método siempre lanzaba
        AttributeError.
        """
        try:
            lineas = self.lineas_estrategicas
            if not lineas:
                return 0.0

            progresos = [p for p in (linea.get_progreso_general() for linea in lineas)
                         if p is not None and p >= 0]
            if not progresos:
                return 0.0
            return sum(progresos) / len(progresos)
        except (TypeError, ZeroDivisionError, AttributeError):
            return 0.0

    # ------------------------------------------------------------------
    # Visibilidad
    #
    # `municipio_id` apunta al usuario que creó el plan, pero el plan es de la
    # entidad territorial, no de esa persona: todos los funcionarios del mismo
    # municipio deben verlo, y ninguno de otro municipio.
    # ------------------------------------------------------------------

    @classmethod
    def filtro_visibilidad(cls, usuario):
        """Condición SQL que limita los planes al municipio del usuario.

        Se compara municipio y departamento porque en Colombia hay nombres de
        municipio repetidos en departamentos distintos.
        """
        from app.models.user import User

        return cls.municipio.has(
            db.and_(
                User.municipality == usuario.municipality,
                User.department == usuario.department,
            )
        )

    @classmethod
    def visibles_para(cls, usuario):
        """Consulta con los planes que el usuario tiene derecho a ver."""
        return cls.query.filter(cls.filtro_visibilidad(usuario))

    def es_visible_para(self, usuario):
        """Indica si este plan pertenece al municipio del usuario."""
        duenio = self.municipio
        if duenio is None:
            return False
        return (duenio.municipality == usuario.municipality
                and duenio.department == usuario.department)

    def activar(self):
        """Activa este plan y desactiva los demás del mismo municipio"""
        PlanDesarrollo.query.filter(
            PlanDesarrollo.filtro_visibilidad(self.municipio),
            PlanDesarrollo.estado == 'activo',
        ).update({'estado': 'borrador'}, synchronize_session=False)

        # Luego activar este plan
        self.estado = 'activo'
        db.session.commit()

    def desactivar(self):
        """Desactiva este plan"""
        self.estado = 'borrador'
        db.session.commit()

    @classmethod
    def get_plan_activo(cls, usuario):
        """Obtiene el plan activo del municipio del usuario, o None."""
        return cls.visibles_para(usuario).filter(cls.estado == 'activo').first()

    @classmethod
    def get_plan_activo_o_primero(cls, usuario):
        """Obtiene el plan activo del municipio; si no hay, el más reciente."""
        plan_activo = cls.get_plan_activo(usuario)
        if plan_activo:
            return plan_activo

        # Si no hay plan activo, devolver el más reciente
        return cls.visibles_para(usuario).order_by(cls.created_at.desc()).first()

    def __repr__(self):
        return f'<PlanDesarrollo {self.titulo} - {self.municipio.municipality}>'
