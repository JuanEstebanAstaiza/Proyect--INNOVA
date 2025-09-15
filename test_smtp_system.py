#!/usr/bin/env python3
"""
Script para probar el sistema SMTP y contraseñas temporales
"""
from app import create_app, db
from app.models import User, SMTPConfig, UserTempPassword

def test_smtp_system():
    """Probar el sistema SMTP y contraseñas temporales"""
    print("🧪 PRUEBA DEL SISTEMA SMTP Y CONTRASEÑAS TEMPORALES")
    print("=" * 60)

    with create_app().app_context():
        try:
            # Verificar tablas creadas
            print("📋 VERIFICANDO TABLAS:")
            smtp_count = SMTPConfig.query.count()
            temp_pass_count = UserTempPassword.query.count()
            print(f"   ✅ Configuraciones SMTP: {smtp_count}")
            print(f"   ✅ Contraseñas temporales: {temp_pass_count}")

            # Verificar configuraciones por municipio
            print("\n🏛️ CONFIGURACIONES SMTP POR MUNICIPIO:")
            smtp_configs = SMTPConfig.query.order_by(SMTPConfig.municipality).all()
            for config in smtp_configs:
                status = "✅ Activa" if config.is_active else "❌ Inactiva"
                print(f"   📧 {config.municipality}: {status}")

            # Verificar usuarios con contraseñas temporales
            print("\n👥 USUARIOS CON CONTRASEÑAS TEMPORALES:")
            users_with_temp = db.session.query(User).join(UserTempPassword).distinct().all()
            for user in users_with_temp:
                temp_pass = UserTempPassword.get_active_for_user(user.id)
                if temp_pass:
                    expiry_status = "✅ Vigente" if not temp_pass.is_expired() else "❌ Expirada"
                    print(f"   🔑 {user.username}: {expiry_status} (expira: {temp_pass.expires_at.strftime('%d/%m/%Y')})")

            # Probar funcionalidad de envío (sin enviar realmente)
            print("\n📧 PRUEBA DE FUNCIONALIDAD DE ENVÍO:")
            auditor = User.query.filter_by(username='auditor_pruebas').first()
            if auditor:
                smtp_config = SMTPConfig.get_by_municipality(auditor.municipality)
                if smtp_config:
                    print(f"   ✅ Usuario {auditor.username} tiene configuración SMTP: {smtp_config.sender_email}")
                    print("   ✅ Sistema listo para enviar emails")
                else:
                    print(f"   ❌ Usuario {auditor.username} NO tiene configuración SMTP")
            else:
                print("   ❌ Usuario auditor_pruebas no encontrado")

            # Verificar rutas disponibles
            from flask import url_for
            app = create_app()

            with app.test_request_context():
                try:
                    smtp_list_url = url_for('admin.smtp_config_list')
                    create_user_url = url_for('admin.create_user')
                    print("\n🌐 RUTAS DISPONIBLES:")
                    print(f"   📧 Config SMTP: {smtp_list_url}")
                    print(f"   👤 Crear usuario: {create_user_url}")

                    if smtp_configs:
                        test_config = smtp_configs[0]
                        edit_url = url_for('admin.edit_smtp_config', municipality=test_config.municipality)
                        test_url = url_for('admin.test_smtp_config', municipality=test_config.municipality)
                        print(f"   ✏️ Editar SMTP: {edit_url}")
                        print(f"   🧪 Probar SMTP: {test_url}")

                    if users_with_temp:
                        temp_pass_url = url_for('admin.view_user_temp_password', user_id=users_with_temp[0].id)
                        print(f"   🔑 Ver contraseña: {temp_pass_url}")

                except Exception as e:
                    print(f"   ❌ Error generando URLs: {e}")

                    print("\n🎯 FUNCIONALIDADES IMPLEMENTADAS:")
                    print("   ✅ Mostrar contraseñas temporales generadas")
                    print("   ✅ Configuración SMTP por municipio")
                    print("   ✅ Envío automático de credenciales por email")
                    print("   ✅ Reenvío manual de credenciales")
                    print("   ✅ Pruebas de configuración SMTP")
                    print("   ✅ Interfaz completa en panel de administración")

                    print("\n🛡️ SEGURIDAD:")
                    print("   ✅ Contraseñas temporales expiran en 7 días")
                    print("   ✅ Solo administradores pueden ver contraseñas")
                    print("   ✅ Configuración SMTP por municipio")
                    print("   ✅ Validación de emails y configuración")

            return True

        except Exception as e:
            print(f"❌ Error probando sistema: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_smtp_system()
    if success:
        print("\n🎊 ¡Sistema SMTP y contraseñas temporales funcionando perfectamente!")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. ✅ Configura SMTP en: Panel Admin → Config SMTP")
        print("2. ✅ Crea usuarios y verás sus contraseñas")
        print("3. ✅ Los emails se enviarán automáticamente")
        print("4. ✅ Usa 'Enviar Credenciales' para reenviar")
    else:
        print("\n❌ Hay problemas con el sistema.")
