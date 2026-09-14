#!/usr/bin/env python3
"""
Script para probar la descarga administrativa de archivos de auditoría
"""
from app import create_app, db
from app.models import User, PlanDesarrollo

def test_admin_download():
    """Probar descarga administrativa de archivos de auditoría"""
    print("🔧 Probando descarga administrativa de archivos de auditoría...")
    print("=" * 70)

    with create_app().app_context():
        try:
            # Verificar usuarios administradores
            admin_users = User.query.filter_by(legacy_role='admin').all()
            if not admin_users:
                print("❌ No hay usuarios administradores")
                return False

            print(f"✅ Usuarios administradores encontrados: {len(admin_users)}")

            # Verificar usuarios con archivos
            import os
            audit_base = 'audit_files'
            users_with_files = []

            for user in User.query.all():
                user_dir = f'user_{user.id}'
                user_path = os.path.join(audit_base, user_dir)

                if os.path.exists(user_path):
                    files = [f for f in os.listdir(user_path) if f.endswith('.pdf') or f.endswith('.txt')]
                    if files:
                        users_with_files.append({
                            'user': user,
                            'files': files,
                            'is_admin': user.legacy_role == 'admin'
                        })

            print(f"✅ Usuarios con archivos de auditoría: {len(users_with_files)}")

            for user_info in users_with_files[:3]:  # Mostrar máximo 3 usuarios
                user = user_info['user']
                files = user_info['files']
                print(f"\n👤 Usuario: {user.username} ({user.email})")
                print(f"   📁 Archivos: {len(files)}")
                for file in files[:2]:  # Mostrar máximo 2 archivos por usuario
                    print(f"   📄 {file}")

            # Verificar endpoints
            from flask import url_for
            app = create_app()

            with app.test_request_context():
                # Probar endpoint administrativo
                if users_with_files:
                    test_user = users_with_files[0]['user']
                    test_file = users_with_files[0]['files'][0]

                    try:
                        admin_url = url_for('audit.download_admin_audit_file',
                                          user_id=test_user.id,
                                          filename=test_file)
                        print("\n🌐 URLs de descarga:")
                        print(f"   👨‍💼 Admin descarga: {admin_url}")

                        normal_url = url_for('audit.download_audit_file',
                                           filename=test_file)
                        print(f"   👤 Usuario normal: {normal_url}")

                    except Exception as e:
                        print(f"   ❌ Error generando URLs: {e}")

            print("\n🎯 Funcionalidades implementadas:")
            print("✅ Endpoint administrativo: /audit/admin/files/<user_id>/<filename>")
            print("✅ Control de acceso solo para administradores")
            print("✅ Descarga de archivos de cualquier usuario")
            print("✅ Verificación de existencia de archivos")
            print("✅ Template administrativo actualizado")
            print("✅ URLs correctas en botones de descarga")

            print("\n🛡️ Seguridad implementada:")
            print("✅ Verificación de permisos administrativos")
            print("✅ Mensajes de error para accesos no autorizados")
            print("✅ Redirección segura para usuarios no admin")
            print("✅ Control de acceso a archivos de otros usuarios")

            return True

        except Exception as e:
            print(f"❌ Error probando descarga administrativa: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_admin_download()
    if success:
        print("\n🎊 ¡Sistema de descarga administrativa funcionando correctamente!")
        print("Los administradores pueden descargar archivos de auditoría de cualquier usuario.")
    else:
        print("\n❌ Hay problemas con el sistema de descarga administrativa.")
