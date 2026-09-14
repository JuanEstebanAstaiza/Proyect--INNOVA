#!/usr/bin/env python3
"""
Sistema de archivos de auditoría para justificaciones de edición
Crea archivos de texto organizados por usuario con información de cambios
"""
import os
from datetime import datetime

from flask import current_app

from app import db
from app.models import EditJustification, IndicadorProducto, PlanDesarrollo, User


def create_user_audit_directory(user_id):
    """Crear directorio de auditoría para un usuario"""
    base_path = current_app.config.get('AUDIT_FILES_PATH', 'audit_files')
    user_path = os.path.join(base_path, f'user_{user_id}')

    # Crear directorio si no existe
    os.makedirs(user_path, exist_ok=True)
    return user_path

def generate_change_filename(edit_justification):
    """Generar nombre de archivo único para el cambio"""
    timestamp = edit_justification.created_at.strftime('%Y%m%d_%H%M%S')
    plan_id = edit_justification.plan_id
    column = edit_justification.column_name or 'unknown'
    return f"{timestamp}_plan_{plan_id}_{column}.pdf"

def create_audit_file(edit_justification):
    """Crear archivo de auditoría en PDF con marca de agua"""

    try:
        from audit_pdf_generator import create_audit_pdf
        pdf_path = create_audit_pdf(edit_justification)
        return pdf_path
    except Exception as e:
        print(f"[ERROR] Error creando PDF de auditoría: {e}")
        # Fallback: crear archivo TXT básico si falla el PDF
        return create_audit_file_txt_fallback(edit_justification)

def create_audit_file_txt_fallback(edit_justification):
    """Fallback: Crear archivo de auditoría en TXT si falla el PDF"""

    # Obtener información del usuario
    user = db.session.get(User, edit_justification.user_id)
    plan = db.session.get(PlanDesarrollo, edit_justification.plan_id)

    # Crear directorio del usuario
    user_dir = create_user_audit_directory(edit_justification.user_id)

    # Generar nombre del archivo
    filename = generate_change_filename(edit_justification)
    file_path = os.path.join(user_dir, filename)

    # Preparar contenido del archivo
    content = f"""AUDITORÍA DE CAMBIO - PLAN DE DESARROLLO
{'='*50}

INFORMACIÓN GENERAL
{'='*20}
Fecha y Hora: {edit_justification.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Usuario: {user.username if user else 'N/A'} ({user.email if user else 'N/A'})
Plan: {plan.titulo if plan else 'N/A'} (ID: {edit_justification.plan_id})

DETALLES DEL CAMBIO
{'='*20}
Columna Editada: {edit_justification.get_column_display_name()}
Valor Anterior: {edit_justification.old_value or 'N/A'}
Valor Nuevo: {edit_justification.new_value}

JUSTIFICACIÓN
{'='*15}
{edit_justification.justification}

ARCHIVOS ANEXADOS
{'='*18}
"""

    # Agregar información de archivos anexados
    if edit_justification.support_file_path and os.path.exists(edit_justification.support_file_path):
        filename = os.path.basename(edit_justification.support_file_path)
        file_size = os.path.getsize(edit_justification.support_file_path)
        content += f"Archivo: {filename}\n"
        content += f"Tamaño: {file_size} bytes\n"
        content += f"Ubicación: {edit_justification.support_file_path}\n"
        content += f"URL de descarga: {edit_justification.get_support_file_url() or 'N/A'}\n"
    else:
        content += "No se anexaron archivos de soporte.\n"

    # Agregar información adicional si hay indicador
    if edit_justification.indicador_id:
        indicador = db.session.get(IndicadorProducto, edit_justification.indicador_id)
        if indicador:
            content += f"\n\nINFORMACIÓN DEL INDICADOR\n{'='*25}\n"
            content += f"Indicador: {indicador.nombre}\n"
            content += f"Código: {indicador.cod_indicador}\n"
            content += f"Proyecto: {indicador.proyecto.nombre if indicador.proyecto else 'N/A'}\n"
            content += f"Programa: {indicador.proyecto.programa.nombre if indicador.proyecto and indicador.proyecto.programa else 'N/A'}\n"

    content += f"\n\n{'='*50}\nFIN DEL REGISTRO DE AUDITORÍA\n"

    # Crear el archivo
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[OK] Archivo de auditoría TXT (fallback) creado: {file_path}")
        return file_path

    except Exception as e:
        print(f"[ERROR] Error creando archivo de auditoría TXT: {e}")
        return None

