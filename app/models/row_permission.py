from app import db
from datetime import datetime

class RowPermission(db.Model):
    __tablename__ = 'row_permissions'

    id = db.Column(db.Integer, primary_key=True)

    # Usuario que tiene el permiso
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Plan al que pertenece el permiso (solo cuando hay plan activo)
    plan_id = db.Column(db.Integer, db.ForeignKey('planes_desarrollo.id'), nullable=False)

    # Entidad específica (opcional - para permisos más granulares)
    indicador_id = db.Column(db.Integer, db.ForeignKey('indicadores_producto.id'), nullable=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyectos.id'), nullable=True)
    programa_id = db.Column(db.Integer, db.ForeignKey('programas.id'), nullable=True)
    componente_id = db.Column(db.Integer, db.ForeignKey('componentes.id'), nullable=True)
    linea_estrategica_id = db.Column(db.Integer, db.ForeignKey('lineas_estrategicas.id'), nullable=True)

    # Permisos específicos
    can_view = db.Column(db.Boolean, default=True)
    can_edit = db.Column(db.Boolean, default=False)

    # Información adicional
    permission_scope = db.Column(db.String(50), nullable=False)  # 'indicador', 'proyecto', 'programa', 'componente', 'linea'
    description = db.Column(db.Text)  # Descripción del permiso específico

    # Estado y timestamps
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Usuario que asignó el permiso
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relaciones
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('row_permissions', lazy=True))
    plan = db.relationship('PlanDesarrollo', backref=db.backref('row_permissions', lazy=True))

    # Relaciones opcionales para diferentes niveles
    indicador = db.relationship('IndicadorProducto', backref=db.backref('row_permissions', lazy=True))
    proyecto = db.relationship('Proyecto', backref=db.backref('row_permissions', lazy=True))
    programa = db.relationship('Programa', backref=db.backref('row_permissions', lazy=True))
    componente = db.relationship('Componente', backref=db.backref('row_permissions', lazy=True))
    linea_estrategica = db.relationship('LineaEstrategica', backref=db.backref('row_permissions', lazy=True))

    assigner = db.relationship('User', foreign_keys=[assigned_by], backref=db.backref('assigned_row_permissions', lazy=True))

    def __init__(self, **kwargs):
        super(RowPermission, self).__init__(**kwargs)
        # Validar que se especifique al menos una entidad
        entities = [self.indicador_id, self.proyecto_id, self.programa_id, self.componente_id, self.linea_estrategica_id]
        if not any(entities):
            raise ValueError("Debe especificarse al menos una entidad (indicador, proyecto, programa, componente o línea estratégica)")

    @property
    def target_entity(self):
        """Retorna la entidad objetivo del permiso"""
        if self.indicador_id:
            return self.indicador
        elif self.proyecto_id:
            return self.proyecto
        elif self.programa_id:
            return self.programa
        elif self.componente_id:
            return self.componente
        elif self.linea_estrategica_id:
            return self.linea_estrategica
        return None

    @property
    def entity_name(self):
        """Retorna el nombre de la entidad objetivo"""
        entity = self.target_entity
        if entity:
            if hasattr(entity, 'nombre'):
                return entity.nombre
            elif hasattr(entity, 'titulo'):
                return entity.titulo
            else:
                return str(entity)
        return "Entidad no encontrada"

    @property
    def entity_type_display(self):
        """Retorna el tipo de entidad en español"""
        types = {
            'indicador': 'Indicador',
            'proyecto': 'Proyecto',
            'programa': 'Programa',
            'componente': 'Componente',
            'linea': 'Línea Estratégica'
        }
        return types.get(self.permission_scope, self.permission_scope.title())

    def can_access_entity(self, entity_id, entity_type):
        """
        Verifica si el usuario puede acceder a una entidad específica

        Args:
            entity_id: ID de la entidad
            entity_type: Tipo de entidad ('indicador', 'proyecto', 'programa', 'componente', 'linea')

        Returns:
            dict: {'can_view': bool, 'can_edit': bool}
        """
        if not self.is_active:
            return {'can_view': False, 'can_edit': False}

        # Verificar si el permiso aplica a esta entidad
        target_id = getattr(self, f'{entity_type}_id')
        if target_id != entity_id:
            return {'can_view': False, 'can_edit': False}

        return {
            'can_view': self.can_view,
            'can_edit': self.can_edit
        }

    def get_scope_hierarchy(self):
        """
        Retorna la jerarquía completa de entidades afectadas por este permiso
        Útil para mostrar el alcance del permiso
        """
        hierarchy = []

        if self.indicador_id and self.indicador:
            hierarchy.append(('Indicador', self.indicador.nombre, self.indicador.id))
            if self.indicador.proyecto:
                hierarchy.append(('Proyecto', self.indicador.proyecto.nombre, self.indicador.proyecto.id))
                if self.indicador.proyecto.programa:
                    hierarchy.append(('Programa', self.indicador.proyecto.programa.nombre, self.indicador.proyecto.programa.id))
                    if self.indicador.proyecto.programa.componente:
                        hierarchy.append(('Componente', self.indicador.proyecto.programa.componente.nombre, self.indicador.proyecto.programa.componente.id))
                        if self.indicador.proyecto.programa.componente.linea_estrategica:
                            hierarchy.append(('Línea Estratégica', self.indicador.proyecto.programa.componente.linea_estrategica.nombre, self.indicador.proyecto.programa.componente.linea_estrategica.id))

        elif self.proyecto_id and self.proyecto:
            hierarchy.append(('Proyecto', self.proyecto.nombre, self.proyecto.id))
            if self.proyecto.programa:
                hierarchy.append(('Programa', self.proyecto.programa.nombre, self.proyecto.programa.id))
                if self.proyecto.programa.componente:
                    hierarchy.append(('Componente', self.proyecto.programa.componente.nombre, self.proyecto.programa.componente.id))
                    if self.proyecto.programa.componente.linea_estrategica:
                        hierarchy.append(('Línea Estratégica', self.proyecto.programa.componente.linea_estrategica.nombre, self.proyecto.programa.componente.linea_estrategica.id))

        elif self.programa_id and self.programa:
            hierarchy.append(('Programa', self.programa.nombre, self.programa.id))
            if self.programa.componente:
                hierarchy.append(('Componente', self.programa.componente.nombre, self.programa.componente.id))
                if self.programa.componente.linea_estrategica:
                    hierarchy.append(('Línea Estratégica', self.programa.componente.linea_estrategica.nombre, self.programa.componente.linea_estrategica.id))

        elif self.componente_id and self.componente:
            hierarchy.append(('Componente', self.componente.nombre, self.componente.id))
            if self.componente.linea_estrategica:
                hierarchy.append(('Línea Estratégica', self.componente.linea_estrategica.nombre, self.componente.linea_estrategica.id))

        elif self.linea_estrategica_id and self.linea_estrategica:
            hierarchy.append(('Línea Estratégica', self.linea_estrategica.nombre, self.linea_estrategica.id))

        return hierarchy

    def to_dict(self):
        """Convierte el permiso a diccionario para API/JSON"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.get_full_name() if self.user else 'N/A',
            'plan_id': self.plan_id,
            'plan_title': self.plan.titulo if self.plan else 'N/A',
            'permission_scope': self.permission_scope,
            'entity_name': self.entity_name,
            'entity_type_display': self.entity_type_display,
            'can_view': self.can_view,
            'can_edit': self.can_edit,
            'description': self.description,
            'is_active': self.is_active,
            'assigned_by': self.assigner.get_full_name() if self.assigner else 'Sistema',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'scope_hierarchy': self.get_scope_hierarchy()
        }

    @staticmethod
    def get_user_permissions_for_plan(user_id, plan_id):
        """
        Obtiene todos los permisos de fila que tiene un usuario para un plan específico

        Args:
            user_id: ID del usuario
            plan_id: ID del plan

        Returns:
            list: Lista de permisos de fila activos
        """
        return RowPermission.query.filter_by(
            user_id=user_id,
            plan_id=plan_id,
            is_active=True
        ).all()

    @staticmethod
    def user_can_access_entity(user_id, plan_id, entity_id, entity_type, permission_type='view'):
        """
        Verifica si un usuario puede acceder a una entidad específica

        Args:
            user_id: ID del usuario
            plan_id: ID del plan
            entity_id: ID de la entidad
            entity_type: Tipo de entidad ('indicador', 'proyecto', 'programa', 'componente', 'linea')
            permission_type: Tipo de permiso ('view' o 'edit')

        Returns:
            bool: True si tiene permiso, False en caso contrario
        """
        permissions = RowPermission.get_user_permissions_for_plan(user_id, plan_id)

        for permission in permissions:
            access = permission.can_access_entity(entity_id, entity_type)
            if access[f'can_{permission_type}']:
                return True

        return False

    @staticmethod
    def get_users_with_permissions_for_entity(plan_id, entity_id, entity_type):
        """
        Obtiene todos los usuarios que tienen permisos sobre una entidad específica

        Args:
            plan_id: ID del plan
            entity_id: ID de la entidad
            entity_type: Tipo de entidad

        Returns:
            list: Lista de usuarios con permisos
        """
        permissions = RowPermission.query.filter_by(
            plan_id=plan_id,
            is_active=True
        ).all()

        users_with_permissions = []
        for permission in permissions:
            access = permission.can_access_entity(entity_id, entity_type)
            if access['can_view'] or access['can_edit']:
                if permission.user not in users_with_permissions:
                    users_with_permissions.append(permission.user)

        return users_with_permissions

    def __repr__(self):
        return f'<RowPermission {self.user.username}:{self.permission_scope} - {self.entity_name}>'