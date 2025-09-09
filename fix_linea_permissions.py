#!/usr/bin/env python3
"""
Script para corregir permisos de 'CÓD LINEA' para el rol Editor General
"""

from app import create_app, db
from app.models import Role, ColumnPermission

def fix_linea_permissions():
    """Corrige los permisos para 'CÓD LINEA'"""

    app = create_app()

    with app.app_context():
        print("🔧 Corrigiendo permisos para 'CÓD LINEA'...")

        # Buscar el rol Editor General
        editor_role = Role.query.filter_by(name='Editor General').first()
        if not editor_role:
            print("❌ No se encontró el rol 'Editor General'")
            return

        # Buscar el permiso para 'CÓD LINEA'
        linea_permission = ColumnPermission.query.filter_by(
            role_id=editor_role.id,
            column_name='CÓD LINEA'
        ).first()

        if not linea_permission:
            print("❌ No se encontró el permiso para 'CÓD LINEA'")
            return

        # Habilitar edición para 'CÓD LINEA'
        linea_permission.can_edit = True
        db.session.commit()

        print("✅ Permiso de edición para 'CÓD LINEA' habilitado")
        print(f"   Rol: {editor_role.name}")
        print(f"   Columna: {linea_permission.column_name}")
        print(f"   Puede editar: {linea_permission.can_edit}")
        print(f"   Puede ver: {linea_permission.can_view}")

if __name__ == '__main__':
    fix_linea_permissions()
