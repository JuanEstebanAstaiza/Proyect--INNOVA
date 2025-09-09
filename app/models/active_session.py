from app import db
from datetime import datetime, timedelta
import json

class ActiveSession(db.Model):
    __tablename__ = 'active_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    device_info = db.Column(db.Text)  # JSON with device/browser info

    # Relationships
    user = db.relationship('User', backref=db.backref('active_sessions', lazy='dynamic'))

    def __init__(self, user_id, session_id, ip_address=None, user_agent=None, device_info=None):
        self.user_id = user_id
        self.session_id = session_id
        self.ip_address = ip_address
        self.user_agent = user_agent

        # Handle device_info - convert dict to JSON string if needed
        if device_info is not None:
            if isinstance(device_info, dict):
                self.device_info = json.dumps(device_info)
            else:
                self.device_info = device_info
        else:
            self.device_info = None

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
        db.session.commit()


    def is_inactive(self, timeout_minutes=20):
        """Check if session is inactive based on timeout"""
        timeout = timedelta(minutes=timeout_minutes)
        return datetime.utcnow() - self.last_activity > timeout

    def get_inactive_duration(self):
        """Get duration of inactivity in minutes"""
        delta = datetime.utcnow() - self.last_activity
        return delta.total_seconds() / 60

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'Unknown',
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'login_time': self.login_time.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'is_active': self.is_active,
            'inactive_duration': self.get_inactive_duration(),
            'is_inactive': self.is_inactive()
        }

    @staticmethod
    def get_active_sessions():
        """Get all currently active sessions"""
        return ActiveSession.query.filter_by(is_active=True).all()

    @staticmethod
    def get_inactive_sessions(timeout_minutes=20):
        """Get sessions that have been inactive for more than timeout_minutes"""
        timeout_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        return ActiveSession.query.filter(
            ActiveSession.is_active == True,
            ActiveSession.last_activity < timeout_time
        ).all()

    @staticmethod
    def cleanup_inactive_sessions(timeout_minutes=60):
        """Mark sessions as inactive if they've been inactive for too long"""
        timeout_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        inactive_sessions = ActiveSession.query.filter(
            ActiveSession.is_active == True,
            ActiveSession.last_activity < timeout_time
        ).update({'is_active': False})
        db.session.commit()
        return inactive_sessions

    def __repr__(self):
        return f'<ActiveSession {self.user.username} - {self.session_id[:8]}...>'
