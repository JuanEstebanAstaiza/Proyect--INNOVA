import json
from datetime import timedelta

from app import db
from app.utils.fechas import ahora_utc
from app.utils.jwt_utils import JWTUtils


class ActiveSession(db.Model):
    __tablename__ = 'active_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    jwt_token = db.Column(db.Text, unique=True, nullable=False)  # JWT token único para la sesión
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    login_time = db.Column(db.DateTime, default=ahora_utc)
    last_activity = db.Column(db.DateTime, default=ahora_utc)
    is_active = db.Column(db.Boolean, default=True)
    device_info = db.Column(db.Text)  # JSON with device/browser info
    device_fingerprint = db.Column(db.String(100))  # Fingerprint único del dispositivo

    # Relationships
    user = db.relationship('User', backref=db.backref('active_sessions', lazy='dynamic'))

    def __init__(self, user_id, session_id, jwt_token, ip_address=None, user_agent=None, device_info=None):
        self.user_id = user_id
        self.session_id = session_id
        self.jwt_token = jwt_token
        self.ip_address = ip_address
        self.user_agent = user_agent

        # Handle device_info - convert dict to JSON string if needed
        if device_info is not None:
            if isinstance(device_info, dict):
                self.device_info = json.dumps(device_info)
                # Generar fingerprint del dispositivo
                self.device_fingerprint = JWTUtils.generate_device_fingerprint(device_info)
            else:
                self.device_info = device_info
                self.device_fingerprint = None
        else:
            self.device_info = None
            self.device_fingerprint = None

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = ahora_utc()
        db.session.commit()

    def validate_jwt(self):
        """Validate the JWT token for this session"""
        return JWTUtils.validate_session_token(self.jwt_token) is not None

    def is_jwt_expired(self):
        """Check if the JWT token has expired"""
        return JWTUtils.is_token_expired(self.jwt_token)

    def get_jwt_info(self):
        """Get detailed information about the JWT token"""
        return JWTUtils.get_token_info(self.jwt_token)

    def get_device_info_dict(self):
        """Get device info as dictionary"""
        if self.device_info:
            try:
                return json.loads(self.device_info)
            except (ValueError, TypeError):
                return {}
        return {}

    def is_inactive(self, timeout_minutes=20):
        """Check if session is inactive based on timeout"""
        timeout = timedelta(minutes=timeout_minutes)
        return ahora_utc() - self.last_activity > timeout

    def get_inactive_duration(self):
        """Get duration of inactivity in minutes"""
        delta = ahora_utc() - self.last_activity
        return delta.total_seconds() / 60

    def get_active_duration(self):
        """Get total active duration of session in minutes"""
        delta = ahora_utc() - self.login_time
        return delta.total_seconds() / 60

    def to_dict(self):
        jwt_info = self.get_jwt_info()
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'Unknown',
            'session_id': self.session_id,
            'jwt_token': self.jwt_token[:50] + '...' if self.jwt_token else None,  # Truncated for security
            'ip_address': self.ip_address,
            'login_time': self.login_time.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'is_active': self.is_active,
            'inactive_duration': self.get_inactive_duration(),
            'active_duration': self.get_active_duration(),
            'is_inactive': self.is_inactive(),
            'jwt_valid': jwt_info.get('valid', False),
            'jwt_expired': jwt_info.get('expired', True),
            'device_fingerprint': self.device_fingerprint,
            'device_info': self.get_device_info_dict()
        }

    @staticmethod
    def create_session_with_jwt(user_id, session_id, ip_address=None, user_agent=None, device_info=None):
        """
        Create a new session with JWT token and invalidate previous sessions for the same user

        Args:
            user_id: ID del usuario
            session_id: ID único de la sesión
            ip_address: Dirección IP del usuario
            user_agent: User agent del navegador
            device_info: Información del dispositivo

        Returns:
            ActiveSession: Nueva sesión creada
        """
        from flask import current_app

        # Generar JWT token para la sesión
        jwt_token = JWTUtils.generate_session_token(user_id, session_id, device_info)

        # Invalidar todas las sesiones anteriores del mismo usuario
        ActiveSession.invalidate_user_sessions(user_id, exclude_session_id=session_id)

        # Crear nueva sesión
        new_session = ActiveSession(
            user_id=user_id,
            session_id=session_id,
            jwt_token=jwt_token,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info
        )

        db.session.add(new_session)
        db.session.commit()

        current_app.logger.info(f"Nueva sesión JWT creada para usuario {user_id}: {session_id}")
        return new_session

    @staticmethod
    def invalidate_user_sessions(user_id, exclude_session_id=None):
        """
        Invalidar todas las sesiones activas de un usuario (excepto una específica)

        Args:
            user_id: ID del usuario
            exclude_session_id: ID de sesión a excluir (opcional)

        Returns:
            int: Número de sesiones invalidadas
        """
        from flask import current_app

        query = ActiveSession.query.filter_by(user_id=user_id, is_active=True)

        if exclude_session_id:
            query = query.filter(ActiveSession.session_id != exclude_session_id)

        invalidated_count = query.update({'is_active': False})
        db.session.commit()

        if invalidated_count > 0:
            current_app.logger.info(f"Invalidado {invalidated_count} sesiones anteriores para usuario {user_id}")

        return invalidated_count

    @staticmethod
    def validate_session_jwt(session_id, jwt_token):
        """
        Validar que una sesión tenga un JWT válido

        Args:
            session_id: ID de la sesión
            jwt_token: Token JWT a validar

        Returns:
            tuple: (is_valid, session) - True/False y objeto de sesión si existe
        """
        session = ActiveSession.query.filter_by(
            session_id=session_id,
            jwt_token=jwt_token,
            is_active=True
        ).first()

        if not session:
            return False, None

        # Validar el JWT
        if not session.validate_jwt():
            # JWT inválido o expirado - marcar sesión como inactiva
            session.is_active = False
            db.session.commit()
            return False, session

        return True, session

    @staticmethod
    def get_user_active_sessions(user_id):
        """
        Obtener todas las sesiones activas de un usuario con validación JWT

        Args:
            user_id: ID del usuario

        Returns:
            list: Lista de sesiones activas válidas
        """
        sessions = ActiveSession.query.filter_by(
            user_id=user_id,
            is_active=True
        ).all()

        # Filtrar solo sesiones con JWT válido
        valid_sessions = []
        for session in sessions:
            if session.validate_jwt() and not session.is_jwt_expired():
                valid_sessions.append(session)
            else:
                # Marcar sesiones inválidas como inactivas
                session.is_active = False

        if len(valid_sessions) != len(sessions):
            db.session.commit()

        return valid_sessions

    @staticmethod
    def get_active_sessions():
        """Get all currently active sessions with JWT validation"""
        sessions = ActiveSession.query.filter_by(is_active=True).all()

        # Filtrar solo sesiones con JWT válido
        valid_sessions = []
        for session in sessions:
            if session.validate_jwt() and not session.is_jwt_expired():
                valid_sessions.append(session)
            else:
                # Marcar sesiones inválidas como inactivas
                session.is_active = False

        if len(valid_sessions) != len(sessions):
            db.session.commit()

        return valid_sessions

    @staticmethod
    def get_inactive_sessions(timeout_minutes=20):
        """Get sessions that have been inactive for more than timeout_minutes"""
        timeout_time = ahora_utc() - timedelta(minutes=timeout_minutes)
        return ActiveSession.query.filter(
            ActiveSession.is_active.is_(True),
            ActiveSession.last_activity < timeout_time
        ).all()

    @staticmethod
    def cleanup_expired_jwt_sessions():
        """
        Marcar como inactivas las sesiones con JWT expirado

        Returns:
            int: Número de sesiones limpiadas
        """
        from flask import current_app

        sessions = ActiveSession.query.filter_by(is_active=True).all()
        cleaned_count = 0

        for session in sessions:
            if session.is_jwt_expired():
                session.is_active = False
                cleaned_count += 1

        if cleaned_count > 0:
            db.session.commit()
            current_app.logger.info(f"Limpiado {cleaned_count} sesiones con JWT expirado")

        return cleaned_count

    @staticmethod
    def cleanup_inactive_sessions(timeout_minutes=60):
        """Mark sessions as inactive if they've been inactive for too long"""
        timeout_time = ahora_utc() - timedelta(minutes=timeout_minutes)
        inactive_sessions = ActiveSession.query.filter(
            ActiveSession.is_active.is_(True),
            ActiveSession.last_activity < timeout_time
        ).update({'is_active': False})
        db.session.commit()
        return inactive_sessions

    @staticmethod
    def force_logout_user(user_id):
        """
        Forzar cierre de sesión de todas las sesiones activas de un usuario

        Args:
            user_id: ID del usuario

        Returns:
            int: Número de sesiones cerradas
        """
        from flask import current_app

        closed_count = ActiveSession.invalidate_user_sessions(user_id)
        current_app.logger.info(f"Fuerza logout de usuario {user_id}: {closed_count} sesiones cerradas")
        return closed_count

    def __repr__(self):
        return f'<ActiveSession {self.user.username} - {self.session_id[:8]}...>'
