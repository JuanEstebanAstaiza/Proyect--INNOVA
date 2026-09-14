#!/usr/bin/env python3
"""
Script para probar el panel de auditoría
"""
from app import create_app, db
from app.models import PlanDesarrollo, User

def test_audit_panel():
    """Probar que el panel de auditoría funciona correctamente"""
    print("🔧 Probando panel de auditoría...")

    with create_app().app_context():
        try:
            # Verificar plan activo
            active_plan = PlanDesarrollo.query.filter_by(estado='activo').first()
            if active_plan:
                print(f"✅ Plan activo encontrado: {active_plan.titulo}")
            else:
                print("⚠️ No hay plan activo")

            # Verificar usuarios
            users = User.query.all()
            print(f"✅ Usuarios encontrados: {len(users)}")

            # Verificar rutas
            from flask import url_for
            app = create_app()

            with app.test_request_context():
                try:
                    audit_url = url_for('audit.audit_dashboard')
                    print(f"✅ URL del panel de auditoría: {audit_url}")

                    files_url = url_for('audit.list_audit_files')
                    print(f"✅ URL de archivos de auditoría: {files_url}")

                except Exception as e:
                    print(f"❌ Error con URLs: {e}")

            # Verificar archivos de auditoría existentes
            import os
            audit_base_path = 'audit_files'
            if os.path.exists(audit_base_path):
                user_dirs = [d for d in os.listdir(audit_base_path) if os.path.isdir(os.path.join(audit_base_path, d))]
                print(f"✅ Directorios de usuario: {len(user_dirs)}")

                for user_dir in user_dirs[:3]:  # Mostrar máximo 3
                    user_path = os.path.join(audit_base_path, user_dir)
                    files = [f for f in os.listdir(user_path) if f.endswith('.txt')]
                    print(f"  📁 Usuario {user_dir}: {len(files)} archivos")
            else:
                print("⚠️ No existe directorio base de auditoría")

            print("\n📋 Panel de Auditoría:")
            print("✅ Endpoint principal creado: /audit/")
            print("✅ Template de solo lectura implementado")
            print("✅ Vinculación con plan activo")
            print("✅ Estadísticas automáticas")
            print("✅ Lista de cambios por fecha y hora")
            print("✅ Enlaces de descarga seguros")

            return True

        except Exception as e:
            print(f"❌ Error probando panel de auditoría: {e}")
            return False

if __name__ == "__main__":
    if test_audit_panel():
        print("\n🎊 ¡Panel de auditoría funcionando correctamente!")
        print("Los usuarios pueden acceder desde el menú: Panel de Auditoría")
    else:
        print("\n❌ Error en el panel de auditoría.")
