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
        super(ColumnPermission, self).__init__(**kwargs)
        # Asignar categoría basada en el nombre de la columna
        self._assign_category()

    def _assign_category(self):
        """Asigna categoría automáticamente basada en el nombre de la columna"""
        column_lower = self.column_name.lower()

        if any(keyword in column_lower for keyword in ['cód', 'linea', 'componente', 'programa', 'proyecto']):
            self.category = 'estructura'
        elif any(keyword in column_lower for keyword in ['indicador', 'meta', 'linea base', 'tipo', 'unidad']):
            self.category = 'indicadores'
        elif any(keyword in column_lower for keyword in ['ejecución', 'trimestre']):
            self.category = 'ejecucion'
        elif any(keyword in column_lower for keyword in ['cumplimiento', '%']):
            self.category = 'cumplimiento'
        elif 'poblacion' in column_lower:
            self.category = 'poblacion'
        elif 'observacion' in column_lower:
            self.category = 'observaciones'
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
