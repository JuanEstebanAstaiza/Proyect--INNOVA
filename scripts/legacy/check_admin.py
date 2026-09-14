#!/usr/bin/env python3
"""
Script para verificar el estado del usuario admin
"""

from app import create_app, db
from app.models import User, Role, UserRole

def check_admin_status():
    """Verifica el estado del usuario admin"""

    app = create_app()
    with app.app_context():
        print("🔍 Verificando estado del usuario admin...")
        print("=" * 50)

        # Buscar usuario admin
        admin = User.query.filter_by(username='admin').first()

        if not admin:
            print("❌ Usuario 'admin' NO encontrado en la base de datos")
            return

        print("✅ Usuario 'admin' encontrado:")
        print(f"   Username: {admin.username}")
        print(f"   Email: {admin.email}")
        print(f"   Legacy role: {admin.legacy_role}")
        print(f"   Active: {admin.is_active}")

        # Verificar roles activos
        print(f"\n📋 Roles activos: {len(admin.active_roles) if admin.active_roles else 0}")
        if admin.active_roles:
            for i, ur in enumerate(admin.active_roles, 1):
                print(f"   {i}. {ur.role.name} (activo: {ur.is_active})")

        # Verificar método is_admin()
        print(f"\n🔐 Método is_admin(): {admin.is_admin()}")

        # Verificar método is_editor()
        print(f"🔐 Método is_editor(): {admin.is_editor()}")

        # Verificar roles disponibles en el sistema
        print("\n📊 Roles disponibles en el sistema:")
        roles = Role.query.all()
        if roles:
            for role in roles:
                print(f"   - {role.name}: {role.description}")
        else:
            print("   ❌ No hay roles definidos")

        # Verificar si admin tiene algún UserRole asignado
        user_roles = UserRole.query.filter_by(user_id=admin.id).all()
        print(f"\n👤 Asignaciones de roles para admin: {len(user_roles)}")
        for ur in user_roles:
            print(f"   - Rol: {ur.role.name} (activo: {ur.is_active})")

if __name__ == '__main__':
    check_admin_status()
