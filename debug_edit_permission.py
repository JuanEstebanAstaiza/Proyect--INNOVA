#!/usr/bin/env python3
"""
Script para debuggear la funcionalidad de edición de permisos
"""
from app import create_app
from app.models import RowPermission, User

def debug_permissions():
    """Debuggear permisos disponibles"""
    print("🔧 Debuggeando permisos de fila...")

    try:
        app = create_app()
        with app.app_context():
            print("✅ Aplicación creada correctamente")

            # Verificar permisos existentes
            permissions = RowPermission.query.all()
            print(f"📊 Total de permisos encontrados: {len(permissions)}")

            if permissions:
                print("\n📋 Lista de permisos:")
                for i, perm in enumerate(permissions[:5]):  # Mostrar solo los primeros 5
                    user = User.query.get(perm.user_id)
                    username = user.username if user else "Usuario desconocido"
                    print(f"  {i+1}. ID: {perm.id}, Usuario: {username}")
                    print(f"      Plan: {perm.plan_id}, Activo: {perm.is_active}")
                    print(f"      Ver: {perm.can_view}, Editar: {perm.can_edit}")
                    if perm.indicador_id:
                        print(f"      Tipo: Indicador, ID: {perm.indicador_id}")
                    elif perm.proyecto_id:
                        print(f"      Tipo: Proyecto, ID: {perm.proyecto_id}")
                    elif perm.programa_id:
                        print(f"      Tipo: Programa, ID: {perm.programa_id}")
                    elif perm.componente_id:
                        print(f"      Tipo: Componente, ID: {perm.componente_id}")
                    elif perm.linea_estrategica_id:
                        print(f"      Tipo: Línea Estratégica, ID: {perm.linea_estrategica_id}")
                    print()

                print("💡 IDs de permisos para probar:")
                for perm in permissions[:3]:
                    print(f"   - {perm.id}")

            else:
                print("❌ No hay permisos en la base de datos")
                print("💡 Necesitas crear algunos permisos primero")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n🎯 Próximos pasos:")
    print("1. Si hay permisos, anota un ID para probar")
    print("2. Ejecuta la aplicación Flask: python run.py")
    print("3. Ve a http://localhost:5000/admin/row-permissions")
    print("4. Inicia sesión como administrador")
    print("5. Haz click en 'Editar' en el permiso con el ID que anotaste")
    print("6. Abre la consola del navegador (F12 → Console) para ver los logs de debugging")

if __name__ == "__main__":
    debug_permissions()
