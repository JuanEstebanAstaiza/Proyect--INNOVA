from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from app import db
from app.models import (User, ActivityLog, ActiveSession, Role, ColumnPermission, RowPermission, UserRole,
                       IndicadorProducto, LineaEstrategica, Componente, Programa, Proyecto)

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
    admin_users = User.query.filter_by(role='admin').count()
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
    recent_time = datetime.utcnow() - timedelta(minutes=5)
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
            municipality_code=form.municipality_code.data,
            role=form.role.data
        )

        # Generar contraseña temporal segura
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        temp_password = ''.join(secrets.choice(alphabet) for i in range(12))
        user.password = temp_password

        try:
            db.session.add(user)
            db.session.commit()

            # Log the activity
            ActivityLog.log_activity(
                'create_user',
                f'Creado nuevo usuario: {user.username}',
                request.remote_addr,
                request.headers.get('User-Agent')
            )

            flash(f'Usuario {user.username} creado exitosamente. Contraseña temporal: {temp_password}', 'success')
            return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el usuario. Por favor intenta nuevamente.', 'error')

    return render_template('admin/create_user.html', title='Crear Usuario', form=form)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    """Toggle user active/inactive status"""
    user = User.query.get_or_404(user_id)

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
    user = User.query.get_or_404(user_id)
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
            'timestamp': datetime.utcnow().isoformat()
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

    except Exception as e:
        return '', 500

@admin_bp.route('/api/activity/alert/<int:user_id>', methods=['POST'])
@login_required
def send_inactivity_alert(user_id):
    """Send inactivity alert to a specific user"""
    if not current_user.is_admin():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    try:
        user = User.query.get_or_404(user_id)

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
            'timestamp': datetime.utcnow().isoformat()
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
    role = Role.query.get_or_404(role_id)

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
    role = Role.query.get_or_404(role_id)

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
        active_roles = [ur for ur in user.active_roles if ur.is_active]
        user_roles_data.append({
            'user': user,
            'roles': active_roles,
            'role_names': [ur.role.name for ur in active_roles],
            'role_colors': [ur.role.color for ur in active_roles]
        })

    return render_template('admin/user_roles.html',
                         title='Asignación de Roles',
                         user_roles_data=user_roles_data,
                         roles=roles)

@admin_bp.route('/users/<int:user_id>/assign-role', methods=['POST'])
def assign_role_to_user(user_id):
    """Asignar rol a usuario"""
    user = User.query.get_or_404(user_id)
    role_id = request.form.get('role_id', type=int)

    if not role_id:
        flash('Debe seleccionar un rol.', 'error')
        return redirect(url_for('admin.user_roles'))

    role = Role.query.get_or_404(role_id)

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
    user = User.query.get_or_404(user_id)
    role = Role.query.get_or_404(role_id)

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

@admin_bp.route('/row-permissions')
def row_permissions():
    """Gestión de permisos de fila por usuario"""
    # Obtener usuarios con permisos de fila
    users_with_permissions = db.session.query(User).join(RowPermission).distinct().all()
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

    user = User.query.get_or_404(user_id)
    indicador = IndicadorProducto.query.get_or_404(indicador_id)

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
    permission = RowPermission.query.get_or_404(permission_id)

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
        users_with_roles = db.session.query(User).join(UserRole).filter(
            UserRole.is_active == True,
            User.is_active == True
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
