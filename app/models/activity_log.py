
from flask_login import current_user

from app import db
from app.utils.fechas import ahora_utc


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # login, logout, create_plan, etc.
    description = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45))  # IPv4/IPv6
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=ahora_utc, index=True)
    session_id = db.Column(db.String(100))
    extra_data = db.Column(db.Text)  # JSON data for additional info

    # Relationships
    user = db.relationship('User', backref=db.backref('activities', lazy='dynamic'))

    def __init__(self, user_id, action, description, ip_address=None, user_agent=None, session_id=None, extra_data=None):
        self.user_id = user_id
        self.action = action
        self.description = description
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.session_id = session_id
        self.extra_data = extra_data

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'Unknown',
            'action': self.action,
            'description': self.description,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat(),
            'session_id': self.session_id
        }

    @staticmethod
    def log_activity(action, description, ip_address=None, user_agent=None, session_id=None, extra_data=None):
        """Helper method to log activity for current user"""
        if current_user and current_user.is_authenticated:
            activity = ActivityLog(
                user_id=current_user.id,
                action=action,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                extra_data=extra_data
            )
            db.session.add(activity)
            db.session.commit()
            return activity
        return None

    def __repr__(self):
        return f'<ActivityLog {self.user.username}:{self.action} at {self.timestamp}>'
