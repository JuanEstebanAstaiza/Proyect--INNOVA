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

    # Roles y permisos
    role = db.Column(db.String(20), default='user')  # admin, editor, viewer

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role not in ['admin', 'editor', 'viewer']:
            self.role = 'viewer'

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

    def is_admin(self):
        return self.role == 'admin'

    def is_editor(self):
        return self.role in ['admin', 'editor']

    def __repr__(self):
        return f'<User {self.username} - {self.municipality}>'
