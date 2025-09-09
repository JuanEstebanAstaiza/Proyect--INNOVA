from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    # Información personal
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    position = db.Column(db.String(100))  # Cargo en la alcaldía

    # Información de la alcaldía
    municipality = db.Column(db.String(100), nullable=False)  # Nombre de la alcaldía
    department = db.Column(db.String(100), nullable=False)  # Departamento/Estado
    municipality_code = db.Column(db.String(20))  # Código único de la alcaldía

    # Estado y timestamps
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Sistema de roles avanzado (legacy para compatibilidad)
    legacy_role = db.Column(db.String(20), default='viewer')  # Mantener para compatibilidad

    # Relaciones con el nuevo sistema de roles
    active_roles = db.relationship('UserRole',
                                 foreign_keys='UserRole.user_id',
                                 lazy=True,
                                 primaryjoin="and_(User.id==UserRole.user_id, UserRole.is_active==True)")

    user_roles = db.relationship('UserRole',
                               foreign_keys='UserRole.user_id',
                               lazy=True,
                               overlaps="active_roles")

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.legacy_role not in ['admin', 'editor', 'viewer']:
            self.legacy_role = 'viewer'

    @property
    def password(self):
        raise AttributeError('La contraseña no es un atributo legible')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    # Propiedad para compatibilidad con el sistema legacy
    @property
    def role(self):
        return self.legacy_role

    @role.setter
    def role(self, value):
        self.legacy_role = value

    def is_admin(self):
        # Verificar si tiene rol admin en el sistema nuevo o legacy
        if self.active_roles:
            # Verificar tanto 'admin' como 'administrador'
            admin_names = ['admin', 'administrador']
            return any(ur.role.name.lower() in admin_names for ur in self.active_roles)
        return self.legacy_role == 'admin'

    def is_editor(self):
        # Verificar si tiene rol editor o admin en el sistema nuevo o legacy
        if self.active_roles:
            admin_roles = ['admin', 'editor', 'administrador', 'editor general', 'editor de ejecución', 'editor de metas']
            return any(ur.role.name.lower() in admin_roles for ur in self.active_roles)
        return self.legacy_role in ['admin', 'editor']

    def get_active_roles(self):
        """Retorna lista de roles activos del usuario"""
        return [ur.role for ur in self.active_roles if ur.is_active]

    def has_role(self, role_name):
        """Verifica si el usuario tiene un rol específico"""
        return any(ur.role.name.lower() == role_name.lower() for ur in self.active_roles)

    def can_edit_column(self, column_name):
        """Verifica si el usuario puede editar una columna específica"""
        if self.is_admin():
            return True  # Los admins pueden editar todo

        for user_role in self.active_roles:
            if user_role.role.can_edit_column(column_name):
                return True

        return False

    def can_view_column(self, column_name):
        """Verifica si el usuario puede ver una columna específica"""
        if self.is_admin():
            return True  # Los admins pueden ver todo

        for user_role in self.active_roles:
            if user_role.role.can_view_column(column_name):
                return True

        return False

    def can_edit_row(self, indicador_id, plan_id=None):
        """Verifica si el usuario puede editar una fila específica"""
        if self.is_admin():
            return True  # Los admins pueden editar todas las filas

        # Verificar permisos específicos de fila
        from app.models.row_permission import RowPermission

        # Si no se especifica plan_id, buscar en todos los planes activos del usuario
        if plan_id is None:
            from app.models.plan_desarrollo import PlanDesarrollo
            active_plan = PlanDesarrollo.query.filter_by(
                municipio=self,
                estado='activo'
            ).first()
            if active_plan:
                plan_id = active_plan.id
            else:
                return False

        permission = RowPermission.query.filter_by(
            user_id=self.id,
            plan_id=plan_id,
            indicador_id=indicador_id,
            is_active=True
        ).first()

        return permission and permission.can_edit

    def can_view_row(self, indicador_id, plan_id=None):
        """Verifica si el usuario puede ver una fila específica"""
        if self.is_admin():
            return True  # Los admins pueden ver todas las filas

        # Verificar permisos específicos de fila
        from app.models.row_permission import RowPermission

        # Si no se especifica plan_id, buscar en todos los planes activos del usuario
        if plan_id is None:
            from app.models.plan_desarrollo import PlanDesarrollo
            active_plan = PlanDesarrollo.query.filter_by(
                municipio=self,
                estado='activo'
            ).first()
            if active_plan:
                plan_id = active_plan.id
            else:
                return False

        permission = RowPermission.query.filter_by(
            user_id=self.id,
            plan_id=plan_id,
            indicador_id=indicador_id,
            is_active=True
        ).first()

        return permission and permission.can_view

    def can_edit_entity(self, entity_id, entity_type, plan_id=None):
        """Verifica si el usuario puede editar una entidad específica"""
        if self.is_admin():
            return True

        from app.models.row_permission import RowPermission

        # Si no se especifica plan_id, buscar en todos los planes activos del usuario
        if plan_id is None:
            from app.models.plan_desarrollo import PlanDesarrollo
            active_plan = PlanDesarrollo.query.filter_by(
                municipio=self,
                estado='activo'
            ).first()
            if active_plan:
                plan_id = active_plan.id
            else:
                return False

        # Mapear tipo de entidad a campo de ID
        entity_field_map = {
            'indicador': 'indicador_id',
            'proyecto': 'proyecto_id',
            'programa': 'programa_id',
            'componente': 'componente_id',
            'linea': 'linea_estrategica_id'
        }

        entity_field = entity_field_map.get(entity_type)
        if not entity_field:
            return False

        # Crear filtro dinámico
        filter_kwargs = {
            'user_id': self.id,
            'plan_id': plan_id,
            'is_active': True
        }
        filter_kwargs[entity_field] = entity_id

        permission = RowPermission.query.filter_by(**filter_kwargs).first()
        return permission and permission.can_edit

    def can_view_entity(self, entity_id, entity_type, plan_id=None):
        """Verifica si el usuario puede ver una entidad específica"""
        if self.is_admin():
            return True

        from app.models.row_permission import RowPermission

        # Si no se especifica plan_id, buscar en todos los planes activos del usuario
        if plan_id is None:
            from app.models.plan_desarrollo import PlanDesarrollo
            active_plan = PlanDesarrollo.query.filter_by(
                municipio=self,
                estado='activo'
            ).first()
            if active_plan:
                plan_id = active_plan.id
            else:
                return False

        # Mapear tipo de entidad a campo de ID
        entity_field_map = {
            'indicador': 'indicador_id',
            'proyecto': 'proyecto_id',
            'programa': 'programa_id',
            'componente': 'componente_id',
            'linea': 'linea_estrategica_id'
        }

        entity_field = entity_field_map.get(entity_type)
        if not entity_field:
            return False

        # Crear filtro dinámico
        filter_kwargs = {
            'user_id': self.id,
            'plan_id': plan_id,
            'is_active': True
        }
        filter_kwargs[entity_field] = entity_id

        permission = RowPermission.query.filter_by(**filter_kwargs).first()
        return permission and permission.can_view

    def get_editable_columns(self):
        """Retorna todas las columnas que el usuario puede editar"""
        if self.is_admin():
            # Los admins pueden editar todas las columnas estándar
            return [
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

        editable_columns = set()
        for user_role in self.active_roles:
            editable_columns.update(user_role.role.get_editable_columns())

        return list(editable_columns)

    def get_viewable_columns(self):
        """Retorna todas las columnas que el usuario puede ver"""
        if self.is_admin():
            # Los admins pueden ver todas las columnas
            return self.get_editable_columns()

        viewable_columns = set()
        for user_role in self.active_roles:
            viewable_columns.update(user_role.role.get_viewable_columns())

        return list(viewable_columns)

    def update_last_login(self):
        """Update the last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<User {self.username} - {self.municipality}>'
