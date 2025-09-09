from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.forms.auth import ProfileEditForm, ChangePasswordForm
from app.models import ActiveSession

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    from app.models import PlanDesarrollo
    # Obtener el plan activo del usuario actual
    plan_activo = PlanDesarrollo.query.filter_by(
        municipio=current_user,
        estado='activo'
    ).first()

    return render_template('main/dashboard.html', title='Dashboard', plan_activo=plan_activo)

@main_bp.route('/profile')
@login_required
def profile():
    return render_template('main/profile.html', title='Perfil de Usuario')

@main_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileEditForm(
        original_username=current_user.username,
        original_email=current_user.email,
        obj=current_user
    )

    if form.validate_on_submit():
        # Actualizar la información del usuario
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.position = form.position.data
        current_user.municipality = form.municipality.data
        current_user.department = form.department.data
        current_user.municipality_code = form.municipality_code.data

        try:
            db.session.commit()

            # Registrar actividad
            from app.models.activity_log import ActivityLog
            ActivityLog.log_activity(
                'edit_profile',
                'Perfil de usuario actualizado',
                request.remote_addr,
                request.headers.get('User-Agent')
            )

            flash('Tu perfil ha sido actualizado exitosamente.', 'success')
            return redirect(url_for('main.profile'))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el perfil. Por favor intenta nuevamente.', 'error')

    return render_template('main/edit_profile.html', title='Editar Perfil', form=form)

@main_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        # Verificar que la contraseña actual sea correcta
        if not current_user.verify_password(form.current_password.data):
            flash('La contraseña actual es incorrecta.', 'error')
            return redirect(url_for('main.change_password'))

        # Actualizar la contraseña
        current_user.password = form.new_password.data

        try:
            db.session.commit()

            # Registrar actividad antes del logout
            from app.models.activity_log import ActivityLog
            ActivityLog.log_activity(
                'change_password',
                'Contraseña de usuario cambiada',
                request.remote_addr,
                request.headers.get('User-Agent')
            )

            flash('Tu contraseña ha sido cambiada exitosamente.', 'success')
            # Forzar logout por seguridad
            logout_user()
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Error al cambiar la contraseña. Por favor intenta nuevamente.', 'error')

    return render_template('main/change_password.html', title='Cambiar Contraseña', form=form)

# =============================================
# API ENDPOINTS PARA MONITOREO DE ACTIVIDAD
# =============================================

@main_bp.route('/api/activity/update', methods=['POST'])
@login_required
def update_user_activity():
    """API endpoint to update user activity"""
    try:
        data = request.get_json() or {}

        # Buscar o crear sesión activa para el usuario
        session_id = request.cookies.get('session', str(hash(str(current_user.id) + str(request.remote_addr))))
        active_session = ActiveSession.query.filter_by(
            user_id=current_user.id,
            session_id=session_id
        ).first()

        if not active_session:
            active_session = ActiveSession(
                user_id=current_user.id,
                session_id=session_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                device_info=data
            )
            db.session.add(active_session)
        else:
            active_session.update_activity()

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Activity updated',
            'timestamp': active_session.last_activity.isoformat(),
            'session_id': session_id
        })

    except Exception as e:
        print(f"Activity update error for user {current_user.username}: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@main_bp.route('/api/activity/heartbeat', methods=['POST'])
@login_required
def user_heartbeat():
    """API endpoint for user heartbeat"""
    try:
        # Actualizar la actividad del usuario
        session_id = request.cookies.get('session', str(hash(str(current_user.id) + str(request.remote_addr))))
        active_session = ActiveSession.query.filter_by(
            user_id=current_user.id,
            session_id=session_id
        ).first()

        if active_session:
            active_session.update_activity()
            db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Heartbeat received',
            'timestamp': active_session.last_activity.isoformat() if active_session else None
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@main_bp.route('/api/activity/beforeunload', methods=['POST'])
@login_required
def handle_beforeunload():
    """API endpoint for page unload events"""
    try:
        data = request.get_json() or {}

        # Registrar el evento de salida de página (solo si hay URL)
        if data.get('url'):
            from app.models.activity_log import ActivityLog
            ActivityLog.log_activity(
                'page_unload',
                f'Página cerrada: {data.get("url")}',
                request.remote_addr,
                request.headers.get('User-Agent')
            )

        return jsonify({'status': 'success'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
