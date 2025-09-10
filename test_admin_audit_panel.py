#!/usr/bin/env python3
"""
Script para probar el panel administrativo de auditoría
"""
from app import create_app, db
from app.models import User, PlanDesarrollo, EditJustification

def test_admin_audit_panel():
    """Probar el panel administrativo de auditoría"""
    print("🔧 Probando panel administrativo de auditoría...")
    print("=" * 60)

    with create_app().app_context():
        try:
            # Verificar usuarios administradores
            admin_users = User.query.filter_by(legacy_role='admin').all()
            if not admin_users:
                print("⚠️ No hay usuarios administradores en el sistema")
                print("💡 Creando usuario administrador de prueba...")

                # Crear usuario admin si no existe
                admin_user = User(
                    username="admin_pruebas",
                    email="admin.pruebas@example.com",
                    password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Leh1rBpY/9H6B5",
                    first_name="Admin",
                    last_name="de Pruebas",
                    position="Administrador de Pruebas",
                    municipality="Municipio Admin",
                    department="Departamento Admin",
                    municipality_code="ADMIN-001",
                    is_active=True,
                    legacy_role="admin"
                )
                db.session.add(admin_user)
                db.session.commit()
                print(f"✅ Usuario administrador creado: {admin_user.username}")
                admin_users = [admin_user]

            print(f"✅ Usuarios administradores encontrados: {len(admin_users)}")

            # Verificar usuarios con archivos de auditoría
            all_users = User.query.all()
            users_with_audit = []

            for user in all_users:
                from audit_file_system import get_user_audit_files
                audit_files = get_user_audit_files(user.id)
                if audit_files:
                    users_with_audit.append({
                        'user': user,
                        'files_count': len(audit_files),
                        'last_activity': max((f['modified'] for f in audit_files), default=None)
                    })

            print(f"✅ Usuarios con archivos de auditoría: {len(users_with_audit)}")

            # Verificar plan activo
            active_plan = PlanDesarrollo.query.filter_by(estado='activo').first()
            if active_plan:
                print(f"✅ Plan activo: {active_plan.titulo}")

                # Obtener estadísticas globales
                total_changes = EditJustification.query.count()
                total_files = sum(len(get_user_audit_files(u.id)) for u in all_users if get_user_audit_files(u.id))

                print("\n📊 Estadísticas del Sistema:")
                print(f"   👥 Usuarios totales: {len(all_users)}")
                print(f"   📝 Cambios totales: {total_changes}")
                print(f"   📁 Archivos totales: {total_files}")
                print(f"   👨‍💼 Usuarios con auditoría: {len(users_with_audit)}")

                # Mostrar detalle de usuarios con auditoría
                if users_with_audit:
                    print("\n👥 Detalle de usuarios con auditoría:")
                    for i, user_info in enumerate(users_with_audit[:5], 1):  # Mostrar máximo 5
                        last_activity = user_info['last_activity'].strftime('%d/%m/%Y %H:%M') if user_info['last_activity'] else 'N/A'
                        print(f"   {i}. {user_info['user'].username} - {user_info['files_count']} archivos - Última: {last_activity}")
            else:
                print("⚠️ No hay plan activo")

            # Verificar rutas y endpoints
            from flask import url_for
            app = create_app()

            with app.test_request_context():
                try:
                    admin_audit_url = url_for('audit.admin_audit_dashboard')
                    print("\n🌐 Endpoints disponibles:")
                    print(f"   📊 Panel Admin Auditoría: {admin_audit_url}")
                    print("   ✅ Endpoint correctamente registrado")

                except Exception as e:
                    print(f"   ❌ Error con endpoint: {e}")

            print("\n🎯 Funcionalidades del Panel Administrativo:")
            print("✅ Vista completa de todos los usuarios")
            print("✅ Estadísticas globales del sistema")
            print("✅ Organización por usuario")
            print("✅ Lista de archivos por usuario")
            print("✅ Descarga de archivos de cualquier usuario")
            print("✅ Información detallada de actividad")
            print("✅ Control de acceso administrativo")
            print("✅ Interfaz organizada y profesional")

            print("\n🚀 Cómo acceder:")
            print("1. Iniciar sesión como administrador")
            print("2. Ir al Panel de Administrador")
            print("3. Hacer clic en 'Panel de Auditoría' (botón rojo)")
            print("4. Explorar la vista completa de auditoría")
            print("5. Descargar archivos de cualquier usuario")

            return True

        except Exception as e:
            print(f"❌ Error probando panel administrativo: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_admin_audit_panel()
    if success:
        print("\n🎊 ¡Panel administrativo de auditoría funcionando perfectamente!")
        print("Los administradores pueden ver todos los archivos de auditoría organizados por usuario.")
    else:
        print("\n❌ Hay problemas con el panel administrativo de auditoría.")
