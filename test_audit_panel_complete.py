#!/usr/bin/env python3
"""
Script completo para probar el panel de auditoría con el usuario de pruebas
"""
from app import create_app, db
from app.models import User, PlanDesarrollo, EditJustification
from flask import url_for

def test_audit_panel_complete():
    """Probar el panel de auditoría de manera completa"""
    print("🔧 Probando panel de auditoría completo...")
    print("=" * 60)

    with create_app().app_context():
        try:
            # Verificar usuario de pruebas
            test_user = User.query.filter_by(username="auditor_pruebas").first()
            if not test_user:
                print("❌ Usuario de pruebas no encontrado")
                return False

            print(f"✅ Usuario de pruebas encontrado: {test_user.username}")
            print(f"   📧 Email: {test_user.email}")
            print(f"   🆔 ID: {test_user.id}")
            print()

            # Verificar plan activo
            active_plan = PlanDesarrollo.query.filter_by(estado='activo').first()
            if not active_plan:
                print("❌ No hay plan activo")
                return False

            print(f"✅ Plan activo encontrado: {active_plan.titulo}")
            print(f"   🆔 ID: {active_plan.id}")
            print()

            # Verificar cambios del usuario
            user_changes = EditJustification.query.filter_by(
                user_id=test_user.id,
                plan_id=active_plan.id
            ).order_by(EditJustification.created_at.desc()).all()

            print(f"✅ Cambios encontrados: {len(user_changes)}")
            for i, change in enumerate(user_changes, 1):
                print(f"   {i}. {change.created_at.strftime('%d/%m/%Y %H:%M')} - {change.get_column_display_name()}")
                print(f"      {change.old_value or 'N/A'} → {change.new_value}")
            print()

            # Verificar archivos de auditoría
            import os
            audit_path = f'audit_files/user_{test_user.id}'
            if os.path.exists(audit_path):
                files = [f for f in os.listdir(audit_path) if f.endswith('.txt')]
                print(f"✅ Archivos de auditoría encontrados: {len(files)}")
                for file in sorted(files):
                    file_path = os.path.join(audit_path, file)
                    size = os.path.getsize(file_path)
                    print(f"      📄 {file} ({size/1024:.1f} KB)")
            else:
                print("❌ No se encontraron archivos de auditoría")

            print()
            print("🌐 URLs de acceso:")
            print("-" * 30)

            # Simular contexto de Flask para probar URLs
            from flask import Flask
            app = create_app()

            with app.test_request_context():
                try:
                    login_url = url_for('auth.login')
                    audit_url = url_for('audit.audit_dashboard')
                    files_url = url_for('audit.list_audit_files')

                    print(f"📱 Login: {login_url}")
                    print(f"📊 Panel Auditoría: {audit_url}")
                    print(f"📁 Lista Archivos: {files_url}")

                except Exception as e:
                    print(f"⚠️ Error generando URLs: {e}")

            print()
            print("🎯 INSTRUCCIONES PARA PROBAR:")
            print("-" * 40)
            print("1. Abre tu navegador")
            print("2. Ve a la página de login")
            print("3. Inicia sesión con:")
            print("   👤 Usuario: auditor_pruebas")
            print("   🔑 Password: auditor123")
            print("4. Ve al menú usuario (esquina superior derecha)")
            print("5. Selecciona 'Panel de Auditoría'")
            print("6. Explora todas las funcionalidades:")
            print("   • Ver estadísticas generales")
            print("   • Revisar lista de cambios")
            print("   • Descargar archivos de auditoría")
            print("   • Ver información del plan activo")

            print()
            print("✅ ¡Panel de auditoría listo para pruebas!")

            return True

        except Exception as e:
            print(f"❌ Error probando panel de auditoría: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_audit_panel_complete()
    if success:
        print("\n🎊 ¡Todo está listo para que pruebes el panel de auditoría!")
        print("El usuario 'auditor_pruebas' tiene 5 cambios registrados y 6 archivos de auditoría.")
    else:
        print("\n❌ Hay problemas con la configuración del panel de auditoría.")
