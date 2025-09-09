from app import db
from datetime import datetime

class RowPermission(db.Model):
    __tablename__ = 'row_permissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    indicador_id = db.Column(db.Integer, db.ForeignKey('indicadores_producto.id'), nullable=False)

    # Permisos
    can_edit = db.Column(db.Boolean, default=True)

    # Información de búsqueda que permitió esta asignación
    search_term = db.Column(db.String(200))  # Término de búsqueda usado para asignar
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # Admin que asignó
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('row_permissions', lazy=True))
    indicador = db.relationship('IndicadorProducto', backref=db.backref('row_permissions', lazy=True))
    assigner = db.relationship('User', foreign_keys=[assigned_by], backref=db.backref('assigned_permissions', lazy=True))

    def __init__(self, **kwargs):
        super(RowPermission, self).__init__(**kwargs)

    def to_dict(self):
        """Convierte el permiso a diccionario"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.get_full_name() if self.user else 'N/A',
            'indicador_id': self.indicador_id,
            'indicador_name': self.indicador.nombre if self.indicador else 'N/A',
            'can_edit': self.can_edit,
            'search_term': self.search_term,
            'assigned_by': self.assigner.get_full_name() if self.assigner else 'Sistema',
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None
        }

    def __repr__(self):
        return f'<RowPermission {self.user.username}:{self.indicador.nombre}>'
