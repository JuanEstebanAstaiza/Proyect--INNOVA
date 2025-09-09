from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
import os

# Inicializar extensiones
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_name=None):
    app = Flask(__name__)

    # Cargar configuración
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV') or 'development'

    from config import config
    app.config.from_object(config.get(config_name, config['default']))

    # Inicializar extensiones con la app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configurar login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicie sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Registrar blueprints
    from app.views.auth import auth_bp
    from app.views.main import main_bp
    from app.views.planes import planes_bp
    from app.views.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(planes_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Crear tablas de la base de datos e inicializar datos por defecto
    with app.app_context():
        db.create_all()

        # Inicializar roles por defecto si no existen
        initialize_default_roles()

    return app


def initialize_default_roles():
    """Inicializa los roles por defecto del sistema si no existen"""
    from app.models import Role, ColumnPermission, User, UserRole

    # Verificar si ya existen roles
    if Role.query.count() > 0:
        print("ℹ️  Roles ya existen en el sistema")
        return

    print("🛠️  Creando roles por defecto...")

    try:
        # Definir roles por defecto
        default_roles = [
            {
                'name': 'Administrador',
                'description': 'Acceso completo al sistema. Puede gestionar usuarios, roles y editar todos los planes.',
                'color': '#dc3545',
                'is_system_role': True,
                'permissions': lambda p: (True, True)  # can_edit, can_view
            },
            {
                'name': 'Editor General',
                'description': 'Puede editar planes de desarrollo pero no gestionar usuarios o roles.',
                'color': '#28a745',
                'is_system_role': True,
                'permissions': lambda p: _get_editor_general_permissions(p)
            },
            {
                'name': 'Editor de Ejecución',
                'description': 'Puede editar datos de ejecución trimestral y porcentajes de cumplimiento.',
                'color': '#007bff',
                'is_system_role': False,
                'permissions': lambda p: _get_execution_editor_permissions(p)
            },
            {
                'name': 'Editor de Metas',
                'description': 'Puede editar metas, indicadores y datos básicos del plan.',
                'color': '#ffc107',
                'is_system_role': False,
                'permissions': lambda p: _get_meta_editor_permissions(p)
            },
            {
                'name': 'Visualizador',
                'description': 'Solo puede ver información del plan de desarrollo.',
                'color': '#6c757d',
                'is_system_role': True,
                'permissions': lambda p: (False, True)  # can_edit, can_view
            }
        ]

        created_roles = []

        for role_data in default_roles:
            # Crear rol
            role = Role(
                name=role_data['name'],
                description=role_data['description'],
                color=role_data['color'],
                is_system_role=role_data['is_system_role']
            )
            db.session.add(role)
            db.session.commit()  # Commit para obtener el ID

            # Configurar permisos
            for permission in role.column_permissions:
                can_edit, can_view = role_data['permissions'](permission)
                permission.can_edit = can_edit
                permission.can_view = can_view

            db.session.commit()
            created_roles.append(role)
            print(f"  ✅ Rol '{role.name}' creado")

        # Asignar roles a usuarios existentes basados en su rol legacy
        _assign_roles_to_existing_users(created_roles)

        print("✅ Roles por defecto inicializados correctamente!")
        print("\n📊 Resumen de roles creados:")
        for role in created_roles:
            editable_count = len(role.get_editable_columns())
            viewable_count = len(role.get_viewable_columns())
            print(f"  • {role.name}: {editable_count} columnas editables, {viewable_count} visibles")

    except Exception as e:
        print(f"❌ Error al inicializar roles: {str(e)}")
        db.session.rollback()


def _get_editor_general_permissions(permission):
    """Define permisos para Editor General"""
    column_name = permission.column_name.lower()

    # Los editores pueden editar casi todo menos estructura organizacional
    can_edit = ('responsable' not in column_name and
                not (column_name == 'cód' and 'linea' not in column_name))

    # Permitir editar específicamente 'CÓD LINEA'
    if permission.column_name == 'CÓD LINEA':
        can_edit = True

    return can_edit, True  # can_edit, can_view


def _get_execution_editor_permissions(permission):
    """Define permisos para Editor de Ejecución"""
    column_name = permission.column_name.lower()

    can_edit = ('ejecución' in column_name or 'cumplimiento' in column_name or
                'población' in column_name or 'observación' in column_name)

    return can_edit, True  # can_edit, can_view


def _get_meta_editor_permissions(permission):
    """Define permisos para Editor de Metas"""
    column_name = permission.column_name.lower()

    can_edit = ('meta' in column_name or 'indicador' in column_name or
                'linea base' in column_name or 'tipo' in column_name or
                'unidad' in column_name or 'sentido' in column_name)

    return can_edit, True  # can_edit, can_view


def _assign_roles_to_existing_users(roles):
    """Asigna roles por defecto a usuarios existentes basados en su rol legacy"""
    print("🔄 Asignando roles por defecto a usuarios existentes...")

    users = User.query.all()
    admin_role = next((r for r in roles if r.name == 'Administrador'), None)
    editor_role = next((r for r in roles if r.name == 'Editor General'), None)
    viewer_role = next((r for r in roles if r.name == 'Visualizador'), None)

    if not all([admin_role, editor_role, viewer_role]):
        print("❌ Error: No se encontraron los roles por defecto")
        return

    assigned_count = 0

    for user in users:
        # Verificar si ya tiene roles asignados
        existing_roles = UserRole.query.filter_by(user_id=user.id, is_active=True).all()
        if existing_roles:
            continue

        # Asignar rol basado en el rol legacy
        if user.legacy_role == 'admin':
            role_to_assign = admin_role
        elif user.legacy_role == 'editor':
            role_to_assign = editor_role
        else:  # viewer u otros
            role_to_assign = viewer_role

        new_role_assignment = UserRole(
            user_id=user.id,
            role_id=role_to_assign.id,
            assigned_by=1,  # Asumir que el usuario 1 es el super admin
            notes='Asignación automática desde sistema legacy'
        )

        db.session.add(new_role_assignment)
        assigned_count += 1

    db.session.commit()
    print(f"✅ Asignados {assigned_count} roles a usuarios existentes")
