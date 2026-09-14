
from app import db
from app.utils.fechas import ahora_utc


class SMTPConfig(db.Model):
    """Configuración SMTP para envío de correos por municipio"""
    __tablename__ = 'smtp_configs'

    id = db.Column(db.Integer, primary_key=True)
    municipality = db.Column(db.String(100), nullable=False, unique=True, index=True)  # Municipio asociado

    # Configuración SMTP
    smtp_server = db.Column(db.String(100), nullable=False)
    smtp_port = db.Column(db.Integer, nullable=False, default=587)
    smtp_username = db.Column(db.String(100), nullable=False)
    smtp_password = db.Column(db.String(200), nullable=False)  # Encriptado en producción
    use_tls = db.Column(db.Boolean, default=True)
    use_ssl = db.Column(db.Boolean, default=False)

    # Configuración del remitente
    sender_email = db.Column(db.String(120), nullable=False)
    sender_name = db.Column(db.String(100), nullable=False)

    # Configuración adicional
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=ahora_utc)
    updated_at = db.Column(db.DateTime, default=ahora_utc, onupdate=ahora_utc)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.sender_name:
            self.sender_name = f"Alcaldía de {self.municipality}"

    @classmethod
    def get_by_municipality(cls, municipality):
        """Obtener configuración SMTP por municipio"""
        return cls.query.filter_by(municipality=municipality, is_active=True).first()

    @classmethod
    def get_or_create(cls, municipality):
        """Obtener configuración SMTP o crear una por defecto"""
        config = cls.get_by_municipality(municipality)
        if not config:
            config = cls(
                municipality=municipality,
                smtp_server='smtp.gmail.com',
                smtp_port=587,
                smtp_username='',
                smtp_password='',
                sender_email='',
                sender_name=f'Alcaldía de {municipality}'
            )
            db.session.add(config)
            db.session.commit()
        return config

    def get_smtp_config_dict(self):
        """Retornar configuración SMTP como diccionario para Flask-Mail"""
        return {
            'MAIL_SERVER': self.smtp_server,
            'MAIL_PORT': self.smtp_port,
            'MAIL_USERNAME': self.smtp_username,
            'MAIL_PASSWORD': self.smtp_password,
            'MAIL_USE_TLS': self.use_tls,
            'MAIL_USE_SSL': self.use_ssl,
            'MAIL_DEFAULT_SENDER': (self.sender_name, self.sender_email)
        }

    def __repr__(self):
        return f'<SMTPConfig {self.municipality} - {self.sender_email}>'
