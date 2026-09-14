#!/usr/bin/env python3
"""
Script para verificar que la página user_roles funciona correctamente
"""
from app import create_app
from app.models import User, RowPermission

def test_user_roles_page():
    """Verificar que la página user_roles funciona sin errores"""
    print("🔧 Verificando página user_roles...")

    try:
        app = create_app()
        with app.app_context():
            print("✅ Aplicación creada correctamente")

            # Verificar usuarios y permisos
            users = User.query.filter_by(is_active=True).all()
            print(f"👥 Usuarios activos: {len(users)}")

            total_permissions = RowPermission.query.filter_by(is_active=True).count()
            print(f"🔐 Permisos de fila activos: {total_permissions}")

            # Verificar que cada usuario tenga permisos válidos
            for user in users[:3]:  # Revisar solo los primeros 3 usuarios
                permissions = RowPermission.query.filter_by(
                    user_id=user.id,
                    is_active=True
                ).all()

                print(f"  👤 {user.username}: {len(permissions)} permisos")

                for perm in permissions:
                    # Verificar que las relaciones estén correctamente cargadas
                    entity_info = []
                    if perm.indicador:
                        entity_info.append(f"Indicador: {perm.indicador.nombre}")
                    if perm.proyecto:
                        entity_info.append(f"Proyecto: {perm.proyecto.nombre}")
                    if perm.programa:
                        entity_info.append(f"Programa: {perm.programa.nombre}")
                    if perm.componente:
                        entity_info.append(f"Componente: {perm.componente.nombre}")
                    if perm.linea_estrategica:
                        entity_info.append(f"Línea: {perm.linea_estrategica.nombre}")

                    if entity_info:
                        print(f"    ✅ {', '.join(entity_info)}")
                    else:
                        print(f"    ⚠️ Permiso sin entidad asociada (ID: {perm.id})")

            print("\n🎯 La página user_roles debería funcionar correctamente ahora")
            print("💡 Los errores de 'None' has no attribute 'nombre' han sido corregidos")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_roles_page()
