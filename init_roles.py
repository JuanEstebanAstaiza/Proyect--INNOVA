#!/usr/bin/env python3
"""
Script para inicializar roles por defecto en el sistema de permisos avanzado
"""

from app import create_app, db
from app.models import Role, ColumnPermission, User, UserRole

def create_default_roles():
    """Crea los roles por defecto del sistema"""

    print("🛠️ Creando roles por defecto...")

    # Rol Administrador - puede hacer todo
    admin_role = Role(
        name='Administrador',
        description='Acceso completo al sistema. Puede gestionar usuarios, roles y editar todos los planes.',
        color='#dc3545',
        is_system_role=True
    )
    db.session.add(admin_role)
    db.session.commit()  # Commit para obtener el ID

    # Configurar permisos para Administrador (todos editables)
    for permission in admin_role.column_permissions:
        permission.can_edit = True
        permission.can_view = True
    db.session.commit()

    # Rol Editor General - puede editar la mayoría de columnas pero no gestión de usuarios
    editor_role = Role(
        name='Editor General',
        description='Puede editar planes de desarrollo pero no gestionar usuarios o roles.',
        color='#28a745',
        is_system_role=True
    )
    db.session.add(editor_role)
    db.session.commit()

    # Configurar permisos para Editor General
    for permission in editor_role.column_permissions:
        column_name = permission.column_name.lower()
        # Los editores pueden editar casi todo menos estructura organizacional
        if 'responsable' not in column_name and not (column_name == 'cód' and 'linea' not in column_name):
            permission.can_edit = True
        # Permitir editar específicamente 'CÓD LINEA'
        if permission.column_name == 'CÓD LINEA':
            permission.can_edit = True
        permission.can_view = True
    db.session.commit()

    # Rol Editor de Ejecución - solo puede editar columnas de ejecución y cumplimiento
    execution_editor = Role(
        name='Editor de Ejecución',
        description='Puede editar datos de ejecución trimestral y porcentajes de cumplimiento.',
        color='#007bff',
        is_system_role=False
    )
    db.session.add(execution_editor)
    db.session.commit()

    # Configurar permisos para Editor de Ejecución
    for permission in execution_editor.column_permissions:
        column_name = permission.column_name.lower()
        if ('ejecución' in column_name or 'cumplimiento' in column_name or
            'población' in column_name or 'observación' in column_name):
            permission.can_edit = True
        permission.can_view = True
    db.session.commit()

    # Rol Visualizador - solo puede ver información
    viewer_role = Role(
        name='Visualizador',
        description='Solo puede ver información del plan de desarrollo.',
        color='#6c757d',
        is_system_role=True
    )
    db.session.add(viewer_role)
    db.session.commit()

    # Configurar permisos para Visualizador (solo lectura)
    for permission in viewer_role.column_permissions:
        permission.can_edit = False
        permission.can_view = True
    db.session.commit()

    # Rol Editor de Metas - puede editar metas e indicadores
    meta_editor = Role(
        name='Editor de Metas',
        description='Puede editar metas, indicadores y datos básicos del plan.',
        color='#ffc107',
        is_system_role=False
    )
    db.session.add(meta_editor)
    db.session.commit()

    # Configurar permisos para Editor de Metas
    for permission in meta_editor.column_permissions:
        column_name = permission.column_name.lower()
        if ('meta' in column_name or 'indicador' in column_name or
            'linea base' in column_name or 'tipo' in column_name or
            'unidad' in column_name or 'sentido' in column_name):
            permission.can_edit = True
        permission.can_view = True
    db.session.commit()

    print("✅ Roles por defecto creados exitosamente!")

    return [admin_role, editor_role, execution_editor, viewer_role, meta_editor]

def assign_default_roles_to_existing_users():
    """Asigna roles por defecto a usuarios existentes basados en su rol legacy"""

    print("🔄 Asignando roles por defecto a usuarios existentes...")

    users = User.query.all()
    admin_role = Role.query.filter_by(name='Administrador').first()
    editor_role = Role.query.filter_by(name='Editor General').first()
    viewer_role = Role.query.filter_by(name='Visualizador').first()

    if not all([admin_role, editor_role, viewer_role]):
        print("❌ Error: No se encontraron los roles por defecto")
        return

    assigned_count = 0

    for user in users:
        # Verificar si ya tiene roles asignados
        existing_roles = UserRole.query.filter_by(user_id=user.id, is_active=True).all()
        if existing_roles:
            continue

        # Asignar rol basado en el rol legacy
        if user.legacy_role == 'admin':
            new_role_assignment = UserRole(
                user_id=user.id,
                role_id=admin_role.id,
                assigned_by=1,  # Asumir que el usuario 1 es el super admin
                notes='Asignación automática desde sistema legacy'
            )
        elif user.legacy_role == 'editor':
            new_role_assignment = UserRole(
                user_id=user.id,
                role_id=editor_role.id,
                assigned_by=1,
                notes='Asignación automática desde sistema legacy'
            )
        else:  # viewer u otros
            new_role_assignment = UserRole(
                user_id=user.id,
                role_id=viewer_role.id,
                assigned_by=1,
                notes='Asignación automática desde sistema legacy'
            )

        db.session.add(new_role_assignment)
        assigned_count += 1

    db.session.commit()
    print(f"✅ Asignados {assigned_count} roles a usuarios existentes")

def main():
    """Función principal"""
    app = create_app()

    with app.app_context():
        print("🚀 Inicializando sistema de roles avanzado...")

        # Crear tablas si no existen
        db.create_all()

        # Crear roles por defecto
        roles = create_default_roles()

        # Asignar roles a usuarios existentes
        assign_default_roles_to_existing_users()

        print("\n📊 Resumen de roles creados:")
        for role in roles:
            editable_count = len(role.get_editable_columns())
            viewable_count = len(role.get_viewable_columns())
            print(f"  • {role.name}: {editable_count} columnas editables, {viewable_count} visibles")

        print("\n🎉 Sistema de roles avanzado inicializado correctamente!")
        print("\n💡 Próximos pasos:")
        print("  1. Accede al panel de administración")
        print("  2. Ve a 'Gestión de Roles' para personalizar permisos")
        print("  3. Asigna roles específicos a los usuarios")
        print("  4. Configura permisos de fila por usuario si es necesario")

if __name__ == '__main__':
    main()
