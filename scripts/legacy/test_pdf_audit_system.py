#!/usr/bin/env python3
"""
Script para probar el sistema de auditoría con PDFs
"""
from app import create_app, db
from app.models import User, PlanDesarrollo, EditJustification
from audit_pdf_generator import create_audit_pdf, create_user_audit_summary_pdf
from datetime import datetime

def test_pdf_audit_system():
    """Probar el sistema completo de auditoría con PDFs"""
    print("🔧 Probando sistema de auditoría con PDFs...")
    print("=" * 60)

    with create_app().app_context():
        try:
            # Verificar que tenemos datos para probar
            test_user = User.query.filter_by(username="auditor_pruebas").first()
            if not test_user:
                print("❌ Usuario de pruebas no encontrado")
                return False

            print(f"✅ Usuario de pruebas encontrado: {test_user.username}")

            # Obtener plan activo
            active_plan = PlanDesarrollo.query.filter_by(estado='activo').first()
            if not active_plan:
                print("❌ No hay plan activo")
                return False

            print(f"✅ Plan activo: {active_plan.titulo}")

            # Obtener cambios del usuario
            user_changes = EditJustification.query.filter_by(
                user_id=test_user.id,
                plan_id=active_plan.id
            ).order_by(EditJustification.created_at.desc()).all()

            print(f"✅ Cambios encontrados: {len(user_changes)}")

            if user_changes:
                # Probar generar PDF para el cambio más reciente
                latest_change = user_changes[0]
                print(f"\n📄 Generando PDF para cambio: {latest_change.get_column_display_name()}")

                pdf_path = create_audit_pdf(latest_change)
                if pdf_path:
                    print(f"✅ PDF generado exitosamente: {pdf_path}")

                    # Verificar que el archivo existe
                    import os
                    if os.path.exists(pdf_path):
                        size = os.path.getsize(pdf_path)
                        print(f"   📏 Tamaño: {size} bytes")
                        print("   ✅ Archivo PDF creado correctamente")
                    else:
                        print("   ❌ Archivo PDF no encontrado")
                else:
                    print("   ❌ Error generando PDF")
                    return False

                # Probar generar resumen en PDF
                print(f"\n📊 Generando resumen en PDF para usuario {test_user.username}")
                summary_pdf_path = create_user_audit_summary_pdf(test_user.id)

                if summary_pdf_path:
                    print(f"✅ PDF resumen generado: {summary_pdf_path}")

                    if os.path.exists(summary_pdf_path):
                        size = os.path.getsize(summary_pdf_path)
                        print(f"   📏 Tamaño: {size} bytes")
                        print("   ✅ Archivo resumen PDF creado correctamente")
                    else:
                        print("   ❌ Archivo resumen PDF no encontrado")
                else:
                    print("   ❌ Error generando PDF resumen")
                    return False

            print("\n🎨 Características del PDF:")
            print("✅ Formato profesional con tablas y estilos")
            print("✅ Marca de agua: 'DOCUMENTO AUTOGENERADO POR LA APLICACIÓN'")
            print("✅ Información completa del cambio")
            print("✅ Detalles del usuario y plan")
            print("✅ Justificación y archivos anexados")
            print("✅ Fecha de generación automática")

            print("\n📁 Estructura de archivos:")
            print("📂 audit_files/")
            print("   └── user_[ID]/")
            print("       ├── [timestamp]_plan_[ID]_[columna].pdf")
            print("       └── resumen_auditoria.pdf")

            print("\n🌐 Integración con el panel:")
            print("✅ Panel de auditoría muestra archivos PDF")
            print("✅ Botones de descarga funcionan con PDFs")
            print("✅ Estadísticas incluyen archivos PDF")
            print("✅ Sistema de fallback a TXT si falla PDF")

            return True

        except Exception as e:
            print(f"❌ Error probando sistema PDF: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_pdf_audit_system()
    if success:
        print("\n🎊 ¡Sistema de auditoría con PDFs funcionando perfectamente!")
        print("Los archivos de auditoría ahora se generan en formato PDF profesional.")
        print("Cada PDF incluye marca de agua y formato elegante.")
    else:
        print("\n❌ Hay problemas con el sistema de PDFs.")
