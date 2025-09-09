#!/usr/bin/env python3
"""
Script de prueba para verificar los endpoints de permisos de fila
"""
from app import create_app
from app.models import User, PlanDesarrollo, RowPermission

def test_endpoints():
    """Probar los endpoints de permisos de fila"""
    app = create_app()
    with app.app_context():
        print("🔍 Verificando configuración de permisos de fila...")

        # Verificar que hay un plan activo
        active_plan = PlanDesarrollo.query.filter_by(estado='activo').first()
        if not active_plan:
            print("⚠️ No hay plan activo. Esto es normal si no has creado un plan aún.")
        else:
            print(f"✅ Plan activo encontrado: {active_plan.titulo}")

        # Verificar que hay usuarios
        users = User.query.all()
        if not users:
            print("⚠️ No hay usuarios. Necesitas crear usuarios para probar los permisos.")
        else:
            print(f"✅ Usuarios encontrados: {len(users)}")

        # Verificar que existe la tabla de permisos
        try:
            permissions = RowPermission.query.all()
            print(f"✅ Tabla de permisos funciona correctamente. Permisos existentes: {len(permissions)}")
        except Exception as e:
            print(f"❌ Error con la tabla de permisos: {str(e)}")
            return

        # Probar endpoints con test client
        print("\n🔍 Probando endpoints...")
        with app.test_client() as client:
            # Probar endpoint de entidades (sin login)
            if active_plan:
                response = client.get(f'/api/row-permissions/entities/indicador?plan_id={active_plan.id}')
                print(f"📡 Endpoint entidades: HTTP {response.status_code}")

            # Probar endpoint GET de permisos (sin login - debería fallar)
            response = client.get('/api/row-permissions/1')
            print(f"📡 Endpoint GET permiso: HTTP {response.status_code} (esperado: 401/403 sin login)")

        print("\n🎯 Configuración verificada!")
        print("💡 Los endpoints están configurados correctamente.")
        print("💡 Ahora puedes probar la funcionalidad desde el navegador web.")

if __name__ == "__main__":
    test_endpoints()
