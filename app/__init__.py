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

    # Crear tablas de la base de datos
    with app.app_context():
        db.create_all()

    return app
