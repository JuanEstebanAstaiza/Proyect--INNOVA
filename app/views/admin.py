from datetime import datetime, timedelta

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import desc

from app import db
from app.models import (
    ActiveSession,
    ActivityLog,
    Componente,
    IndicadorProducto,
    LineaEstrategica,
    PlanDesarrollo,
    Programa,
    Proyecto,
    Role,
    RowPermission,
    SMTPConfig,
    User,
    UserRole,
    UserTempPassword,
)
from app.utils.fechas import ahora_utc

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def require_admin():
    """Require admin role for all admin routes"""
    if not current_user.is_admin():
        flash('Acceso denegado. Se requieren permisos de administrador.', 'error')
        return redirect(url_for('main.dashboard'))

@admin_bp.route('/dashboard')
def dashboard():
    """Admin dashboard with overview statistics including JWT"""
    # Get statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admin_users = User.query.filter_by(legacy_role='admin').count()

    # Get plans statistics
    from app.models import PlanDesarrollo
    planes_visibles = PlanDesarrollo.visibles_para(current_user)
    total_plans = planes_visibles.count()
    active_plans = planes_visibles.filter(PlanDesarrollo.estado == 'activo').count()

    recent_activities = ActivityLog.query.order_by(desc(ActivityLog.timestamp)).limit(10).all()

    # Obtener sesiones activas con validación JWT
    raw_active_sessions = ActiveSession.query.filter_by(is_active=True).all()
    valid_sessions = []
    invalid_sessions = []

    for session in raw_active_sessions:
        if session.validate_jwt() and not session.is_jwt_expired():
            valid_sessions.append(session)
        else:
            # Marcar sesiones inválidas como inactivas
            session.is_active = False
            invalid_sessions.append(session)

    # Commit cambios si hay sesiones inválidas
    if invalid_sessions:
        db.session.commit()

    inactive_sessions = ActiveSession.get_inactive_sessions()

    # Estadísticas JWT
    jwt_stats = {
        'valid_sessions': len(valid_sessions),
        'invalid_sessions': len(invalid_sessions),
        'total_jwt_sessions': len(raw_active_sessions),
        'jwt_validation_rate': (len(valid_sessions) / len(raw_active_sessions) * 100) if raw_active_sessions else 0
    }

    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'admin_users': admin_users,
        'total_sessions': len(valid_sessions),  # Solo sesiones válidas
        'inactive_sessions': len(inactive_sessions),
        'jwt_stats': jwt_stats
    }

    # Add plans statistics to stats object
    stats['total_plans'] = total_plans
    stats['active_plans'] = active_plans

    return render_template('admin/dashboard.html',
                         title='Panel de Administrador',
                         stats=stats,
                         recent_activities=recent_activities,
                         active_sessions=valid_sessions,  # Usar valid_sessions en lugar de active_sessions
                         inactive_sessions=inactive_sessions)

@admin_bp.route('/users')
def users():
    """User management page"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    users_query = User.query.order_by(User.created_at.desc())
    users_pagination = users_query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('admin/users.html',
                         title='Gestión de Usuarios',
                         users=users_pagination.items,
                         pagination=users_pagination)

@admin_bp.route('/activities')
def activities():
    """Activity log viewer"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    user_filter = request.args.get('user', type=int)
    action_filter = request.args.get('action')

    query = ActivityLog.query

    if user_filter:
        query = query.filter_by(user_id=user_filter)
    if action_filter:
        query = query.filter_by(action=action_filter)

    activities_pagination = query.order_by(desc(ActivityLog.timestamp)).paginate(
        page=page, per_page=per_page, error_out=False)

    # Get unique actions for filter dropdown
    unique_actions = db.session.query(ActivityLog.action).distinct().all()
    actions = [action[0] for action in unique_actions]

    # Get all users for filter dropdown
    all_users = User.query.all()

    # Calculate statistics
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Get activity counts for today
    logins_today = ActivityLog.query.filter(
        ActivityLog.action == 'login',
        ActivityLog.timestamp >= today_start
    ).count()

    # Get total activity counts
    total_plans = ActivityLog.query.filter(ActivityLog.action == 'create_plan').count()
    total_edits = ActivityLog.query.filter(ActivityLog.action.like('%edit%')).count()
    total_logins = ActivityLog.query.filter(ActivityLog.action == 'login').count()

    # Get unique users count (from today's activities)
    unique_users_today = ActivityLog.query.filter(
        ActivityLog.timestamp >= today_start
    ).with_entities(ActivityLog.user_id).distinct().count()

    return render_template('admin/activities.html',
                         title='Registro de Actividades',
                         activities=activities_pagination.items,
                         pagination=activities_pagination,
                         actions=actions,
                         all_users=all_users,
                         current_user_filter=user_filter,
                         current_action_filter=action_filter,
                         today_start=today_start,
                         logins_today=logins_today,
                         total_plans=total_plans,
                         total_edits=total_edits,
                         total_logins=total_logins,
                         unique_users_today=unique_users_today)

@admin_bp.route('/sessions')
def sessions():
    """Active sessions monitor with JWT validation"""
    # Obtener todas las sesiones marcadas como activas
    raw_sessions = ActiveSession.query.filter_by(is_active=True).all()

    # Filtrar sesiones con JWT válido (sesiones únicas por usuario)
    active_sessions = []
    invalid_sessions = []

    for session in raw_sessions:
        if session.validate_jwt() and not session.is_jwt_expired():
            active_sessions.append(session)
        else:
            # Marcar sesiones inválidas como inactivas
            session.is_active = False
            invalid_sessions.append(session)

    # Commit cambios si hay sesiones inválidas
    if invalid_sessions:
        db.session.commit()

    # Obtener sesiones inactivas (sin validación adicional ya que están inactivas)
    inactive_sessions = ActiveSession.get_inactive_sessions()

    # Calculate statistics
    total_active = len(active_sessions)
    total_inactive = len(inactive_sessions)
    total_invalid = len(invalid_sessions)

    # Count sessions with alerts (>30 minutes inactive)
    critical_alerts = sum(1 for session in inactive_sessions if session.get_inactive_duration() > 30)

    # Calculate average inactive duration for active sessions
    if active_sessions:
        total_duration = sum(session.get_inactive_duration() for session in active_sessions)
        avg_duration = total_duration / len(active_sessions)
    else:
        avg_duration = 0

    return render_template('admin/sessions.html',
                         title='Monitoreo de Sesiones JWT',
                         active_sessions=active_sessions,
                         inactive_sessions=inactive_sessions,
                         invalid_sessions=invalid_sessions,
                         total_active=total_active,
                         total_inactive=total_inactive,
                         total_invalid=total_invalid,
                         critical_alerts=critical_alerts,
                         avg_duration=avg_duration,
                         jwt_enabled=True)

