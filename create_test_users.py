#!/usr/bin/env python3
"""
Script para crear usuarios de prueba en el sistema de permisos avanzado
"""

from app import create_app, db
from app.models import User, Role, UserRole, RowPermission, IndicadorProducto

def create_test_users():
    """Crea usuarios de prueba para el sistema"""

    app = create_app()
    with app.app_context():
        print("🧪 Creando usuarios de prueba para el sistema...")
        print("=" * 60)

        try:
            # Crear usuario de Editor de Ejecución
            print("👤 Creando usuario Editor de Ejecución...")
            editor_user = User.query.filter_by(username='editor_ejecucion').first()
            if not editor_user:
                editor_user = User(
                    username='editor_ejecucion',
                    email='editor.ejecucion@alcaldia.gob.sv',
                    password='editor123',
                    first_name='Carlos',
                    last_name='Martínez',
                    position='Especialista en Ejecución',
                    municipality='Municipio Central',
                    department='San Salvador',
                    municipality_code='MC-002'
                )
                db.session.add(editor_user)
                db.session.commit()
                print(f"✅ Usuario Editor de Ejecución creado: {editor_user.username}")

                # Asignar rol de Editor de Ejecución
                editor_role = Role.query.filter_by(name='Editor de Ejecución').first()
                if editor_role:
                    user_role_assignment = UserRole(
                        user_id=editor_user.id,
                        role_id=editor_role.id,
                        assigned_by=1,  # Admin
                        notes='Usuario de prueba para edición de ejecución'
                    )
                    db.session.add(user_role_assignment)
                    db.session.commit()
                    print(f"✅ Rol asignado: {editor_role.name}")
                else:
                    print("⚠️ Rol 'Editor de Ejecución' no encontrado")

            # Crear usuario de Visualizador
            print("👤 Creando usuario Visualizador...")
            viewer_user = User.query.filter_by(username='visualizador').first()
            if not viewer_user:
                viewer_user = User(
                    username='visualizador',
                    email='visualizador@alcaldia.gob.sv',
                    password='viewer123',
                    first_name='Ana',
                    last_name='López',
                    position='Analista',
                    municipality='Municipio Norte',
                    department='San Salvador',
                    municipality_code='MN-001'
                )
                db.session.add(viewer_user)
                db.session.commit()
                print(f"✅ Usuario Visualizador creado: {viewer_user.username}")

                # Asignar rol de Visualizador
                viewer_role = Role.query.filter_by(name='Visualizador').first()
                if viewer_role:
                    user_role_assignment = UserRole(
                        user_id=viewer_user.id,
                        role_id=viewer_role.id,
                        assigned_by=1,  # Admin
                        notes='Usuario de prueba con permisos de solo lectura'
                    )
                    db.session.add(user_role_assignment)
                    db.session.commit()
                    print(f"✅ Rol asignado: {viewer_role.name}")
                else:
                    print("⚠️ Rol 'Visualizador' no encontrado")

            # Crear usuario con permiso de fila específico
            print("👤 Creando usuario con permiso de fila específico...")
            specific_user = User.query.filter_by(username='usuario_especifico').first()
            if not specific_user:
                specific_user = User(
                    username='usuario_especifico',
                    email='usuario.especifico@alcaldia.gob.sv',
                    password='especifico123',
                    first_name='Roberto',
                    last_name='García',
                    position='Coordinador de Proyecto',
                    municipality='Municipio Sur',
                    department='La Libertad',
                    municipality_code='MS-001'
                )
                db.session.add(specific_user)
                db.session.commit()
                print(f"✅ Usuario específico creado: {specific_user.username}")

                # Asignar rol de Visualizador inicialmente
                viewer_role = Role.query.filter_by(name='Visualizador').first()
                if viewer_role:
                    user_role_assignment = UserRole(
                        user_id=specific_user.id,
                        role_id=viewer_role.id,
                        assigned_by=1,
                        notes='Usuario con permiso específico de fila'
                    )
                    db.session.add(user_role_assignment)
                    db.session.commit()

                    # Buscar un indicador existente para asignar permiso específico
                    indicador = IndicadorProducto.query.first()
                    if indicador:
                        row_permission = RowPermission(
                            user_id=specific_user.id,
                            indicador_id=indicador.id,
                            can_edit=True,
                            search_term='permiso específico',
                            assigned_by=1
                        )
                        db.session.add(row_permission)
                        db.session.commit()
                        print(f"✅ Permiso de fila específico asignado para indicador: {indicador.nombre}")
                    else:
                        print("⚠️ No se encontró ningún indicador para asignar permiso específico")

            print("\n" + "=" * 60)
            print("🎉 ¡Usuarios de prueba creados exitosamente!")
            print("\n📋 Cuentas de usuario disponibles para pruebas:")

            print("\n   👑 Administrador (Control Total):")
            print("      • Usuario: admin")
            print("      • Email: admin@alcaldia.gob.sv")
            print("      • Permisos: Control total del sistema")

            if editor_user:
                print("\n   📊 Editor de Ejecución:")
                print("      • Usuario: editor_ejecucion")
                print("      • Email: editor.ejecucion@alcaldia.gob.sv")
                print("      • Contraseña: editor123")
                print("      • Permisos: Solo columnas de ejecución y cumplimiento")

            if viewer_user:
                print("\n   👁️ Visualizador:")
                print("      • Usuario: visualizador")
                print("      • Email: visualizador@alcaldia.gob.sv")
                print("      • Contraseña: viewer123")
                print("      • Permisos: Solo lectura de todas las columnas")

            if specific_user:
                print("\n   🎯 Usuario con Permiso Específico:")
                print("      • Usuario: usuario_especifico")
                print("      • Email: usuario.especifico@alcaldia.gob.sv")
                print("      • Contraseña: especifico123")
                print("      • Permisos: Solo lectura + edición de fila específica")

            print("\n💡 Para probar el sistema:")
            print("   1. Inicia sesión con cada usuario para ver las diferencias")
            print("   2. Ve a la Vista Excel y compara los permisos")
            print("   3. Prueba editar diferentes columnas con cada usuario")
            print("   4. Accede al Panel de Administración como admin")

            print("\n🔗 URL del sistema:")
            print("   http://localhost:5000")

            return True

        except Exception as e:
            print(f"❌ Error creando usuarios de prueba: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = create_test_users()
    if success:
        print("\n🎯 ¡Sistema listo para pruebas completas con múltiples usuarios!")
    else:
        print("\n❌ Falló la creación de usuarios de prueba.")
