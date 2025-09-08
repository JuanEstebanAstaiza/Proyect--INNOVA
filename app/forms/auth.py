from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(message='El usuario es obligatorio')])
    password = PasswordField('Contraseña', validators=[DataRequired(message='La contraseña es obligatoria')])
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')

class RegistrationForm(FlaskForm):
    username = StringField('Usuario',
                          validators=[DataRequired(message='El usuario es obligatorio'),
                                    Length(min=3, max=64, message='El usuario debe tener entre 3 y 64 caracteres')])
    email = StringField('Correo Electrónico',
                       validators=[DataRequired(message='El correo es obligatorio'),
                                 Email(message='Ingrese un correo electrónico válido')])
    password = PasswordField('Contraseña',
                            validators=[DataRequired(message='La contraseña es obligatoria'),
                                      Length(min=6, message='La contraseña debe tener al menos 6 caracteres')])
    password2 = PasswordField('Repetir Contraseña',
                             validators=[DataRequired(message='Debe confirmar la contraseña'),
                                       EqualTo('password', message='Las contraseñas deben coincidir')])

    first_name = StringField('Nombre',
                            validators=[DataRequired(message='El nombre es obligatorio'),
                                      Length(max=64, message='El nombre no puede exceder 64 caracteres')])
    last_name = StringField('Apellido',
                           validators=[DataRequired(message='El apellido es obligatorio'),
                                     Length(max=64, message='El apellido no puede exceder 64 caracteres')])
    position = StringField('Cargo',
                          validators=[DataRequired(message='El cargo es obligatorio'),
                                    Length(max=100, message='El cargo no puede exceder 100 caracteres')])

    municipality = StringField('Alcaldía/Municipio',
                              validators=[DataRequired(message='La alcaldía es obligatoria'),
                                        Length(max=100, message='El nombre de la alcaldía no puede exceder 100 caracteres')])
    department = StringField('Departamento',
                            validators=[DataRequired(message='El departamento es obligatorio'),
                                      Length(max=100, message='El departamento no puede exceder 100 caracteres')])
    municipality_code = StringField('Código de Alcaldía',
                                   validators=[Length(max=20, message='El código no puede exceder 20 caracteres')])

    submit = SubmitField('Registrarse')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Este nombre de usuario ya está registrado. Por favor elija otro.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Este correo electrónico ya está registrado. Por favor use otro.')
