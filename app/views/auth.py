from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
try:
    from werkzeug.urls import url_parse
except ImportError:
    from urllib.parse import urlparse as url_parse
from app import db
from app.models import User
from app.forms.auth import LoginForm, RegistrationForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

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

        # Registrar actividad de login
        from app.models.activity_log import ActivityLog
        ActivityLog.log_activity(
            'login',
            f'Inicio de sesión exitoso desde {request.remote_addr}',
            request.remote_addr,
            request.headers.get('User-Agent')
        )

        # Crear o actualizar sesión activa
        from app.models.active_session import ActiveSession
        session_id = request.cookies.get('session', str(hash(str(user.id) + str(request.remote_addr))))
        active_session = ActiveSession.query.filter_by(
            user_id=user.id,
            session_id=session_id
        ).first()

        if not active_session:
            active_session = ActiveSession(
                user_id=user.id,
                session_id=session_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(active_session)
        else:
            active_session.is_active = True
            active_session.update_activity()

        db.session.commit()

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        return redirect(next_page)

    return render_template('auth/login.html', title='Iniciar Sesión', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    # Registrar actividad de logout antes de cerrar sesión
    from app.models.activity_log import ActivityLog
    ActivityLog.log_activity(
        'logout',
        f'Cierre de sesión desde {request.remote_addr}',
        request.remote_addr,
        request.headers.get('User-Agent')
    )

    # Marcar sesión como inactiva
    from app.models.active_session import ActiveSession
    session_id = request.cookies.get('session', str(hash(str(current_user.id) + str(request.remote_addr))))
    active_session = ActiveSession.query.filter_by(
        user_id=current_user.id,
        session_id=session_id
    ).first()
    if active_session:
        active_session.is_active = False
        db.session.commit()

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
