#!/usr/bin/env python3
"""
Vistas para el sistema de auditoría de archivos
"""
from flask import Blueprint, render_template, current_app, send_from_directory, abort
from flask_login import login_required, current_user
from audit_file_system import get_user_audit_files, create_user_audit_summary
import os
from datetime import datetime

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')

@audit_bp.route('/')
@login_required
def audit_dashboard():
    """Panel principal de auditoría - solo lectura para usuarios"""
    from app.models import PlanDesarrollo, EditJustification

    try:
        # Obtener el plan activo
        active_plan = PlanDesarrollo.query.filter_by(estado='activo').first()

        # Obtener archivos de auditoría del usuario
        audit_files = get_user_audit_files(current_user.id)

        # Obtener justificaciones del usuario para el plan activo
        user_changes = []
        if active_plan:
            user_changes = EditJustification.query.filter_by(
                user_id=current_user.id,
                plan_id=active_plan.id
            ).order_by(EditJustification.created_at.desc()).all()

        # Estadísticas
        total_changes = len(user_changes)
        total_files = len(audit_files)
        total_size = sum(file['size'] for file in audit_files) if audit_files else 0

        return render_template('audit/dashboard.html',
                             title='Panel de Auditoría',
                             active_plan=active_plan,
                             audit_files=audit_files,
                             user_changes=user_changes,
                             total_changes=total_changes,
                             total_files=total_files,
                             total_size=total_size)

    except Exception as e:
        current_app.logger.error(f"Error cargando panel de auditoría: {e}")
        return render_template('audit/dashboard.html',
                             title='Panel de Auditoría',
                             active_plan=None,
                             audit_files=[],
                             user_changes=[],
                             error=str(e))

@audit_bp.route('/admin')
@login_required
def admin_audit_dashboard():
    """Panel administrativo de auditoría - vista completa de todos los usuarios"""
    from flask_login import current_user
    from app.models import User, PlanDesarrollo, EditJustification

    # Verificar que el usuario sea administrador
    if not current_user.is_admin():
        from flask import flash, redirect, url_for
        flash('No tienes permisos para acceder al panel administrativo de auditoría.', 'error')
        return redirect(url_for('audit.audit_dashboard'))

    try:
        # Obtener todos los usuarios con archivos de auditoría
        users_with_audit = []
        all_users = User.query.all()

        total_files = 0
        total_size = 0
        total_changes = 0

        for user in all_users:
            user_audit_files = get_user_audit_files(user.id)

            if user_audit_files:  # Solo incluir usuarios que tengan archivos
                # Obtener cambios del usuario
                user_changes = EditJustification.query.filter_by(user_id=user.id).all()

                # Calcular estadísticas del usuario
                user_size = sum(file['size'] for file in user_audit_files)
                user_files = len(user_audit_files)

                user_info = {
                    'user': user,
                    'audit_files': user_audit_files,
                    'total_changes': len(user_changes),
                    'total_files': user_files,
                    'total_size': user_size,
                    'last_activity': max((f['modified'] for f in user_audit_files), default=None) if user_audit_files else None
                }

                users_with_audit.append(user_info)

                # Sumar a totales globales
                total_files += user_files
                total_size += user_size
                total_changes += len(user_changes)

        # Ordenar usuarios por última actividad (más reciente primero)
        users_with_audit.sort(key=lambda x: x['last_activity'] or datetime.min, reverse=True)

        # Obtener plan activo
        active_plan = PlanDesarrollo.query.filter_by(estado='activo').first()

        return render_template('audit/admin_dashboard.html',
                             title='Panel Administrativo de Auditoría',
                             active_plan=active_plan,
                             users_with_audit=users_with_audit,
                             total_users=len(users_with_audit),
                             total_files=total_files,
                             total_size=total_size,
                             total_changes=total_changes)

    except Exception as e:
        current_app.logger.error(f"Error cargando panel administrativo de auditoría: {e}")
        return render_template('audit/admin_dashboard.html',
                             title='Panel Administrativo de Auditoría',
                             active_plan=None,
                             users_with_audit=[],
                             error=str(e))