@admin_bp.route('/api/sessions/update/<session_id>', methods=['POST'])
def update_session_activity(session_id):
    """API endpoint to update session activity with JWT validation"""
    session = ActiveSession.query.filter_by(session_id=session_id, is_active=True).first()

    if not session:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404

    # Validar JWT antes de actualizar actividad
    if not session.validate_jwt():
        # JWT inválido - marcar sesión como inactiva
        session.is_active = False
        db.session.commit()
        return jsonify({'status': 'error', 'message': 'Invalid JWT token'}), 401

    if session.is_jwt_expired():
        # JWT expirado - marcar sesión como inactiva
        session.is_active = False
        db.session.commit()
        return jsonify({'status': 'error', 'message': 'JWT token expired'}), 401

    # JWT válido - actualizar actividad
    session.update_activity()
    return jsonify({
        'status': 'success',
        'jwt_valid': True,
        'last_activity': session.last_activity.isoformat()
    })

@admin_bp.route('/api/sessions/force-logout/<user_id>', methods=['POST'])
@login_required
def force_user_logout(user_id):
    """API endpoint to force logout all sessions of a specific user"""
    if not current_user.is_admin():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    try:
        user_id_int = int(user_id)
        closed_count = ActiveSession.force_logout_user(user_id_int)

        return jsonify({
            'status': 'success',
            'message': f'Closed {closed_count} sessions for user {user_id}',
            'sessions_closed': closed_count
        })

    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid user ID'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/api/sessions/cleanup-expired', methods=['POST'])
