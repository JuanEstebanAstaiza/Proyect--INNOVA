import logging

from flask import current_app, render_template
from flask_mail import Mail, Message

logger = logging.getLogger(__name__)

class EmailService:
    """Servicio para envío de correos electrónicos"""

    @staticmethod
    def get_mail_instance(smtp_config=None):
        """Obtener instancia de Flask-Mail configurada"""
        if smtp_config:
            # Usar configuración específica del municipio
            mail_config = smtp_config.get_smtp_config_dict()
            mail = Mail()

            # Configurar mail con la configuración específica
            app = current_app._get_current_object()
            for key, value in mail_config.items():
                app.config[key] = value

            mail.init_app(app)
            return mail
        else:
            # Usar configuración por defecto de la aplicación
            return current_app.extensions.get('mail')

    @staticmethod
    def send_user_credentials_email(user, temp_password, smtp_config=None):
        """Enviar email con credenciales de usuario"""
        try:
            mail = EmailService.get_mail_instance(smtp_config)

            if not mail:
                logger.error("No se pudo obtener instancia de mail")
                return False

            # Crear mensaje
            subject = "Credenciales de Acceso - Sistema de Gestión de Planes de Desarrollo"
            recipients = [user.email]

            # Renderizar template HTML
            html_body = render_template('emails/user_credentials.html',
                                      user=user,
                                      temp_password=temp_password,
                                      smtp_config=smtp_config)

            # Renderizar template texto plano
            text_body = render_template('emails/user_credentials.txt',
                                      user=user,
                                      temp_password=temp_password,
                                      smtp_config=smtp_config)

            msg = Message(subject=subject,
                         recipients=recipients,
                         html=html_body,
                         body=text_body)

            mail.send(msg)
            logger.info(f"Email de credenciales enviado exitosamente a {user.email}")
            return True

        except Exception as e:
            logger.error(f"Error enviando email de credenciales a {user.email}: {e!s}")
            return False

    @staticmethod
    def send_test_email(smtp_config, test_email):
        """Enviar email de prueba"""
        try:
            mail = EmailService.get_mail_instance(smtp_config)

            if not mail:
                logger.error("No se pudo obtener instancia de mail")
                return False

            subject = "Prueba de Configuración SMTP - Sistema de Gestión"
            recipients = [test_email]

            html_body = f"""
            <h2>Prueba de Configuración SMTP</h2>
            <p>Este es un email de prueba enviado desde el Sistema de Gestión de Planes de Desarrollo.</p>
            <p>Si estás viendo este mensaje, la configuración SMTP está funcionando correctamente.</p>
            <hr>
            <p><strong>Configuración utilizada:</strong></p>
            <ul>
                <li>Servidor: {smtp_config.smtp_server}</li>
                <li>Puerto: {smtp_config.smtp_port}</li>
                <li>Usuario: {smtp_config.smtp_username}</li>
                <li>Remitente: {smtp_config.sender_email}</li>
                <li>Nombre: {smtp_config.sender_name}</li>
            </ul>
            """

            text_body = f"""
            Prueba de Configuración SMTP

            Este es un email de prueba enviado desde el Sistema de Gestión de Planes de Desarrollo.

            Si estás viendo este mensaje, la configuración SMTP está funcionando correctamente.

            Configuración utilizada:
            - Servidor: {smtp_config.smtp_server}
            - Puerto: {smtp_config.smtp_port}
            - Usuario: {smtp_config.smtp_username}
            - Remitente: {smtp_config.sender_email}
            - Nombre: {smtp_config.sender_name}
            """

            msg = Message(subject=subject,
                         recipients=recipients,
                         html=html_body,
                         body=text_body)

            mail.send(msg)
            logger.info(f"Email de prueba enviado exitosamente a {test_email}")
            return True

        except Exception as e:
            logger.error(f"Error enviando email de prueba a {test_email}: {e!s}")
            return False

    @staticmethod
    def send_password_reset_email(user, reset_token, smtp_config=None):
        """Enviar email de restablecimiento de contraseña"""
        try:
            mail = EmailService.get_mail_instance(smtp_config)

            if not mail:
                logger.error("No se pudo obtener instancia de mail")
                return False

            subject = "Restablecimiento de Contraseña - Sistema de Gestión"
            recipients = [user.email]

            html_body = render_template('emails/password_reset.html',
                                      user=user,
                                      reset_token=reset_token)

            text_body = render_template('emails/password_reset.txt',
                                      user=user,
                                      reset_token=reset_token)

            msg = Message(subject=subject,
                         recipients=recipients,
                         html=html_body,
                         body=text_body)

            mail.send(msg)
            logger.info(f"Email de restablecimiento enviado a {user.email}")
            return True

        except Exception as e:
            logger.error(f"Error enviando email de restablecimiento a {user.email}: {e!s}")
            return False
