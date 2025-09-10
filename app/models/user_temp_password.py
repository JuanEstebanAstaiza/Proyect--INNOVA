from app import db
from datetime import datetime, timedelta

class UserTempPassword(db.Model):
    """Almacena contraseñas temporales generadas para usuarios"""
    __tablename__ = 'user_temp_passwords'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    temp_password = db.Column(db.String(200), nullable=False)  # Contraseña encriptada
    plain_password = db.Column(db.String(50), nullable=False)  # Contraseña en texto plano (solo para mostrar)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))  # Expira en 7 días
    is_used = db.Column(db.Boolean, default=False)

    # Relaciones
    user = db.relationship('User', backref=db.backref('temp_passwords', lazy=True))

    @classmethod
    def create_for_user(cls, user, temp_password):
        """Crear registro de contraseña temporal para un usuario"""
        # Marcar contraseñas anteriores como usadas
        cls.query.filter_by(user_id=user.id, is_used=False).update({'is_used': True})

        # Crear nueva contraseña temporal
        temp_record = cls(
            user_id=user.id,
            temp_password=user.password_hash,  # Guardar el hash
            plain_password=temp_password,      # Guardar en texto plano para mostrar
            expires_at=datetime.utcnow() + timedelta(days=7)
        )

        db.session.add(temp_record)
        return temp_record

    @classmethod
    def get_active_for_user(cls, user_id):
        """Obtener contraseña temporal activa para un usuario"""
        return cls.query.filter_by(
            user_id=user_id,
            is_used=False,
            expires_at=datetime.utcnow() + timedelta(days=1)  # Solo si expira en más de 1 día
        ).order_by(cls.created_at.desc()).first()

    def is_expired(self):
        """Verificar si la contraseña temporal ha expirado"""
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f'<UserTempPassword user_id={self.user_id} expires={self.expires_at}>'
