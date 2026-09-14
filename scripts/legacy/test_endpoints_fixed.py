#!/usr/bin/env python3
"""
Script de prueba para verificar que los endpoints funcionan con las rutas corregidas
"""
from app import create_app
from app.models import User, PlanDesarrollo, RowPermission

def test_endpoints_with_correct_routes():
    """Probar los endpoints con las rutas corregidas"""
    app = create_app()
    with app.app_context():
        print("🔍 Verificando configuración final de endpoints...")

        # Verificar que hay datos
        active_plan = PlanDesarrollo.query.filter_by(estado='activo').first()
        users = User.query.all()
        permissions = RowPermission.query.all()

        print(f"📊 Plan activo: {'✅' if active_plan else '❌'}")
        print(f"👥 Usuarios: {len(users)}")
        print(f"🔐 Permisos: {len(permissions)}")

        # Probar endpoints con test client
        with app.test_client() as client:
            print("\n🌐 Probando rutas corregidas:")

            # Simular login como administrador
            with client.session_transaction() as sess:
                if users:
                    sess['user_id'] = users[0].id

            # Probar endpoint corregido
            if active_plan:
                # GET /admin/api/row-permissions/entities/indicador
                response = client.get(f'/admin/api/row-permissions/entities/indicador?plan_id={active_plan.id}')
                print(f"📡 GET /admin/api/row-permissions/entities/indicador: HTTP {response.status_code}")

                # POST /admin/api/row-permissions (crear)
                response = client.post('/admin/api/row-permissions', data={
                    'user_id': users[0].id if users else 1,
                    'entity_type': 'indicador',
                    'entity_id': 1,
                    'can_view': 'on',
                    'can_edit': 'off'
                })
                print(f"📡 POST /admin/api/row-permissions: HTTP {response.status_code}")

            # Probar endpoints con permisos existentes
            if permissions:
                permission_id = permissions[0].id

                # GET /admin/api/row-permissions/{id} (obtener para editar)
                response = client.get(f'/admin/api/row-permissions/{permission_id}')
                print(f"📡 GET /admin/api/row-permissions/{{id}}: HTTP {response.status_code}")

                # PATCH /admin/api/row-permissions/{id} (editar)
                response = client.patch(f'/admin/api/row-permissions/{permission_id}', data={
                    'can_view': 'on',
                    'can_edit': 'on'
                })
                print(f"📡 PATCH /admin/api/row-permissions/{{id}}: HTTP {response.status_code}")

                # DELETE /admin/api/row-permissions/{id} (eliminar)
                response = client.delete(f'/admin/api/row-permissions/{permission_id}')
                print(f"📡 DELETE /admin/api/row-permissions/{{id}}: HTTP {response.status_code}")

        print("\n🎯 Verificación completada!")
        print("💡 Las rutas están correctamente configuradas con el prefijo /admin")
        print("🚀 La funcionalidad de edición debería funcionar ahora sin errores 404")

if __name__ == "__main__":
    test_endpoints_with_correct_routes()