@audit_bp.route('/files')
@login_required
def list_audit_files():
    """Mostrar lista de archivos de auditoría del usuario actual (modo administración)"""
    try:
        audit_files = get_user_audit_files(current_user.id)

        # Crear resumen si no existe
        summary_path = create_user_audit_summary(current_user.id)

        return render_template('audit/files.html',
                             title='Mis Archivos de Auditoría',
                             audit_files=audit_files,
                             summary_exists=summary_path is not None)

    except Exception as e:
        current_app.logger.error(f"Error listando archivos de auditoría: {e}")
        return render_template('audit/files.html',
                             title='Mis Archivos de Auditoría',
                             audit_files=[],
                             error=str(e))

@audit_bp.route('/files/<filename>')
@login_required
def download_audit_file(filename):
    """Descargar archivo de auditoría específico del usuario actual"""
    try:
        user_dir = f'user_{current_user.id}'
        base_path = current_app.config.get('AUDIT_FILES_PATH', 'audit_files')
        directory = os.path.join(base_path, user_dir)
        file_path = os.path.join(directory, filename)

        # Verificar que el archivo pertenece al usuario actual
        if not os.path.exists(file_path):
            from flask import flash, redirect, url_for
            flash('El archivo solicitado no existe o no tienes permisos para descargarlo.', 'error')
            return redirect(url_for('audit.audit_dashboard'))

        # Verificar que el directorio del usuario existe
        if not os.path.exists(directory):
            from flask import flash, redirect, url_for
            flash('No se encontraron archivos de auditoría para tu cuenta.', 'warning')
            return redirect(url_for('audit.audit_dashboard'))

        return send_from_directory(directory, filename, as_attachment=True)

    except Exception as e:
        current_app.logger.error(f"Error descargando archivo de auditoría: {e}")
        from flask import flash, redirect, url_for
        flash('Error al descargar el archivo. Inténtalo de nuevo.', 'error')
        return redirect(url_for('audit.audit_dashboard'))

@audit_bp.route('/admin/files/<int:user_id>/<filename>')
@login_required
def download_admin_audit_file(user_id, filename):
    """Descargar archivo de auditoría de cualquier usuario (solo administradores)"""
    # Verificar que el usuario actual sea administrador
    if not current_user.is_admin():
        from flask import flash, redirect, url_for
        flash('No tienes permisos para acceder a archivos de otros usuarios.', 'error')
        return redirect(url_for('audit.admin_audit_dashboard'))

    try:
        user_dir = f'user_{user_id}'
        base_path = current_app.config.get('AUDIT_FILES_PATH', 'audit_files')
        directory = os.path.join(base_path, user_dir)
        file_path = os.path.join(directory, filename)

        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            from flask import flash, redirect, url_for
            flash(f'El archivo "{filename}" no existe para el usuario solicitado.', 'error')
            return redirect(url_for('audit.admin_audit_dashboard'))

        # Verificar que el directorio del usuario existe
        if not os.path.exists(directory):
            from flask import flash, redirect, url_for
            flash('No se encontraron archivos de auditoría para este usuario.', 'warning')
            return redirect(url_for('audit.admin_audit_dashboard'))

        return send_from_directory(directory, filename, as_attachment=True)

    except Exception as e:
        current_app.logger.error(f"Error descargando archivo administrativo de auditoría: {e}")
        from flask import flash, redirect, url_for
        flash('Error al descargar el archivo. Inténtalo de nuevo.', 'error')
        return redirect(url_for('audit.admin_audit_dashboard'))

@audit_bp.route('/summary')
@login_required
def download_summary():
    """Descargar resumen de auditoría del usuario"""
    try:
        summary_path = create_user_audit_summary(current_user.id)
        if not summary_path:
            abort(404)

        user_dir = f'user_{current_user.id}'
        base_path = current_app.config.get('AUDIT_FILES_PATH', 'audit_files')
        directory = os.path.join(base_path, user_dir)
        filename = 'resumen_auditoria.txt'

        return send_from_directory(directory, filename, as_attachment=True)

    except Exception as e:
        current_app.logger.error(f"Error descargando resumen de auditoría: {e}")
        abort(500)
