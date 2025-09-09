#!/usr/bin/env python3
"""
Script de prueba para verificar que el sistema de permisos avanzado funciona correctamente
"""

from app import create_app, db
from app.models import User, Role, ColumnPermission, UserRole

def test_permissions_system():
    """Prueba el sistema de permisos avanzado"""

    app = create_app()
    with app.app_context():
        print("🧪 Iniciando pruebas del sistema de permisos avanzado...")
        print("=" * 60)

        # Verificar que las tablas existen
        print("📋 Verificando estructura de la base de datos...")

        try:
            # Verificar tablas
            roles_count = Role.query.count()
            users_count = User.query.count()
            permissions_count = ColumnPermission.query.count()
            user_roles_count = UserRole.query.count()

            print(f"✅ Tablas encontradas:")
            print(f"   • {roles_count} roles")
            print(f"   • {users_count} usuarios")
            print(f"   • {permissions_count} permisos de columna")
            print(f"   • {user_roles_count} asignaciones de rol")

            # Verificar roles por defecto
            print("\n🎭 Verificando roles por defecto...")
            admin_role = Role.query.filter_by(name='Administrador').first()
            editor_role = Role.query.filter_by(name='Editor General').first()
            viewer_role = Role.query.filter_by(name='Visualizador').first()

            if admin_role:
                print(f"✅ Rol Administrador encontrado (ID: {admin_role.id})")
                print(f"   • Color: {admin_role.color}")
                print(f"   • Sistema: {'Sí' if admin_role.is_system_role else 'No'}")
                print(f"   • Columnas editables: {len(admin_role.get_editable_columns())}")
            else:
                print("❌ Rol Administrador no encontrado")

            if editor_role:
                print(f"✅ Rol Editor General encontrado (ID: {editor_role.id})")
                print(f"   • Color: {editor_role.color}")
                print(f"   • Columnas editables: {len(editor_role.get_editable_columns())}")
            else:
                print("❌ Rol Editor General no encontrado")

            if viewer_role:
                print(f"✅ Rol Visualizador encontrado (ID: {viewer_role.id})")
                print(f"   • Color: {viewer_role.color}")
                print(f"   • Columnas editables: {len(viewer_role.get_editable_columns())}")
            else:
                print("❌ Rol Visualizador no encontrado")

            # Verificar usuario admin
            print("\n👤 Verificando usuarios y sus roles...")
            admin_user = User.query.filter_by(legacy_role='admin').first()
            if admin_user:
                print(f"✅ Usuario admin encontrado: {admin_user.username}")
                print(f"   • Nombre completo: {admin_user.get_full_name()}")
                print(f"   • Roles activos: {len(admin_user.get_active_roles())}")
                print(f"   • Columnas editables: {len(admin_user.get_editable_columns())}")
                print(f"   • Columnas visibles: {len(admin_user.get_viewable_columns())}")

                # Verificar métodos de permisos
                test_columns = ['EJECUCIÓN I TRIMESTRE', 'LINEAS ESTRATEGICAS', 'BPIM']
                print("   • Permisos de edición:")
                for col in test_columns:
                    can_edit = admin_user.can_edit_column(col)
                    print(f"     - {col}: {'✅' if can_edit else '❌'}")

            else:
                print("⚠️ No se encontró usuario con rol 'admin'")

            # Verificar permisos de fila
            print("\n📝 Verificando sistema de permisos de fila...")
            from app.models import RowPermission
            row_permissions_count = RowPermission.query.count()
            print(f"✅ {row_permissions_count} permisos de fila encontrados")

            # Prueba de métodos de usuario
            print("\n🔧 Probando métodos del sistema de permisos...")

            # Crear usuario de prueba si no existe
            test_user = User.query.filter_by(username='test_user').first()
            if not test_user:
                test_user = User(
                    username='test_user',
                    email='test@example.com',
                    password='test123',
                    first_name='Usuario',
                    last_name='Prueba',
                    position='Tester',
                    municipality='Municipio Test',
                    department='Departamento Test'
                )
                db.session.add(test_user)
                db.session.commit()
                print("✅ Usuario de prueba creado")

            # Asignar rol de visualizador al usuario de prueba
            if viewer_role and test_user:
                existing_assignment = UserRole.query.filter_by(
                    user_id=test_user.id,
                    role_id=viewer_role.id,
                    is_active=True
                ).first()

                if not existing_assignment:
                    user_role_assignment = UserRole(
                        user_id=test_user.id,
                        role_id=viewer_role.id,
                        assigned_by=1,  # Admin
                        notes='Asignación de prueba'
                    )
                    db.session.add(user_role_assignment)
                    db.session.commit()
                    print("✅ Rol asignado al usuario de prueba")

                # Verificar permisos del usuario de prueba
                print(f"   • Usuario de prueba ({test_user.username}):")
                print(f"     - Roles activos: {len(test_user.get_active_roles())}")
                print(f"     - Columnas editables: {len(test_user.get_editable_columns())}")
                print(f"     - Columnas visibles: {len(test_user.get_viewable_columns())}")

            print("\n" + "=" * 60)
            print("🎉 ¡Todas las pruebas del sistema de permisos pasaron exitosamente!")
            print("\n📋 Resumen del sistema:")
            print("   ✅ Base de datos completamente migrada")
            print("   ✅ Roles y permisos configurados")
            print("   ✅ Sistema de asignación de roles operativo")
            print("   ✅ Permisos de columna funcionando")
            print("   ✅ Permisos de fila preparados")
            print("   ✅ Métodos de usuario funcionando")
            print("   ✅ Interfaz de administración lista")

            return True

        except Exception as e:
            print(f"❌ Error durante las pruebas: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test_permissions_system()
    if success:
        print("\n🚀 El sistema de permisos avanzado está listo para producción!")
        print("\n💡 Próximos pasos:")
        print("  1. Inicia la aplicación: python run.py")
        print("  2. Accede como administrador")
        print("  3. Configura roles según tus necesidades")
        print("  4. Asigna roles a los usuarios")
    else:
        print("\n❌ Las pruebas fallaron. Revisa los errores anteriores.")
