#!/usr/bin/env python3
"""
Script para mostrar información del usuario de pruebas creado
"""
from app import create_app, db
from app.models import User, EditJustification, PlanDesarrollo

def show_test_user_info():
    """Mostrar información completa del usuario de pruebas"""
    print("📋 Información del Usuario de Pruebas")
    print("=" * 50)

    with create_app().app_context():
        # Buscar usuario de pruebas
        test_user = User.query.filter_by(username="auditor_pruebas").first()

        if not test_user:
            print("❌ Usuario de pruebas no encontrado")
            return

        print(f"👤 Usuario: {test_user.username}")
        print(f"📧 Email: {test_user.email}")
        print(f"🔑 Password: auditor123")
        print(f"📍 Municipio: {test_user.municipality}")
        print(f"🏢 Departamento: {test_user.department}")
        print(f"📊 ID de Usuario: {test_user.id}")
        print(f"✅ Estado: {'Activo' if test_user.is_active else 'Inactivo'}")
        print()

        # Obtener plan activo
        active_plan = PlanDesarrollo.query.filter_by(estado='activo').first()
        if active_plan:
            print(f"📋 Plan Activo: {active_plan.titulo}")
            print(f"🆔 ID del Plan: {active_plan.id}")
            print()

            # Obtener cambios del usuario en el plan activo
            user_changes = EditJustification.query.filter_by(
                user_id=test_user.id,
                plan_id=active_plan.id
            ).order_by(EditJustification.created_at.desc()).all()

            print(f"📊 Cambios Realizados: {len(user_changes)}")
            print()

            if user_changes:
                print("📝 Detalle de Cambios:")
                print("-" * 70)
                for i, change in enumerate(user_changes, 1):
                    print(f"{i}. 📅 {change.created_at.strftime('%d/%m/%Y %H:%M')}")
                    print(f"   📊 Columna: {change.get_column_display_name()}")
                    print(f"   🔄 Cambio: {change.old_value or 'N/A'} → {change.new_value}")
                    print(f"   📄 Archivo: {change.created_at.strftime('%Y%m%d_%H%M%S')}_plan_{change.plan_id}_{change.column_name}.txt")
                    print()

        print("🌐 Acceso al Panel de Auditoría:")
        print("-" * 40)
        print("1. Ve a la página de login")
        print("2. Inicia sesión con:")
        print("   👤 Usuario: auditor_pruebas")
        print("   🔑 Password: auditor123")
        print("3. Una vez dentro, ve al menú de usuario (esquina superior derecha)")
        print("4. Selecciona 'Panel de Auditoría'")
        print("5. O accede directamente a: /audit/")
        print()

        print("📁 Archivos de Auditoría:")
        print("-" * 40)
        import os
        audit_path = f'audit_files/user_{test_user.id}'
        if os.path.exists(audit_path):
            files = [f for f in os.listdir(audit_path) if f.endswith('.txt')]
            print(f"📂 Ubicación: {audit_path}")
            print(f"📊 Archivos: {len(files)}")
            for file in sorted(files):
                print(f"   📄 {file}")
        else:
            print("❌ No se encontraron archivos de auditoría")

        print()
        print("✅ ¡Todo listo para probar el panel de auditoría!")

if __name__ == "__main__":
    show_test_user_info()