@login_required
def cleanup_expired_sessions():
    """API endpoint to cleanup expired JWT sessions"""
    if not current_user.is_admin():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    try:
        cleaned_count = ActiveSession.cleanup_expired_jwt_sessions()

        return jsonify({
            'status': 'success',
            'message': f'Cleaned up {cleaned_count} expired JWT sessions',
            'sessions_cleaned': cleaned_count
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/api/sessions/inactive-alerts')
def get_inactive_alerts():
    """API endpoint to get inactive session alerts"""
    inactive_sessions = ActiveSession.get_inactive_sessions()
    alerts = []

    for session in inactive_sessions:
        alerts.append({
            'user': session.user.username,
            'session_id': session.session_id,
            'last_activity': session.last_activity.isoformat(),
            'inactive_minutes': round(session.get_inactive_duration(), 1),
            'ip_address': session.ip_address
        })

    return jsonify({'alerts': alerts, 'count': len(alerts)})

@admin_bp.route('/api/stats/live')
def get_live_stats():
    """API endpoint for live dashboard statistics"""
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    active_sessions = ActiveSession.query.filter_by(is_active=True).count()
    inactive_sessions = len(ActiveSession.get_inactive_sessions())

    # Recent activities (last 5 minutes)
    recent_time = ahora_utc() - timedelta(minutes=5)
    recent_activities = ActivityLog.query.filter(
        ActivityLog.timestamp >= recent_time
    ).order_by(desc(ActivityLog.timestamp)).limit(5).all()

    activities_data = []
    for activity in recent_activities:
        activities_data.append({
            'username': activity.user.username,
            'action': activity.action,
            'description': activity.description,
            'timestamp': activity.timestamp.isoformat(),
            'ip_address': activity.ip_address
        })

    return jsonify({
        'stats': {
            'total_users': total_users,
            'active_users': active_users,
            'active_sessions': active_sessions,
            'inactive_sessions': inactive_sessions
        },
        'recent_activities': activities_data
    })

@admin_bp.route('/users/create', methods=['GET', 'POST'])
def create_user():
    """Create new user"""
    from app.forms.auth import ProfileEditForm

    form = ProfileEditForm()
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

        # Asignar rol legacy basado en el rol seleccionado
        selected_role = form.role.data
        if selected_role == 'Administrador':
            user.legacy_role = 'admin'
        elif selected_role in ['Editor General', 'Editor de Ejecución', 'Editor de Metas']:
            user.legacy_role = 'editor'
        else:
            user.legacy_role = 'viewer'

        # Generar contraseña temporal segura
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        temp_password = ''.join(secrets.choice(alphabet) for i in range(12))
        user.password = temp_password

        try:
            db.session.add(user)
            db.session.commit()

            # Asignar rol del sistema avanzado
            from app.models import Role, UserRole
            role_obj = Role.query.filter_by(name=selected_role, is_active=True).first()
            if role_obj:
                user_role = UserRole(
                    user_id=user.id,
                    role_id=role_obj.id,
                    is_active=True
                )
                db.session.add(user_role)
                db.session.commit()

            # Crear registro de contraseña temporal
            temp_password_record = UserTempPassword.create_for_user(user, temp_password)
            db.session.add(temp_password_record)
            db.session.commit()

            # Intentar enviar email con credenciales
            smtp_config = SMTPConfig.get_by_municipality(user.municipality)
            email_sent = False

            if smtp_config and smtp_config.is_active:
                try:
                    from app.utils.email_service import EmailService
                    email_sent = EmailService.send_user_credentials_email(user, temp_password, smtp_config)
                except Exception as e:
                    current_app.logger.error(f"Error enviando email: {e}")

            # Log the activity
            ActivityLog.log_activity(
                'create_user',
                f'Creado nuevo usuario: {user.username}',
                request.remote_addr,
                request.headers.get('User-Agent')
            )

            if email_sent:
                flash(f'Usuario {user.username} creado exitosamente. Las credenciales han sido enviadas por email.', 'success')
            else:
                flash(f'Usuario {user.username} creado exitosamente. Contraseña temporal: <strong>{temp_password}</strong><br>'
                      '<small class="text-muted">Guarda esta contraseña en un lugar seguro. '
                      'Si no se envió el email, configura SMTP en el panel de administración.</small>', 'success')

            return redirect(url_for('admin.users'))
        except Exception:
            db.session.rollback()
            flash('Error al crear el usuario. Por favor intenta nuevamente.', 'error')

    return render_template('admin/create_user.html', title='Crear Usuario', form=form)

# ==================== CONFIGURACIÓN SMTP ====================

@admin_bp.route('/smtp-config')
@login_required
def smtp_config_list():
    """Listar configuraciones SMTP por municipio"""
    smtp_configs = SMTPConfig.query.order_by(SMTPConfig.municipality).all()
    return render_template('admin/smtp_configs.html', title='Configuración SMTP', smtp_configs=smtp_configs)

@admin_bp.route('/smtp-config/<municipality>/edit', methods=['GET', 'POST'])
@login_required
def edit_smtp_config(municipality):
    """Editar configuración SMTP para un municipio"""
    from app.forms.smtp import SMTPConfigForm

    smtp_config = SMTPConfig.get_or_create(municipality)
    form = SMTPConfigForm(obj=smtp_config)

    # Llenar choices de municipios
    from app.models import User
    municipios = db.session.query(User.municipality).distinct().all()
    form.municipality.choices = [(m[0], m[0]) for m in municipios]
    form.municipality.data = municipality

    if form.validate_on_submit():
        # Actualizar configuración
        smtp_config.smtp_server = form.smtp_server.data
        smtp_config.smtp_port = form.smtp_port.data
        smtp_config.smtp_username = form.smtp_username.data
        smtp_config.smtp_password = form.smtp_password.data
        smtp_config.use_tls = form.use_tls.data
        smtp_config.use_ssl = form.use_ssl.data
        smtp_config.sender_email = form.sender_email.data
        smtp_config.sender_name = form.sender_name.data
        smtp_config.is_active = form.is_active.data

        try:
            db.session.commit()

            # Si se presionó el botón de prueba
            if 'test_email' in request.form:
                # Redirigir a página de prueba
                return redirect(url_for('admin.test_smtp_config', municipality=municipality))

            flash('Configuración SMTP guardada exitosamente.', 'success')
            return redirect(url_for('admin.smtp_config_list'))

        except Exception:
            db.session.rollback()
            flash('Error al guardar la configuración.', 'error')

    return render_template('admin/edit_smtp_config.html', title=f'Configuración SMTP - {municipality}',
                         form=form, smtp_config=smtp_config)

@admin_bp.route('/smtp-config/<municipality>/test', methods=['GET', 'POST'])
@login_required
def test_smtp_config(municipality):
    """Probar configuración SMTP"""
    from app.forms.smtp import TestEmailForm

    smtp_config = SMTPConfig.get_by_municipality(municipality)
    if not smtp_config:
        flash('Configuración SMTP no encontrada.', 'error')
        return redirect(url_for('admin.smtp_config_list'))

    form = TestEmailForm()

    if form.validate_on_submit():
        try:
            from app.utils.email_service import EmailService
            success = EmailService.send_test_email(smtp_config, form.test_email.data)

            if success:
                flash(f'Email de prueba enviado exitosamente a {form.test_email.data}', 'success')
            else:
                flash('Error al enviar el email de prueba. Revisa la configuración.', 'error')

        except Exception as e:
            flash(f'Error al probar la configuración: {e!s}', 'error')

    return render_template('admin/test_smtp_config.html', title=f'Probar SMTP - {municipality}',
                         form=form, smtp_config=smtp_config)

# ==================== GESTIÓN DE CONTRASEÑAS TEMPORALES ====================

@admin_bp.route('/users/<int:user_id>/temp-password')
@login_required
def view_user_temp_password(user_id):
    """Ver contraseña temporal de un usuario"""
    user = db.get_or_404(User, user_id)
    temp_password_record = UserTempPassword.get_active_for_user(user_id)

    return render_template('admin/user_temp_password.html',
                         title=f'Contraseña Temporal - {user.username}',
                         user=user,
                         temp_password_record=temp_password_record)

@admin_bp.route('/users/<int:user_id>/send-credentials', methods=['POST'])
@login_required
def send_user_credentials(user_id):
    """Reenviar credenciales por email"""
    user = db.get_or_404(User, user_id)
    temp_password_record = UserTempPassword.get_active_for_user(user_id)

    if not temp_password_record:
        flash('No hay contraseña temporal activa para este usuario.', 'warning')
        return redirect(url_for('admin.view_user_temp_password', user_id=user_id))

    # Obtener configuración SMTP
    smtp_config = SMTPConfig.get_by_municipality(user.municipality)

    if not smtp_config or not smtp_config.is_active:
        flash('No hay configuración SMTP activa para el municipio de este usuario.', 'warning')
        return redirect(url_for('admin.view_user_temp_password', user_id=user_id))

    try:
        from app.utils.email_service import EmailService
        success = EmailService.send_user_credentials_email(user, temp_password_record.plain_password, smtp_config)

        if success:
            flash('Credenciales enviadas exitosamente por email.', 'success')
        else:
            flash('Error al enviar las credenciales por email.', 'error')

    except Exception as e:
        flash(f'Error al enviar email: {e!s}', 'error')

    return redirect(url_for('admin.view_user_temp_password', user_id=user_id))

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    """Toggle user active/inactive status"""
    user = db.get_or_404(User, user_id)

    # Prevent admin from deactivating themselves
    if user.id == current_user.id:
        flash('No puedes desactivar tu propia cuenta.', 'error')
        return redirect(url_for('admin.users'))

    user.is_active = not user.is_active
    db.session.commit()

    status = 'activado' if user.is_active else 'desactivado'
    flash(f'Usuario {user.username} ha sido {status}.', 'success')

    # Log the activity
    ActivityLog.log_activity(
        'toggle_user_status',
        f'Usuario {user.username} {status}',
        request.remote_addr,
        request.headers.get('User-Agent')
    )

    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/change-role', methods=['POST'])
def change_user_role(user_id):
    """Change user role"""
    user = db.get_or_404(User, user_id)
    new_role = request.form.get('role')

    if new_role not in ['admin', 'editor', 'viewer']:
        flash('Rol inválido.', 'error')
        return redirect(url_for('admin.users'))

    old_role = user.role
    user.role = new_role
    db.session.commit()

    flash(f'Rol de {user.username} cambiado de {old_role} a {new_role}.', 'success')

    # Log the activity
    ActivityLog.log_activity(
        'change_user_role',
        f'Rol de {user.username} cambiado: {old_role} → {new_role}',
        request.remote_addr,
        request.headers.get('User-Agent')
    )

    return redirect(url_for('admin.users'))

# =============================================
# API ENDPOINTS PARA MONITOREO DE ACTIVIDAD
# =============================================


@admin_bp.route('/api/activity/heartbeat', methods=['POST'])
@login_required
def user_heartbeat():
    """API endpoint for user heartbeat"""
    try:
        data = request.get_json() or {}

        # Buscar sesión activa usando JWT
        from flask import session as flask_session
        jwt_token = flask_session.get('jwt_token')
        session_id = flask_session.get('session_id')

        if jwt_token and session_id:
            # Validar sesión JWT
            is_valid, active_session = ActiveSession.validate_session_jwt(session_id, jwt_token)

            if is_valid and active_session:
                # Actualizar actividad si no ha sido muy reciente
                time_since_activity = data.get('time_since_activity', 0)
                if time_since_activity > 60:  # Solo actualizar si ha pasado más de 1 minuto
                    active_session.update_activity()
            else:
                # Sesión JWT inválida - no hacer nada, dejará de actualizarse
                pass

        return jsonify({
            'status': 'success',
            'timestamp': ahora_utc().isoformat()
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/api/activity/beforeunload', methods=['POST'])
@login_required
def handle_page_unload():
    """API endpoint to handle page unload events"""
    try:
        # Solo registrar el evento, no necesitamos respuesta
        ActivityLog.log_activity(
            'page_unload',
            'Usuario cerró/refrescó la página',
            request.remote_addr,
            request.headers.get('User-Agent')
        )

        return '', 204  # No Content response

    except Exception:
        current_app.logger.exception('No se pudo registrar el cierre de página')
        return '', 500

@admin_bp.route('/api/activity/alert/<int:user_id>', methods=['POST'])
@login_required
def send_inactivity_alert(user_id):
    """Send inactivity alert to a specific user"""
    if not current_user.is_admin():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    try:
        user = db.get_or_404(User, user_id)

        # Registrar la alerta en el log
        ActivityLog.log_activity(
            'inactivity_alert_sent',
            f'Alerta de inactividad enviada a {user.username}',
            request.remote_addr,
            request.headers.get('User-Agent')
        )

        # Aquí se podría implementar envío de notificaciones push
        # Por ahora solo registramos el evento

        return jsonify({
            'status': 'success',
            'message': f'Alert sent to {user.username}',
            'timestamp': ahora_utc().isoformat()
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# =====================================
# GESTIÓN DE ROLES Y PERMISOS
# =====================================

@admin_bp.route('/roles')
def roles():
    """Gestión de roles del sistema"""
    roles = Role.query.order_by(Role.name).all()
    return render_template('admin/roles.html', title='Gestión de Roles', roles=roles)

@admin_bp.route('/roles/create', methods=['GET', 'POST'])
def create_role():
    """Crear nuevo rol"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        color = request.form.get('color', '#007bff')

        # Verificar si el rol ya existe
        existing_role = Role.query.filter_by(name=name).first()
        if existing_role:
            flash('Ya existe un rol con ese nombre.', 'error')
            return redirect(url_for('admin.create_role'))

        # Crear nuevo rol
        new_role = Role(name=name, description=description, color=color)
        db.session.add(new_role)
        db.session.commit()

        # Configurar permisos por defecto
        for permission in new_role.column_permissions:
            # Crear el nombre del campo del formulario
            field_name = permission.column_name
            field_name = field_name.replace(" ", "_")
            field_name = field_name.replace("%", "pct")
            field_name = field_name.replace("(", "")
            field_name = field_name.replace(")", "")
            field_name = field_name.replace("/", "_")
            field_name = field_name.replace("'", "")
            field_name = f'edit_{field_name.lower()}'

            can_edit = request.form.get(field_name, 'false') == 'true'
            permission.can_edit = can_edit
            permission.can_view = True  # Siempre pueden ver

        db.session.commit()

        # Registrar actividad
        ActivityLog.log_activity(
            'role_created',
            f'Rol "{name}" creado por {current_user.username}',
            request.remote_addr,
            request.headers.get('User-Agent')
        )

        flash(f'Rol "{name}" creado exitosamente.', 'success')
        return redirect(url_for('admin.roles'))

    return render_template('admin/create_role.html', title='Crear Rol')

@admin_bp.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
def edit_role(role_id):
    """Editar rol existente"""
    role = db.get_or_404(Role, role_id)

    if request.method == 'POST':
        # Actualizar información básica
        role.name = request.form.get('name')
        role.description = request.form.get('description')
        role.color = request.form.get('color', role.color)

        # Actualizar permisos
        for permission in role.column_permissions:
            # Crear el nombre del campo del formulario
            field_name = permission.column_name
            field_name = field_name.replace(" ", "_")
            field_name = field_name.replace("%", "pct")
            field_name = field_name.replace("(", "")
            field_name = field_name.replace(")", "")
            field_name = field_name.replace("/", "_")
            field_name = field_name.replace("'", "")
            field_name = f'edit_{field_name.lower()}'

            can_edit = request.form.get(field_name, 'false') == 'true'
            permission.can_edit = can_edit
            permission.can_view = True

        db.session.commit()

        # Registrar actividad
        ActivityLog.log_activity(
            'role_updated',
            f'Rol "{role.name}" actualizado por {current_user.username}',
            request.remote_addr,
            request.headers.get('User-Agent')
        )

        flash(f'Rol "{role.name}" actualizado exitosamente.', 'success')
        return redirect(url_for('admin.roles'))

    return render_template('admin/edit_role.html', title='Editar Rol', role=role)

@admin_bp.route('/roles/<int:role_id>/delete', methods=['POST'])
def delete_role(role_id):
    """Eliminar rol"""
    role = db.get_or_404(Role, role_id)

    if role.is_system_role:
        flash('No se pueden eliminar roles del sistema.', 'error')
        return redirect(url_for('admin.roles'))

    # Verificar si hay usuarios con este rol
    users_with_role = UserRole.query.filter_by(role_id=role_id, is_active=True).count()
    if users_with_role > 0:
        flash(f'No se puede eliminar el rol "{role.name}" porque hay {users_with_role} usuario(s) asignado(s).', 'error')
        return redirect(url_for('admin.roles'))

    # Eliminar rol
    db.session.delete(role)
    db.session.commit()

    # Registrar actividad
    ActivityLog.log_activity(
        'role_deleted',
        f'Rol "{role.name}" eliminado por {current_user.username}',
        request.remote_addr,
        request.headers.get('User-Agent')
    )

    flash(f'Rol "{role.name}" eliminado exitosamente.', 'success')
    return redirect(url_for('admin.roles'))

@admin_bp.route('/user-roles')
def user_roles():
    """Gestión de asignación de roles a usuarios"""
    # Obtener todos los usuarios con sus roles activos
    users = User.query.filter_by(is_active=True).all()
    roles = Role.query.filter_by(is_active=True).all()

    user_roles_data = []
    for user in users:
        # Obtener roles activos del usuario
        active_roles = [ur for ur in user.active_roles if ur.is_active]

        # Obtener permisos de fila del usuario con las relaciones cargadas
        row_permissions = RowPermission.query.filter_by(
            user_id=user.id,
            is_active=True
        ).options(
            db.joinedload(RowPermission.indicador),
            db.joinedload(RowPermission.proyecto),
            db.joinedload(RowPermission.programa),
            db.joinedload(RowPermission.componente),
            db.joinedload(RowPermission.linea_estrategica)
        ).all()

        user_roles_data.append({
            'user': user,
            'roles': active_roles,
            'role_names': [ur.role.name for ur in active_roles],
            'role_colors': [ur.role.color for ur in active_roles],
            'row_permissions': row_permissions
        })

    # Convertir roles a formato JSON serializable
    roles_data = []
    for role in roles:
        roles_data.append({
            'id': role.id,
            'name': role.name,
            'description': role.description,
            'color': role.color,
            'is_active': role.is_active,
            'created_at': role.created_at.isoformat() if role.created_at else None
        })

    return render_template('admin/user_roles.html',
                         title='Asignación de Roles',
                         user_roles_data=user_roles_data,
                         roles=roles_data)

@admin_bp.route('/users/<int:user_id>/assign-role', methods=['POST'])
def assign_role_to_user(user_id):
    """Asignar rol a usuario"""
    user = db.get_or_404(User, user_id)
    role_id = request.form.get('role_id', type=int)

    if not role_id:
        flash('Debe seleccionar un rol.', 'error')
        return redirect(url_for('admin.user_roles'))

    role = db.get_or_404(Role, role_id)

    # Verificar si ya tiene este rol asignado
    existing_assignment = UserRole.query.filter_by(
        user_id=user_id,
        role_id=role_id,
        is_active=True
    ).first()

    if existing_assignment:
        flash(f'El usuario {user.username} ya tiene asignado el rol "{role.name}".', 'warning')
        return redirect(url_for('admin.user_roles'))

    # Crear nueva asignación
    new_assignment = UserRole(
        user_id=user_id,
        role_id=role_id,
        assigned_by=current_user.id,
        notes=request.form.get('notes', '')
    )
    db.session.add(new_assignment)
    db.session.commit()

    # Registrar actividad
    ActivityLog.log_activity(
        'role_assigned',
        f'Rol "{role.name}" asignado a {user.username} por {current_user.username}',
        request.remote_addr,
        request.headers.get('User-Agent')
    )

    flash(f'Rol "{role.name}" asignado exitosamente a {user.username}.', 'success')
    return redirect(url_for('admin.user_roles'))

@admin_bp.route('/users/<int:user_id>/remove-role/<int:role_id>', methods=['POST'])
def remove_role_from_user(user_id, role_id):
    """Remover rol de usuario"""
    user = db.get_or_404(User, user_id)
    role = db.get_or_404(Role, role_id)

    # Buscar asignación activa
    assignment = UserRole.query.filter_by(
        user_id=user_id,
        role_id=role_id,
        is_active=True
    ).first()

    if not assignment:
        flash(f'El usuario {user.username} no tiene asignado el rol "{role.name}".', 'warning')
        return redirect(url_for('admin.user_roles'))

    # Desactivar asignación (no eliminar para mantener historial)
    assignment.is_active = False
    db.session.commit()

    # Registrar actividad
    ActivityLog.log_activity(
        'role_removed',
        f'Rol "{role.name}" removido de {user.username} por {current_user.username}',
        request.remote_addr,
        request.headers.get('User-Agent')
    )

    flash(f'Rol "{role.name}" removido exitosamente de {user.username}.', 'success')
    return redirect(url_for('admin.user_roles'))

@admin_bp.route('/user-row-permissions')
def user_row_permissions():
    """Gestión de permisos de fila por usuario"""
    # Obtener usuarios con permisos de fila
    users_with_permissions = db.session.query(User).join(RowPermission, RowPermission.user_id == User.id).distinct().all()
    all_users = User.query.filter_by(is_active=True).all()
    indicadores = IndicadorProducto.query.order_by(IndicadorProducto.nombre).all()

    permissions_data = []
    for user in users_with_permissions:
        user_permissions = RowPermission.query.filter_by(user_id=user.id).all()
        permissions_data.append({
            'user': user,
            'permissions': user_permissions,
            'count': len(user_permissions)
        })

    return render_template('admin/row_permissions.html',
                         title='Permisos de Fila',
                         permissions_data=permissions_data,
                         all_users=all_users,
                         indicadores=indicadores)

@admin_bp.route('/search-indicadores')
def search_indicadores():
    """API para buscar indicadores por texto"""
    query = request.args.get('q', '').strip()

    if not query:
        return jsonify({'results': []})

    # Buscar indicadores que contengan el texto en nombre, descripción o proyecto
    indicadores = IndicadorProducto.query.filter(
        db.or_(
            IndicadorProducto.nombre.ilike(f'%{query}%'),
            IndicadorProducto.descripcion.ilike(f'%{query}%'),
            IndicadorProducto.proyecto.has(db.or_(
                Proyecto.nombre.ilike(f'%{query}%'),
                Proyecto.programa.has(db.or_(
                    Programa.nombre.ilike(f'%{query}%'),
                    Programa.componente.has(db.or_(
                        Componente.nombre.ilike(f'%{query}%'),
                        Componente.linea_estrategica.has(
                            LineaEstrategica.nombre.ilike(f'%{query}%')
                        )
                    ))
                ))
            ))
        )
    ).limit(20).all()

    results = []
    for indicador in indicadores:
        results.append({
            'id': indicador.id,
            'text': f"{indicador.nombre} (Proyecto: {indicador.proyecto.nombre})",
            'proyecto': indicador.proyecto.nombre,
            'programa': indicador.proyecto.programa.nombre if indicador.proyecto.programa else 'N/A',
            'componente': indicador.proyecto.programa.componente.nombre if indicador.proyecto.programa and indicador.proyecto.programa.componente else 'N/A'
        })

    return jsonify({'results': results})

@admin_bp.route('/assign-row-permission', methods=['POST'])
def assign_row_permission():
    """Asignar permiso de fila a usuario"""
    user_id = request.form.get('user_id', type=int)
    indicador_id = request.form.get('indicador_id', type=int)
    search_term = request.form.get('search_term', '')

    if not all([user_id, indicador_id]):
        return jsonify({'status': 'error', 'message': 'Datos incompletos'}), 400

    user = db.get_or_404(User, user_id)
    indicador = db.get_or_404(IndicadorProducto, indicador_id)

    # Verificar si ya existe el permiso
    existing_permission = RowPermission.query.filter_by(
        user_id=user_id,
        indicador_id=indicador_id
    ).first()

    if existing_permission:
        return jsonify({'status': 'warning', 'message': 'El usuario ya tiene permiso para esta fila'})

    # Crear nuevo permiso
    new_permission = RowPermission(
        user_id=user_id,
        indicador_id=indicador_id,
        search_term=search_term,
        assigned_by=current_user.id
    )
    db.session.add(new_permission)
    db.session.commit()

    # Registrar actividad
    ActivityLog.log_activity(
        'row_permission_assigned',
        f'Permiso de fila asignado a {user.username} para "{indicador.nombre}" por {current_user.username}',
        request.remote_addr,
        request.headers.get('User-Agent')
    )

    return jsonify({
        'status': 'success',
        'message': f'Permiso asignado a {user.username}',
        'permission_id': new_permission.id
    })

@admin_bp.route('/remove-row-permission/<int:permission_id>', methods=['POST'])
def remove_row_permission(permission_id):
    """Remover permiso de fila"""
    permission = db.get_or_404(RowPermission, permission_id)

    # Eliminar permiso
    db.session.delete(permission)
    db.session.commit()

    # Registrar actividad
    ActivityLog.log_activity(
        'row_permission_removed',
        f'Permiso de fila removido de {permission.user.username} para indicador {permission.indicador.nombre} por {current_user.username}',
        request.remote_addr,
        request.headers.get('User-Agent')
    )

    return jsonify({'status': 'success', 'message': 'Permiso removido exitosamente'})

@admin_bp.route('/api/roles/stats')
@login_required
def get_roles_stats():
    """API endpoint para estadísticas de roles en tiempo real"""
    if not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        # Contar roles activos
        total_roles = Role.query.filter_by(is_active=True).count()

        # Contar usuarios con roles asignados
        users_with_roles = db.session.query(User).join(UserRole, UserRole.user_id == User.id).filter(
            UserRole.is_active.is_(True),
            User.is_active.is_(True)
        ).distinct().count()

        # Contar permisos de fila
        total_row_permissions = RowPermission.query.count()

        # Calcular total de columnas editables en el sistema
        total_editable_columns = 0
        roles = Role.query.filter_by(is_active=True).all()
        for role in roles:
            total_editable_columns += len(role.get_editable_columns())

        return jsonify({
            'total_roles': total_roles,
            'users_with_roles': users_with_roles,
            'total_row_permissions': total_row_permissions,
            'total_editable_columns': total_editable_columns
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/roles/guide')
def roles_guide():
    """Guía completa de roles y permisos"""
    return render_template('admin/roles_guide.html', title='Guía de Roles y Permisos')

# =============================================
# ENDPOINTS PARA PERMISOS DE FILA
# =============================================

@admin_bp.route('/row-permissions')
@login_required
def manage_row_permissions():
    """Página principal de gestión de permisos de fila"""
    # Verificar si hay un plan activo
    from app.models import PlanDesarrollo
    active_plan = PlanDesarrollo.visibles_para(current_user).filter(PlanDesarrollo.estado == 'activo').first()

    if not active_plan:
        flash('No hay un plan de desarrollo activo. Los permisos de fila solo están disponibles cuando hay un plan activo.', 'warning')
        return redirect(url_for('admin.dashboard'))

    # Obtener todos los permisos de fila para el plan activo
    row_permissions_list = RowPermission.query.filter_by(
        plan_id=active_plan.id,
        is_active=True
    ).order_by(RowPermission.created_at.desc()).all()

    # Obtener todos los usuarios para el selector
    all_users = User.query.filter_by(is_active=True).order_by(User.first_name, User.last_name).all()

    return render_template('admin/row_permissions.html',
                         title='Permisos de Fila',
                         row_permissions=row_permissions_list,
                         active_plan=active_plan,
                         all_users=all_users)

@admin_bp.route('/row-permissions/create', methods=['POST'])
@login_required
def create_row_permission():
    """Asignar un nuevo permiso de fila"""
    try:
        # Verificar que hay un plan activo
        from app.models import PlanDesarrollo
        active_plan = PlanDesarrollo.visibles_para(current_user).filter(PlanDesarrollo.estado == 'activo').first()

        if not active_plan:
            return jsonify({
                'success': False,
                'message': 'No hay un plan de desarrollo activo.'
            }), 400

        # Obtener datos del formulario
        user_id = request.form.get('user_id', type=int)
        entity_type = request.form.get('entity_type')
        entity_id = request.form.get('entity_id', type=int)
        can_view = request.form.get('can_view') == 'on'
        can_edit = request.form.get('can_edit') == 'on'
        description = request.form.get('description', '')

        # Validaciones
        if not user_id or not entity_type or not entity_id:
            return jsonify({
                'success': False,
                'message': 'Todos los campos requeridos deben ser completados.'
            }), 400

        if not can_view and not can_edit:
            return jsonify({
                'success': False,
                'message': 'Debe seleccionar al menos un permiso (ver o editar).'
            }), 400

        # Verificar que el usuario existe
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'Usuario no encontrado.'
            }), 404

        # Crear el permiso de fila
        row_permission = RowPermission(
            user_id=user_id,
            plan_id=active_plan.id,
            permission_scope=entity_type,
            can_view=can_view,
            can_edit=can_edit,
            description=description,
            assigned_by=current_user.id
        )

        # Asignar la entidad específica según el tipo
        if entity_type == 'indicador':
            row_permission.indicador_id = entity_id
        elif entity_type == 'proyecto':
            row_permission.proyecto_id = entity_id
        elif entity_type == 'programa':
            row_permission.programa_id = entity_id
        elif entity_type == 'componente':
            row_permission.componente_id = entity_id
        elif entity_type == 'linea':
            row_permission.linea_estrategica_id = entity_id
        else:
            return jsonify({
                'success': False,
                'message': 'Tipo de entidad no válido.'
            }), 400

        # Verificar que no existe un permiso duplicado
        existing_permission = RowPermission.query.filter_by(
            user_id=user_id,
            plan_id=active_plan.id,
            indicador_id=row_permission.indicador_id,
            proyecto_id=row_permission.proyecto_id,
            programa_id=row_permission.programa_id,
            componente_id=row_permission.componente_id,
            linea_estrategica_id=row_permission.linea_estrategica_id,
            is_active=True
        ).first()

        if existing_permission:
            return jsonify({
                'success': False,
                'message': 'Ya existe un permiso activo para esta entidad y usuario.'
            }), 400

        # Guardar el permiso
        db.session.add(row_permission)
        db.session.commit()

        # Registrar en el log de actividad
        ActivityLog.log_activity(
            'assign_row_permission',
            f'Asignado permiso de fila a {user.get_full_name()} para {entity_type}',
            request.remote_addr,
            request.headers.get('User-Agent')
        )

        return jsonify({
            'success': True,
            'message': f'Permiso asignado exitosamente a {user.get_full_name()}.',
            'permission_id': row_permission.id
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error asignando permiso de fila: {e!s}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor. Inténtalo de nuevo.'
        }), 500

@admin_bp.route('/api/row-permissions/entities/<entity_type>')
@login_required
def get_entities_for_permission(entity_type):
    """Obtener entidades disponibles para asignar permisos"""
    try:
        plan_id = request.args.get('plan_id', type=int)
        if not plan_id:
            return jsonify([]), 400

        # Verificar que el plan existe y pertenece al usuario
        from app.models import PlanDesarrollo
        plan = (PlanDesarrollo.visibles_para(current_user)
                .filter(PlanDesarrollo.id == plan_id).first())

        if not plan:
            return jsonify([]), 403

        entities = []

        if entity_type == 'indicador':
            indicadores = IndicadorProducto.query.join(Proyecto).join(Programa).join(Componente).join(LineaEstrategica).filter(
                LineaEstrategica.plan_id == plan_id
            ).all()

            for indicador in indicadores:
                entities.append({
                    'id': indicador.id,
                    'name': f"{indicador.cod_indicador} - {indicador.nombre}",
                    'hierarchy': [
                        ('Línea Estratégica', indicador.proyecto.programa.componente.linea_estrategica.nombre, indicador.proyecto.programa.componente.linea_estrategica.id),
                        ('Componente', indicador.proyecto.programa.componente.nombre, indicador.proyecto.programa.componente.id),
                        ('Programa', indicador.proyecto.programa.nombre, indicador.proyecto.programa.id),
                        ('Proyecto', indicador.proyecto.nombre, indicador.proyecto.id),
                        ('Indicador', indicador.nombre, indicador.id)
                    ]
                })

        elif entity_type == 'proyecto':
            proyectos = Proyecto.query.join(Programa).join(Componente).join(LineaEstrategica).filter(
                LineaEstrategica.plan_id == plan_id
            ).all()

            for proyecto in proyectos:
                entities.append({
                    'id': proyecto.id,
                    'name': proyecto.nombre,
                    'hierarchy': [
                        ('Línea Estratégica', proyecto.programa.componente.linea_estrategica.nombre, proyecto.programa.componente.linea_estrategica.id),
                        ('Componente', proyecto.programa.componente.nombre, proyecto.programa.componente.id),
                        ('Programa', proyecto.programa.nombre, proyecto.programa.id),
                        ('Proyecto', proyecto.nombre, proyecto.id)
                    ]
                })

        elif entity_type == 'programa':
            programas = Programa.query.join(Componente).join(LineaEstrategica).filter(
                LineaEstrategica.plan_id == plan_id
            ).all()

            for programa in programas:
                entities.append({
                    'id': programa.id,
                    'name': f"{programa.cod_programa} - {programa.nombre}",
                    'hierarchy': [
                        ('Línea Estratégica', programa.componente.linea_estrategica.nombre, programa.componente.linea_estrategica.id),
                        ('Componente', programa.componente.nombre, programa.componente.id),
                        ('Programa', programa.nombre, programa.id)
                    ]
                })

        elif entity_type == 'componente':
            componentes = Componente.query.join(LineaEstrategica).filter(
                LineaEstrategica.plan_id == plan_id
            ).all()

            for componente in componentes:
                entities.append({
                    'id': componente.id,
                    'name': f"{componente.cod_componente} - {componente.nombre}",
                    'hierarchy': [
                        ('Línea Estratégica', componente.linea_estrategica.nombre, componente.linea_estrategica.id),
                        ('Componente', componente.nombre, componente.id)
                    ]
                })

        elif entity_type == 'linea':
            lineas = LineaEstrategica.query.filter_by(plan_id=plan_id).all()

            for linea in lineas:
                entities.append({
                    'id': linea.id,
                    'name': f"{linea.cod_linea} - {linea.nombre}",
                    'hierarchy': [
                        ('Línea Estratégica', linea.nombre, linea.id)
                    ]
                })

        return jsonify(entities)

    except Exception as e:
        print(f"Error obteniendo entidades: {e!s}")
        return jsonify([]), 500

@admin_bp.route('/api/row-permissions', methods=['POST'])
@login_required
def create_row_permission_api():
    """Crear un nuevo permiso de fila (API endpoint)"""
    try:
        # Verificar que hay un plan activo
        from app.models import PlanDesarrollo
        active_plan = PlanDesarrollo.visibles_para(current_user).filter(PlanDesarrollo.estado == 'activo').first()

        if not active_plan:
            return jsonify({
                'success': False,
                'message': 'No hay un plan de desarrollo activo.'
            }), 400

        # Obtener datos del formulario
        user_id = request.form.get('user_id', type=int)
        entity_type = request.form.get('entity_type')
        entity_id = request.form.get('entity_id', type=int)
        can_view = request.form.get('can_view') == 'on'
        can_edit = request.form.get('can_edit') == 'on'
        description = request.form.get('description', '')

        # Validaciones
        if not user_id or not entity_type or not entity_id:
            return jsonify({
                'success': False,
                'message': 'Todos los campos obligatorios deben ser completados.'
            }), 400

        if not can_view and not can_edit:
            return jsonify({
                'success': False,
                'message': 'Debe seleccionar al menos un permiso (ver o editar).'
            }), 400

        # Verificar que el usuario existe
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'Usuario no encontrado.'
            }), 404

        # Crear el permiso según el tipo de entidad
        permission = None
        if entity_type == 'indicador':
            indicador = db.session.get(IndicadorProducto, entity_id)
            if not indicador:
                return jsonify({
                    'success': False,
                    'message': 'Indicador no encontrado.'
                }), 404
            permission = RowPermission(
                user_id=user_id,
                plan_id=active_plan.id,
                indicador_id=entity_id,
                can_view=can_view,
                can_edit=can_edit,
                description=description,
                assigned_by=current_user.id
            )
        elif entity_type == 'proyecto':
            proyecto = db.session.get(Proyecto, entity_id)
            if not proyecto:
                return jsonify({
                    'success': False,
                    'message': 'Proyecto no encontrado.'
                }), 404
            permission = RowPermission(
                user_id=user_id,
                plan_id=active_plan.id,
                proyecto_id=entity_id,
                can_view=can_view,
                can_edit=can_edit,
                description=description,
                assigned_by=current_user.id
            )
        elif entity_type == 'programa':
            programa = db.session.get(Programa, entity_id)
            if not programa:
                return jsonify({
                    'success': False,
                    'message': 'Programa no encontrado.'
                }), 404
            permission = RowPermission(
                user_id=user_id,
                plan_id=active_plan.id,
                programa_id=entity_id,
                can_view=can_view,
                can_edit=can_edit,
                description=description,
                assigned_by=current_user.id
            )
        elif entity_type == 'componente':
            componente = db.session.get(Componente, entity_id)
            if not componente:
                return jsonify({
                    'success': False,
                    'message': 'Componente no encontrado.'
                }), 404
            permission = RowPermission(
                user_id=user_id,
                plan_id=active_plan.id,
                componente_id=entity_id,
                can_view=can_view,
                can_edit=can_edit,
                description=description,
                assigned_by=current_user.id
            )
        elif entity_type == 'linea':
            linea = db.session.get(LineaEstrategica, entity_id)
            if not linea:
                return jsonify({
                    'success': False,
                    'message': 'Línea estratégica no encontrada.'
                }), 404
            permission = RowPermission(
                user_id=user_id,
                plan_id=active_plan.id,
                linea_estrategica_id=entity_id,
                can_view=can_view,
                can_edit=can_edit,
                description=description,
                assigned_by=current_user.id
            )
        else:
            return jsonify({
                'success': False,
                'message': 'Tipo de entidad no válido.'
            }), 400

        # Verificar que no exista un permiso duplicado
        existing_permission = RowPermission.query.filter_by(
            user_id=user_id,
            plan_id=active_plan.id,
            indicador_id=permission.indicador_id,
            proyecto_id=permission.proyecto_id,
            programa_id=permission.programa_id,
            componente_id=permission.componente_id,
            linea_estrategica_id=permission.linea_estrategica_id
        ).first()

        if existing_permission:
            return jsonify({
                'success': False,
                'message': 'Ya existe un permiso para este usuario y entidad.'
            }), 400

        # Guardar el permiso
        db.session.add(permission)
        db.session.commit()

        # Registrar en el log de actividad
        ActivityLog.log_activity(
            'create_row_permission',
            f'Creado permiso de fila para {user.get_full_name()}',
            request.remote_addr,
            request.headers.get('User-Agent')
        )

        return jsonify({
            'success': True,
            'message': 'Permiso asignado exitosamente.',
            'permission_id': permission.id
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error creando permiso de fila: {e!s}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor. Inténtalo de nuevo.'
        }), 500

@admin_bp.route('/api/row-permissions/<int:permission_id>', methods=['GET', 'PATCH'])
@login_required
def get_or_edit_row_permission(permission_id):
    """Obtener o editar un permiso de fila existente"""
    try:
        permission = db.session.get(RowPermission, permission_id)
        if not permission:
            return jsonify({
                'success': False,
                'message': 'Permiso no encontrado.'
            }), 404

        # Verificar que el permiso pertenece al plan del usuario actual
        plan = (PlanDesarrollo.visibles_para(current_user)
                .filter(PlanDesarrollo.id == permission.plan_id).first())

        if not plan:
            return jsonify({
                'success': False,
                'message': 'No tienes permisos para acceder a este permiso.'
            }), 403

        # Manejar solicitud GET (obtener datos para edición)
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'user_id': permission.user_id,
                'plan_id': permission.plan_id,
                'indicador_id': permission.indicador_id,
                'proyecto_id': permission.proyecto_id,
                'programa_id': permission.programa_id,
                'componente_id': permission.componente_id,
                'linea_estrategica_id': permission.linea_estrategica_id,
                'can_view': permission.can_view,
                'can_edit': permission.can_edit,
                'description': permission.description,
                'permission_scope': permission.permission_scope,
                'is_active': permission.is_active
            })

        # Manejar solicitud PATCH (actualizar permiso)
        elif request.method == 'PATCH':
            # Actualizar permisos
            permission.can_view = request.form.get('can_view') == 'on'
            permission.can_edit = request.form.get('can_edit') == 'on'
            permission.description = request.form.get('description', '')
            permission.updated_at = ahora_utc()

            if not permission.can_view and not permission.can_edit:
                return jsonify({
                    'success': False,
                    'message': 'Debe seleccionar al menos un permiso (ver o editar).'
                }), 400

            db.session.commit()

            # Registrar en el log de actividad
            ActivityLog.log_activity(
                'edit_row_permission',
                f'Editado permiso de fila para {permission.user.get_full_name()}',
                request.remote_addr,
                request.headers.get('User-Agent')
            )

            return jsonify({
                'success': True,
                'message': 'Permiso actualizado exitosamente.'
            })

    except Exception as e:
        db.session.rollback()
        print(f"Error procesando permiso de fila: {e!s}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor. Inténtalo de nuevo.'
        }), 500

@admin_bp.route('/api/row-permissions/<int:permission_id>', methods=['DELETE'])
@login_required
def delete_row_permission(permission_id):
    """Eliminar un permiso de fila"""
    try:
        permission = db.session.get(RowPermission, permission_id)
        if not permission:
            return jsonify({
                'success': False,
                'message': 'Permiso no encontrado.'
            }), 404

        # Verificar que el permiso pertenece al plan del usuario actual
        from app.models import PlanDesarrollo
        plan = (PlanDesarrollo.visibles_para(current_user)
                .filter(PlanDesarrollo.id == permission.plan_id).first())

        if not plan:
            return jsonify({
                'success': False,
                'message': 'No tienes permisos para eliminar este permiso.'
            }), 403

        # Marcar como inactivo (no eliminar físicamente)
        permission.is_active = False
        permission.updated_at = ahora_utc()
        db.session.commit()

        # Registrar en el log de actividad
        ActivityLog.log_activity(
            'delete_row_permission',
            f'Eliminado permiso de fila para {permission.user.get_full_name()}',
            request.remote_addr,
            request.headers.get('User-Agent')
        )

        return jsonify({
            'success': True,
            'message': 'Permiso eliminado exitosamente.'
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error eliminando permiso de fila: {e!s}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor. Inténtalo de nuevo.'
        }), 500
