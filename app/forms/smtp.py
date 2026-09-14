from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange


class SMTPConfigForm(FlaskForm):
    """Formulario para configuración SMTP"""

    # Municipio
    municipality = SelectField('Municipio', validators=[DataRequired()],
                             choices=[],  # Se llenará dinámicamente
                             render_kw={"class": "form-control"})

    # Configuración SMTP
    smtp_server = StringField('Servidor SMTP',
                             validators=[DataRequired(), Length(min=1, max=100)],
                             render_kw={"class": "form-control", "placeholder": "smtp.gmail.com"})

    smtp_port = IntegerField('Puerto SMTP',
                           validators=[DataRequired(), NumberRange(min=1, max=65535)],
                           default=587,
                           render_kw={"class": "form-control"})

    smtp_username = StringField('Usuario SMTP',
                              validators=[DataRequired(), Length(min=1, max=100)],
                              render_kw={"class": "form-control", "placeholder": "usuario@dominio.com"})

    smtp_password = PasswordField('Contraseña SMTP',
                                validators=[DataRequired(), Length(min=1, max=200)],
                                render_kw={"class": "form-control"})

    use_tls = BooleanField('Usar TLS', default=True,
                          render_kw={"class": "form-check-input"})

    use_ssl = BooleanField('Usar SSL', default=False,
                          render_kw={"class": "form-check-input"})

    # Configuración del remitente
    sender_email = StringField('Correo del Remitente',
                             validators=[DataRequired(), Email(), Length(min=1, max=120)],
                             render_kw={"class": "form-control", "placeholder": "remitente@alcaldia.gob"})

    sender_name = StringField('Nombre del Remitente',
                            validators=[DataRequired(), Length(min=1, max=100)],
                            render_kw={"class": "form-control", "placeholder": "Alcaldía de [Municipio]"})

    # Estado
    is_active = BooleanField('Configuración Activa', default=True,
                           render_kw={"class": "form-check-input"})

    # Botones
    submit = SubmitField('Guardar Configuración',
                        render_kw={"class": "btn btn-primary"})

    test_email = SubmitField('Probar Configuración',
                           render_kw={"class": "btn btn-info"})


class TestEmailForm(FlaskForm):
    """Formulario para probar envío de email"""

    test_email = StringField('Correo de Prueba',
                           validators=[DataRequired(), Email()],
                           render_kw={"class": "form-control", "placeholder": "prueba@dominio.com"})

    submit = SubmitField('Enviar Email de Prueba',
                        render_kw={"class": "btn btn-success"})
