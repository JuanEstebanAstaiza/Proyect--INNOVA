#!/usr/bin/env python3
"""
Script básico para probar el sistema SMTP
"""
from app import create_app, db
from app.models import SMTPConfig

def test_smtp_basic():
    """Probar configuración básica de SMTP"""
    print("🧪 PRUEBA BÁSICA DEL SISTEMA SMTP")
    print("=" * 50)

    with create_app().app_context():
        try:
            # Verificar configuración de Flask-Mail
            from flask import current_app
            mail_config = current_app.config

            print("📧 CONFIGURACIÓN FLASK-MAIL:")
            print(f"   MAIL_SERVER: {mail_config.get('MAIL_SERVER', 'No configurado')}")
            print(f"   MAIL_PORT: {mail_config.get('MAIL_PORT', 'No configurado')}")
            print(f"   MAIL_USE_TLS: {mail_config.get('MAIL_USE_TLS', 'No configurado')}")
            print(f"   MAIL_USE_SSL: {mail_config.get('MAIL_USE_SSL', 'No configurado')}")
            print(f"   MAIL_USERNAME: {'Configurado' if mail_config.get('MAIL_USERNAME') else 'No configurado'}")
            print(f"   MAIL_PASSWORD: {'Configurado' if mail_config.get('MAIL_PASSWORD') else 'No configurado'}")
            print(f"   MAIL_DEFAULT_SENDER: {mail_config.get('MAIL_DEFAULT_SENDER', 'No configurado')}")

            # Verificar que Flask-Mail esté inicializado
            from flask_mail import Mail
            mail = current_app.extensions.get('mail')
            if mail:
                print("✅ Flask-Mail inicializado correctamente")
            else:
                print("❌ Flask-Mail no está inicializado")

            # Verificar configuraciones por municipio
            print("\n🏛️ CONFIGURACIONES SMTP POR MUNICIPIO:")
            smtp_configs = SMTPConfig.query.all()
            if smtp_configs:
                for config in smtp_configs[:3]:  # Mostrar máximo 3
                    print(f"   📧 {config.municipality}: {'Activa' if config.is_active else 'Inactiva'}")
            else:
                print("   ℹ️ No hay configuraciones SMTP personalizadas")

            # Verificar que podemos importar el servicio de email
            try:
                from app.utils.email_service import EmailService
                print("✅ Servicio de email importado correctamente")
            except ImportError as e:
                print(f"❌ Error importando servicio de email: {e}")

            print("\n🎯 SISTEMA SMTP:")
            if smtp_configs and mail:
                print("✅ Configurado y listo para usar")
                print("✅ Las funcionalidades de email están disponibles")
            else:
                print("⚠️ Sistema básico configurado, pero necesita configuración específica")
                print("💡 Configure SMTP en: Panel Admin → Configurar SMTP")

            return True

        except Exception as e:
            print(f"❌ Error probando sistema SMTP: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_smtp_basic()
    if success:
        print("\n🎊 ¡Sistema SMTP básico funcionando!")
    else:
        print("\n❌ Hay problemas con el sistema SMTP.")
