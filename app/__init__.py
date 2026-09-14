"""Fábrica de la aplicación Flask del Proyecto INNOVA.

Expone `create_app()`, que construye la aplicación, registra las extensiones
y los blueprints, y siembra los roles por defecto la primera vez que se
arranca contra una base de datos vacía.
"""

import logging
import os

from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

# Inicializar extensiones
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()

logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """Construye y configura una instancia de la aplicación.

    Args:
        config_name: 'development', 'production' o 'testing'. Si es None se
            toma de la variable de entorno FLASK_ENV.
    """
    # Cargar variables de entorno desde .env antes de leer la configuración.
    try:
        from dotenv import load_dotenv

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        load_dotenv(os.path.join(project_root, '.env'))
    except ImportError:  # python-dotenv es opcional en tiempo de ejecución
        logger.debug('python-dotenv no está instalado; se usan solo las variables del sistema')

    app = Flask(__name__)

    # Cargar configuración
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV') or 'development'

    from config import config

    app.config.from_object(config.get(config_name, config['default']))

    # Asegurar que existan los directorios de trabajo declarados en la configuración
    for folder_key in ('UPLOAD_FOLDER', 'AUDIT_FILES_PATH'):
        folder = app.config.get(folder_key)
        if folder:
            os.makedirs(folder, exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)

    # Inicializar extensiones con la app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    # Configurar login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicie sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User

        return db.session.get(User, int(user_id))

    # Registrar blueprints
    from app.views.admin import admin_bp
    from app.views.audit import audit_bp
    from app.views.auth import auth_bp
    from app.views.main import main_bp
    from app.views.planes import planes_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(planes_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(audit_bp)

    registrar_comandos(app)

    return app


def registrar_comandos(app):
    """Comandos de `flask` propios de la aplicación."""

    @app.cli.command('init-db')
    def init_db():
        """Crea las tablas que falten y siembra los roles por defecto.

        El esquema NO se toca al arrancar la aplicación: hay que pedirlo
        explícitamente con este comando o con `flask db upgrade`. Así una
        migración de Alembic no se encuentra las tablas ya creadas.
        """
        db.create_all()
        initialize_default_roles()
        print('Base de datos lista.')

    @app.cli.command('crear-roles')
    def crear_roles():
        """Siembra los roles por defecto si aún no existen."""
        initialize_default_roles()
        print('Roles verificados.')


def initialize_default_roles():
    """Crea los roles por defecto del sistema si la tabla de roles está vacía."""
    from app.models import Role

    if Role.query.count() > 0:
        logger.info('Los roles ya existen en el sistema; no se siembran de nuevo')
        return

    logger.info('Creando roles por defecto...')

    # Cada 'permissions' recibe un ColumnPermission y devuelve (can_edit, can_view).
    default_roles = [
        {
            'name': 'Administrador',
            'description': 'Acceso completo al sistema. Puede gestionar usuarios, roles y editar todos los planes.',
            'color': '#dc3545',
            'is_system_role': True,
            'permissions': lambda p: (True, True),
        },
        {
            'name': 'Editor General',
            'description': 'Puede editar planes de desarrollo pero no gestionar usuarios o roles.',
            'color': '#28a745',
            'is_system_role': True,
            'permissions': _get_editor_general_permissions,
        },
        {
            'name': 'Editor de Ejecución',
            'description': 'Puede editar datos de ejecución trimestral y porcentajes de cumplimiento.',
            'color': '#007bff',
            'is_system_role': False,
            'permissions': _get_execution_editor_permissions,
        },
        {
            'name': 'Editor de Metas',
            'description': 'Puede editar metas, indicadores y datos básicos del plan.',
            'color': '#ffc107',
            'is_system_role': False,
            'permissions': _get_meta_editor_permissions,
        },
        {
            'name': 'Visualizador',
            'description': 'Solo puede ver información del plan de desarrollo.',
            'color': '#6c757d',
            'is_system_role': True,
            'permissions': lambda p: (False, True),
        },
    ]

    try:
        created_roles = []

        for role_data in default_roles:
            role = Role(
                name=role_data['name'],
                description=role_data['description'],
                color=role_data['color'],
                is_system_role=role_data['is_system_role'],
            )

            # Role.__init__ ya adjuntó el juego de columnas por defecto; aquí
            # solo se ajusta el nivel de acceso de cada una.
            for permission in role.column_permissions:
                permission.can_edit, permission.can_view = role_data['permissions'](permission)

            db.session.add(role)
            created_roles.append(role)
            logger.info('Rol "%s" creado', role.name)

        db.session.commit()

        # Asignar roles a usuarios existentes basados en su rol legacy
        _assign_roles_to_existing_users(created_roles)

        logger.info('Roles por defecto inicializados correctamente')
        for role in created_roles:
            logger.info(
                '  %s: %d columnas editables, %d visibles',
                role.name,
                len(role.get_editable_columns()),
                len(role.get_viewable_columns()),
            )
    except Exception:
        logger.exception('Error al inicializar los roles por defecto')
        db.session.rollback()


def _get_editor_general_permissions(permission):
    """Define permisos para Editor General. Devuelve (can_edit, can_view)."""
    column_name = permission.column_name.lower()

    # Los editores pueden editar casi todo menos la estructura organizacional.
    # Ojo: la columna del Excel original dice 'DEPENDENCIA RESPOSABLE', sin la N.
    # Se comprueban las dos grafías para que la regla no dependa de la errata.
    es_responsable = 'responsable' in column_name or 'resposable' in column_name
    can_edit = not es_responsable and not column_name.strip().startswith('cód')

    # 'CÓD LINEA' sí es editable por este rol.
    if permission.column_name == 'CÓD LINEA':
        can_edit = True

    return can_edit, True


def _get_execution_editor_permissions(permission):
    """Define permisos para Editor de Ejecución. Devuelve (can_edit, can_view)."""
    column_name = permission.column_name.lower()

    can_edit = (
        'ejecución' in column_name
        or 'cumplimiento' in column_name
        or 'población' in column_name
        or 'observación' in column_name
    )

    return can_edit, True


def _get_meta_editor_permissions(permission):
    """Define permisos para Editor de Metas. Devuelve (can_edit, can_view)."""
    column_name = permission.column_name.lower()

    can_edit = (
        'meta' in column_name
        or 'indicador' in column_name
        or 'linea base' in column_name
        or 'tipo' in column_name
        or 'unidad' in column_name
        or 'sentido' in column_name
    )

    return can_edit, True


def assign_default_roles_to_users():
    """Asigna los roles por defecto a los usuarios que aun no tengan ninguno.

    Util despues de sembrar usuarios desde un script, cuando los roles ya
    existian y por tanto initialize_default_roles() no volvio a ejecutarse.
    """
    from app.models import Role

    _assign_roles_to_existing_users(Role.query.all())


def _assign_roles_to_existing_users(roles):
    """Asigna un rol por defecto a los usuarios que aún no tienen ninguno."""
    from app.models import User, UserRole

    logger.info('Asignando roles por defecto a usuarios existentes...')

    admin_role = next((r for r in roles if r.name == 'Administrador'), None)
    editor_role = next((r for r in roles if r.name == 'Editor General'), None)
    viewer_role = next((r for r in roles if r.name == 'Visualizador'), None)

    if not all([admin_role, editor_role, viewer_role]):
        logger.error('No se encontraron los roles por defecto; se omite la asignación')
        return

    # El usuario que consta como "asignador" debe existir para respetar la
    # clave foránea de UserRole.assigned_by.
    first_user = User.query.order_by(User.id).first()
    assigned_by = first_user.id if first_user else None

    assigned_count = 0

    for user in User.query.all():
        if UserRole.query.filter_by(user_id=user.id, is_active=True).count():
            continue

        if user.legacy_role == 'admin':
            role_to_assign = admin_role
        elif user.legacy_role == 'editor':
            role_to_assign = editor_role
        else:  # viewer u otros
            role_to_assign = viewer_role

        db.session.add(
            UserRole(
                user_id=user.id,
                role_id=role_to_assign.id,
                assigned_by=assigned_by,
                notes='Asignación automática desde sistema legacy',
            )
        )
        assigned_count += 1

    db.session.commit()
    logger.info('Asignados %d roles a usuarios existentes', assigned_count)
