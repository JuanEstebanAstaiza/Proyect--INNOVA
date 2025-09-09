#!/usr/bin/env python3
"""
Script para probar el login del usuario admin
"""

from app import create_app
from app.models import User
from flask_login import login_user
from flask import session

def test_admin_login():
    """Prueba el login del usuario admin"""

    app = create_app()
    with app.app_context():
        print("🧪 Probando login del usuario admin...")
        print("=" * 50)

        # Buscar usuario admin
        admin = User.query.filter_by(username='admin').first()

        if not admin:
            print("❌ Usuario 'admin' no encontrado")
            return

        # Verificar contraseña
        password_correct = admin.verify_password('admin123')
        print(f"🔑 Contraseña correcta: {password_correct}")

        if not password_correct:
            print("❌ Contraseña incorrecta")
            return

        # Verificar métodos de permisos
        print(f"👑 Es admin: {admin.is_admin()}")
        print(f"📝 Es editor: {admin.is_editor()}")

        # Verificar roles activos
        print(f"📋 Roles activos: {len(admin.active_roles) if admin.active_roles else 0}")
        if admin.active_roles:
            for ur in admin.active_roles:
                print(f"   - {ur.role.name} (activo: {ur.is_active})")

        # Simular login
        print("\n🔐 Simulando login...")
        try:
            with app.test_request_context():
                login_user(admin, remember=False)
                print("✅ Login exitoso")

                # Verificar que current_user funcione
                from flask_login import current_user
                print(f"👤 Current user: {current_user.username if current_user.is_authenticated else 'No autenticado'}")
                print(f"👑 Current user es admin: {current_user.is_admin() if current_user.is_authenticated else 'N/A'}")

        except Exception as e:
            print(f"❌ Error en login: {str(e)}")

        print("\n🎯 Resultado:")
        if admin.is_admin():
            print("✅ El usuario admin será reconocido correctamente como administrador")
            print("✅ Podrá acceder al panel de administración")
        else:
            print("❌ El usuario admin NO será reconocido como administrador")
            print("❌ NO podrá acceder al panel de administración")

if __name__ == '__main__':
    test_admin_login()
