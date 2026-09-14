import os
from datetime import timedelta


class Config:
    """Configuración base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    # Configuración de sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Configuración de archivos
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

    # Configuración de archivos de auditoría
    AUDIT_FILES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audit_files')

    # Configuración de email por defecto
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None or True
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL') is not None or False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'Sistema de Gestión <noreply@alcaldia.gob>'

    # Extensiones permitidas para archivos
    ALLOWED_EXTENSIONS = frozenset({
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
        'txt', 'rtf', 'jpg', 'jpeg', 'png', 'gif', 'bmp',
        'zip', 'rar', '7z', 'mp4', 'avi', 'mov', 'wmv',
    })

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///alcaldias_dev.db'

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///alcaldias.db'

    # Seguridad de las cookies.
    #
    # `Secure` hace que el navegador solo envíe la cookie por HTTPS, que es lo
    # correcto en producción. Pero si el sistema se sirve por HTTP plano (una
    # demostración, una red interna sin TLS) la cookie nunca vuelve y NADIE
    # puede iniciar sesión. Por eso es configurable:
    #     SESSION_COOKIE_SECURE=false  -> permite HTTP (solo para pruebas)
    _cookies_seguras = os.environ.get('SESSION_COOKIE_SECURE', 'true').lower() not in ('false', '0', 'no')

    SESSION_COOKIE_SECURE = _cookies_seguras
    REMEMBER_COOKIE_SECURE = _cookies_seguras
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True

    # Configuración de logs
    LOG_LEVEL = 'INFO'

class TestingConfig(Config):
    """Configuración para pruebas"""
    TESTING = True
    # Permite que la suite apunte a una base temporal en disco; una base en
    # memoria no sobrevive a los distintos hilos del cliente de pruebas.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
