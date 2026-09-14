from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.utils.fechas import ahora_utc

try:
    from werkzeug.urls import url_parse
except ImportError:
    from urllib.parse import urlparse as url_parse
import uuid

from app import db
from app.forms.auth import LoginForm, RegistrationForm
from app.models import User
from app.models.active_session import ActiveSession
from app.models.activity_log import ActivityLog

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def get_device_info():
    """
    Recopila información del dispositivo y navegador para fingerprinting
    """
    user_agent = request.headers.get('User-Agent', '')

    # Información básica del dispositivo
    device_info = {
        'user_agent': user_agent,
        'platform': request.headers.get('Sec-Ch-Ua-Platform', '').strip('"'),
        'language': request.headers.get('Accept-Language', '').split(',')[0] if request.headers.get('Accept-Language') else '',
        'timezone': request.headers.get('Timezone', ''),
        'screen_resolution': request.form.get('screen_resolution', ''),
        'cookie_enabled': True,  # Asumimos que sí porque están usando la app
        'ip_address': request.remote_addr,
        'timestamp': ahora_utc().isoformat(),
        'session_id': str(uuid.uuid4())  # ID único para esta sesión
    }

    # Limpiar valores vacíos
    device_info = {k: v for k, v in device_info.items() if v and v != ''}

    return device_info

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.verify_password(form.password.data):
            flash('Usuario o contraseña inválidos', 'error')
            return redirect(url_for('auth.login'))

        if not user.is_active:
            flash('Su cuenta está desactivada. Contacte al administrador.', 'error')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)

        # Actualizar último login
        user.update_last_login()

        # Recopilar información del dispositivo
        device_info = get_device_info()

        # Generar ID único para la sesión
        session_id = str(uuid.uuid4())

        # Crear sesión con JWT (invalida sesiones anteriores del mismo usuario)
        active_session = ActiveSession.create_session_with_jwt(
            user_id=user.id,
            session_id=session_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            device_info=device_info
        )

        # Almacenar información de la sesión en Flask session
        session['jwt_token'] = active_session.jwt_token
        session['session_id'] = session_id
        session['device_fingerprint'] = active_session.device_fingerprint

        # Registrar actividad de login con JWT
        ActivityLog.log_activity(
            'login',
            f'Inicio de sesión exitoso desde {request.remote_addr} (JWT: {active_session.jwt_token[:20]}...)',
            request.remote_addr,
            request.headers.get('User-Agent')
        )

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        return redirect(next_page)

    return render_template('auth/login.html', title='Iniciar Sesión', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    # Obtener información de la sesión JWT
    jwt_token = session.get('jwt_token')
    session_id = session.get('session_id')

    # Registrar actividad de logout
    ActivityLog.log_activity(
        'logout',
        f'Cierre de sesión desde {request.remote_addr} (JWT: {jwt_token[:20] if jwt_token else "N/A"}...)',
        request.remote_addr,
        request.headers.get('User-Agent')
    )

    # Marcar sesión JWT como inactiva si existe
    if jwt_token and session_id:
        active_session = ActiveSession.query.filter_by(
            user_id=current_user.id,
            session_id=session_id,
            jwt_token=jwt_token
        ).first()
        if active_session:
            active_session.is_active = False
            db.session.commit()

    # Limpiar datos de sesión
    session.pop('jwt_token', None)
    session.pop('session_id', None)
    session.pop('device_fingerprint', None)

    logout_user()
    flash('Ha cerrado sesión exitosamente.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            position=form.position.data,
            municipality=form.municipality.data,
            department=form.department.data,
            municipality_code=form.municipality_code.data
        )
        user.password = form.password.data

        db.session.add(user)
        db.session.commit()

        # Registrar actividad de registro
        from app.models.activity_log import ActivityLog
        ActivityLog.log_activity(
            'user_registration',
            f'Nuevo usuario registrado: {user.username}',
            request.remote_addr,
            request.headers.get('User-Agent')
        )

        flash('¡Registro exitoso! Ahora puede iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', title='Registro', form=form)
