from app import db
from datetime import datetime

class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#007bff')  # Hex color for UI

    # Estado
    is_active = db.Column(db.Boolean, default=True)
    is_system_role = db.Column(db.Boolean, default=False)  # System roles cannot be deleted

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    column_permissions = db.relationship('ColumnPermission',
                                       backref=db.backref('role', lazy=True),
                                       cascade='all, delete-orphan',
                                       lazy=True)

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        # Crear permisos por defecto para nuevas columnas cuando se crea el rol
        if not self.is_system_role:
            self._create_default_column_permissions()

    def _create_default_column_permissions(self):
        """Crea permisos por defecto para las columnas estándar"""
        default_columns = [
            'CÓD LINEA', 'LINEAS ESTRATEGICAS', 'CÓD COMPONENTE', 'COMPONENTES',
            'CÓD PROGRAMA', 'PROGRAMA PDM', 'DEPENDENCIA RESPOSABLE', 'BPIM',
            'NOMBRE PROYECTO', 'INDICADORES ', 'CÓD INDICADOR DE PRODUCTO',
            'INDICADOR DE PRODUCTO', 'TIPO DE INDICADOR', 'LINEA BASE', 'SENTIDO',
            'TIPOLOGÍA', 'UNIDAD', 'META CUATRIENIO (2024-2027)', 'META 2024',
            'EJECUCIÓN I TRIMESTRE ', 'EJECUCIÓN II TRIMESTRE ',
            'EJECUCIÓN III TRIMESTRE ', 'EJECUCIÓN IV TRIMESTRE ',
            'EJECUCIÓN ACUMULADA', '% CUMPLIMIENTO I TRIMESTRE',
            '% CUMPLIMIENTO II TRIMESTRE', '% CUMPLIMIENTO III TRIMESTRE',
            '% CUMPLIMIENTO IV TRIMESTRE', '% CUMPLIMIENTO ACUMULADO',
            'POBLACIÓN IMPACTADA POR SECTOR I TRIMESTRE',
            'POBLACIÓN IMPACTADA POR SECTOR II TRIMESTRE',
            'POBLACIÓN IMPACTADA POR SECTOR III TRIMESTRE',
            'POBLACIÓN IMPACTADA POR SECTOR IV TRIMESTRE',
            'OBSERVACIÓN AL CUMPLIMIENTO ITRIMESTRE',
            'OBSERVACIÓN AL CUMPLIMIENTO II TRIMESTRE',
            'OBSERVACIÓN AL CUMPLIMIENTO III TRIMESTRE',
            'OBSERVACIÓN AL CUMPLIMIENTO IV TRIMESTRE'
        ]

        for column_name in default_columns:
            permission = ColumnPermission(
                column_name=column_name,
                can_view=True,
                can_edit=False  # Por defecto solo lectura
            )
            self.column_permissions.append(permission)

    def get_column_permission(self, column_name):
        """Obtiene el permiso para una columna específica"""
        return next((p for p in self.column_permissions if p.column_name == column_name), None)

    def can_edit_column(self, column_name):
        """Verifica si el rol puede editar una columna específica"""
        permission = self.get_column_permission(column_name)
        return permission and permission.can_edit

    def can_view_column(self, column_name):
        """Verifica si el rol puede ver una columna específica"""
        permission = self.get_column_permission(column_name)
        return permission and permission.can_view

    def get_editable_columns(self):
        """Retorna lista de columnas que el rol puede editar"""
        return [p.column_name for p in self.column_permissions if p.can_edit]

    def get_viewable_columns(self):
        """Retorna lista de columnas que el rol puede ver"""
        return [p.column_name for p in self.column_permissions if p.can_view]

    def __repr__(self):
        return f'<Role {self.name}>'
