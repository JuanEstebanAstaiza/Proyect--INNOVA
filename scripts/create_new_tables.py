#!/usr/bin/env python3
"""
Script para crear las nuevas tablas en la base de datos
"""
from app import create_app, db
from app.models import SMTPConfig, UserTempPassword

def create_new_tables():
    """Crear las nuevas tablas en la base de datos"""
    print("🔧 Creando nuevas tablas en la base de datos...")
    print("=" * 60)

    with create_app().app_context():
        try:
            # Crear las tablas
            print("📋 Creando tabla smtp_configs...")
            SMTPConfig.__table__.create(db.engine, checkfirst=True)

            print("📋 Creando tabla user_temp_passwords...")
            UserTempPassword.__table__.create(db.engine, checkfirst=True)

            print("✅ Tablas creadas exitosamente")

            # Crear configuraciones SMTP por defecto para municipios existentes
            print("🏛️ Creando configuraciones SMTP por defecto...")

            from app.models import User
            municipios = db.session.query(User.municipality).distinct().all()

            for municipio_tuple in municipios:
                municipio = municipio_tuple[0]

                # Verificar si ya existe configuración
                existing_config = SMTPConfig.query.filter_by(municipality=municipio).first()
                if not existing_config:
                    config = SMTPConfig(
                        municipality=municipio,
                        smtp_server='smtp.gmail.com',
                        smtp_port=587,
                        smtp_username='',
                        smtp_password='',
                        sender_email='',
                        sender_name=f'Alcaldía de {municipio}'
                    )
                    db.session.add(config)
                    print(f"   ✅ Configuración creada para: {municipio}")
                else:
                    print(f"   ⚠️ Configuración ya existe para: {municipio}")

            db.session.commit()
            print("✅ Configuraciones SMTP creadas exitosamente")

            print("\n🎯 RESUMEN:")
            print(f"   📊 Configuraciones SMTP: {SMTPConfig.query.count()}")
            print(f"   👥 Municipios configurados: {len(set([c[0] for c in municipios]))}")

            return True

        except Exception as e:
            print(f"❌ Error creando tablas: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = create_new_tables()
    if success:
        print("\n🎊 ¡Tablas creadas exitosamente!")
        print("Ahora puedes:")
        print("1. ✅ Ver contraseñas temporales de usuarios")
        print("2. ✅ Configurar SMTP por municipio")
        print("3. ✅ Enviar credenciales por email")
        print("4. ✅ Probar configuraciones SMTP")
    else:
        print("\n❌ Error al crear las tablas.")
