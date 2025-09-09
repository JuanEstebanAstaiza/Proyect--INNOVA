from app import db
from datetime import datetime

class UserRole(db.Model):
    __tablename__ = 'user_roles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)

    # Estado de la asignación
    is_active = db.Column(db.Boolean, default=True)

    # Información de asignación
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # Admin que asignó
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)  # Notas adicionales sobre la asignación

    # Relaciones
    user = db.relationship('User', foreign_keys=[user_id], overlaps="active_roles,user_roles")
    role = db.relationship('Role', backref=db.backref('user_assignments', lazy=True))
    assigner = db.relationship('User', foreign_keys=[assigned_by], backref=db.backref('assigned_roles', lazy=True))

    def __init__(self, **kwargs):
        super(UserRole, self).__init__(**kwargs)

    def to_dict(self):
        """Convierte la asignación a diccionario"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.get_full_name() if self.user else 'N/A',
            'role_id': self.role_id,
            'role_name': self.role.name if self.role else 'N/A',
            'role_color': self.role.color if self.role else '#007bff',
            'is_active': self.is_active,
            'assigned_by': self.assigner.get_full_name() if self.assigner else 'Sistema',
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'notes': self.notes
        }

    def get_permissions_summary(self):
        """Retorna resumen de permisos del rol"""
        if not self.role:
            return {}

        editable_columns = self.role.get_editable_columns()
        viewable_columns = self.role.get_viewable_columns()

        return {
            'editable_columns_count': len(editable_columns),
            'viewable_columns_count': len(viewable_columns),
            'editable_columns': editable_columns[:5],  # Primeras 5 para resumen
            'has_more_editable': len(editable_columns) > 5
        }

    def __repr__(self):
        return f'<UserRole {self.user.username}:{self.role.name}>'
