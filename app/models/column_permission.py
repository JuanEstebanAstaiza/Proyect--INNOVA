from app import db


class ColumnPermission(db.Model):
    __tablename__ = 'column_permissions'

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    column_name = db.Column(db.String(200), nullable=False)

    # Permisos
    can_view = db.Column(db.Boolean, default=True)
    can_edit = db.Column(db.Boolean, default=False)

    # Categorización de columnas para mejor organización
    category = db.Column(db.String(50), default='general')  # estructura, indicadores, ejecucion, cumplimiento, poblacion, observaciones

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Asignar categoría basada en el nombre de la columna
        self._assign_category()

    def _assign_category(self):
        """Asigna categoría automáticamente según el nombre de la columna.

        El orden importa: casi todas las columnas de ejecución, cumplimiento,
        población y observaciones contienen la palabra "trimestre", así que las
        reglas más específicas van primero. Además se comprueban las variantes
        con y sin tilde, porque los encabezados reales llevan acento.
        """
        column_lower = (self.column_name or '').lower()

        def contiene(*palabras):
            return any(palabra in column_lower for palabra in palabras)

        if contiene('observacion', 'observación'):
            self.category = 'observaciones'
        elif contiene('poblacion', 'población'):
            self.category = 'poblacion'
        elif contiene('cumplimiento', '%'):
            self.category = 'cumplimiento'
        elif contiene('ejecucion', 'ejecución', 'trimestre'):
            self.category = 'ejecucion'
        elif contiene('indicador', 'meta', 'linea base', 'tipo', 'unidad', 'sentido'):
            self.category = 'indicadores'
        elif contiene('cod', 'cód', 'linea', 'componente', 'programa', 'proyecto',
                      'bpim', 'responsable', 'resposable'):
            self.category = 'estructura'
        else:
            self.category = 'general'

    def to_dict(self):
        """Convierte el permiso a diccionario para JSON"""
        return {
            'id': self.id,
            'column_name': self.column_name,
            'can_view': self.can_view,
            'can_edit': self.can_edit,
            'category': self.category
        }

    def __repr__(self):
        return f'<ColumnPermission {self.role.name}:{self.column_name} - Edit:{self.can_edit}>'