def create_user_audit_summary(user_id):
    """Crear resumen de auditoría en PDF para un usuario"""

    try:
        from audit_pdf_generator import create_user_audit_summary_pdf
        pdf_path = create_user_audit_summary_pdf(user_id)
        return pdf_path
    except Exception as e:
        print(f"[ERROR] Error creando PDF resumen de auditoría: {e}")
        # Fallback: crear archivo TXT básico si falla el PDF
        return create_user_audit_summary_txt_fallback(user_id)

def create_user_audit_summary_txt_fallback(user_id):
    """Fallback: Crear resumen de auditoría en TXT si falla el PDF"""
    user_dir = create_user_audit_directory(user_id)

    # Obtener todos los cambios del usuario
    changes = EditJustification.query.filter_by(user_id=user_id).order_by(EditJustification.created_at.desc()).all()

    if not changes:
        print(f"No hay cambios registrados para el usuario {user_id}")
        return None

    # Crear archivo de resumen
    summary_path = os.path.join(user_dir, 'resumen_auditoria.txt')

    content = f"""RESUMEN DE AUDITORÍA - USUARIO {user_id}
{'='*50}

Total de cambios registrados: {len(changes)}
Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

LISTADO DE CAMBIOS
{'='*20}
"""

    for i, change in enumerate(changes, 1):
        content += f"\n{i}. {change.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"   Columna: {change.get_column_display_name()}\n"
        content += f"   Cambio: {change.old_value or 'N/A'} → {change.new_value}\n"
        content += f"   Archivo: {generate_change_filename(change)}\n"

    content += f"\n\n{'='*50}\nFIN DEL RESUMEN\n"

    try:
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[OK] Resumen de auditoría TXT (fallback) creado: {summary_path}")
        return summary_path

    except Exception as e:
        print(f"[ERROR] Error creando resumen de auditoría TXT: {e}")
        return None

def get_user_audit_files(user_id):
    """Obtener lista de archivos de auditoría de un usuario"""
    user_dir = create_user_audit_directory(user_id)

    if not os.path.exists(user_dir):
        return []

    files = []
    for filename in os.listdir(user_dir):
        # Buscar archivos PDF y también TXT (por compatibilidad con archivos existentes)
        if filename.endswith('.pdf') or filename.endswith('.txt'):
            file_path = os.path.join(user_dir, filename)
            file_info = {
                'filename': filename,
                'path': file_path,
                'size': os.path.getsize(file_path),
                'modified': datetime.fromtimestamp(os.path.getmtime(file_path)),
                'type': 'PDF' if filename.endswith('.pdf') else 'TXT'
            }
            files.append(file_info)

    return sorted(files, key=lambda x: x['modified'], reverse=True)

def setup_audit_system():
    """Configurar el sistema de auditoría"""
    # Crear directorio base si no existe
    base_path = 'audit_files'
    os.makedirs(base_path, exist_ok=True)

    # Crear archivo .gitkeep para que se incluya en el repositorio
    gitkeep_path = os.path.join(base_path, '.gitkeep')
    if not os.path.exists(gitkeep_path):
        with open(gitkeep_path, 'w') as f:
            f.write("# Directorio para archivos de auditoría\n")

    print("[OK] Sistema de auditoría configurado")

if __name__ == "__main__":
    print("Sistema de Archivos de Auditoría")
    setup_audit_system()
