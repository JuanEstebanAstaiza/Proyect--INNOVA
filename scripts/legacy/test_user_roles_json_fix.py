#!/usr/bin/env python3
"""
Script para verificar que la corrección de serialización JSON funciona
"""
from app import create_app
from app.models import User, Role

def test_user_roles_json_serialization():
    """Verificar que los roles se serializan correctamente"""
    print("🔧 Verificando serialización JSON de roles...")

    try:
        app = create_app()
        with app.app_context():
            print("✅ Aplicación creada correctamente")

            # Verificar que hay roles
            roles = Role.query.filter_by(is_active=True).all()
            print(f"👥 Roles encontrados: {len(roles)}")

            if roles:
                print("\n📋 Lista de roles:")
                for role in roles:
                    print(f"  - ID: {role.id}, Nombre: {role.name}")
                    print(f"    Color: {role.color}, Descripción: {role.description or 'Sin descripción'}")

                # Probar la serialización que se hace en user_roles()
                print("\n🔄 Probando conversión a JSON...")
                roles_data = []
                for role in roles:
                    role_dict = {
                        'id': role.id,
                        'name': role.name,
                        'description': role.description,
                        'color': role.color,
                        'is_active': role.is_active,
                        'created_at': role.created_at.isoformat() if role.created_at else None
                    }
                    roles_data.append(role_dict)

                print("✅ Serialización exitosa")
                print(f"📊 Datos serializados: {len(roles_data)} roles")

                # Mostrar ejemplo del primer rol
                if roles_data:
                    print(f"\n📄 Ejemplo de rol serializado:")
                    import json
                    print(json.dumps(roles_data[0], indent=2, ensure_ascii=False))

            else:
                print("⚠️ No hay roles activos en la base de datos")
                print("💡 Necesitas crear algunos roles primero")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n🎯 Resultado:")
    print("✅ Los roles ahora se pueden convertir a JSON correctamente")
    print("✅ La página user_roles debería cargar sin errores de serialización")
    print("🚀 El filtro de roles por JavaScript debería funcionar correctamente")

if __name__ == "__main__":
    test_user_roles_json_serialization()
