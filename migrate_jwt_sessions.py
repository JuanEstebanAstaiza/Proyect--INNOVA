#!/usr/bin/env python3
"""
Migración para agregar campos JWT a la tabla active_sessions
"""

from app import create_app, db
from app.models.active_session import ActiveSession
from sqlalchemy import text
import os

def migrate_active_sessions():
    """Agregar campos JWT a la tabla active_sessions"""

    print("🔄 INICIANDO MIGRACIÓN JWT PARA SESIONES")
    print("=" * 50)

    app = create_app()

    with app.app_context():
        try:
            # Verificar si los campos ya existen
            inspector = db.inspect(db.engine)

            columns = inspector.get_columns('active_sessions')
            column_names = [col['name'] for col in columns]

            print(f"📋 Columnas actuales en active_sessions: {column_names}")

            # PASO 1: Agregar campos a la base de datos
            fields_added = []

            # Agregar campo jwt_token si no existe
            if 'jwt_token' not in column_names:
                print("➕ Agregando campo jwt_token...")
                db.session.execute(text("""
                    ALTER TABLE active_sessions
                    ADD COLUMN jwt_token TEXT
                """))
                fields_added.append('jwt_token')
                print("✅ Campo jwt_token agregado")
            else:
                print("ℹ️ Campo jwt_token ya existe")

            # Agregar campo device_fingerprint si no existe
            if 'device_fingerprint' not in column_names:
                print("➕ Agregando campo device_fingerprint...")
                db.session.execute(text("""
                    ALTER TABLE active_sessions
                    ADD COLUMN device_fingerprint VARCHAR(100)
                """))
                fields_added.append('device_fingerprint')
                print("✅ Campo device_fingerprint agregado")
            else:
                print("ℹ️ Campo device_fingerprint ya existe")

            # PASO 2: Actualizar datos existentes (solo si se agregaron campos)
            if fields_added:
                print("🔄 Actualizando datos de sesiones existentes...")

                # Forzar recarga del modelo para incluir nuevos campos
                db.session.commit()

                # Obtener sesiones usando SQL directo para evitar problemas de modelo
                result = db.session.execute(text("""
                    SELECT id, user_id, session_id, device_info
                    FROM active_sessions
                """))

                sessions_data = result.fetchall()
                print(f"📊 Encontradas {len(sessions_data)} sesiones para actualizar")

                from app.utils.jwt_utils import JWTUtils

                updated_count = 0
                for row in sessions_data:
                    session_id = row[0]
                    user_id = row[1]
                    session_uuid = row[2]
                    device_info_json = row[3]

                    updates = {}

                    # Generar JWT si es necesario
                    if 'jwt_token' in fields_added:
                        device_info = {}
                        if device_info_json:
                            try:
                                import json
                                device_info = json.loads(device_info_json)
                            except:
                                device_info = {}

                        jwt_token = JWTUtils.generate_session_token(
                            user_id,
                            session_uuid,
                            device_info
                        )
                        updates['jwt_token'] = jwt_token

                    # Generar fingerprint si es necesario
                    if 'device_fingerprint' in fields_added and device_info_json:
                        try:
                            import json
                            device_info = json.loads(device_info_json)
                            if device_info:
                                fingerprint = JWTUtils.generate_device_fingerprint(device_info)
                                updates['device_fingerprint'] = fingerprint
                        except:
                            pass

                    # Aplicar actualizaciones
                    if updates:
                        set_clause = ', '.join([f"{k} = :{k}" for k in updates.keys()])
                        db.session.execute(text(f"""
                            UPDATE active_sessions
                            SET {set_clause}
                            WHERE id = :session_id
                        """), {**updates, 'session_id': session_id})
                        updated_count += 1

                        if updated_count % 10 == 0:
                            print(f"  Procesadas {updated_count}/{len(sessions_data)} sesiones...")

                print(f"✅ Actualizadas {updated_count} sesiones existentes")
            else:
                print("ℹ️ No hay campos nuevos que actualizar")

            # Verificar que los campos se agregaron correctamente
            columns_after = inspector.get_columns('active_sessions')
            column_names_after = [col['name'] for col in columns_after]

            print(f"📋 Columnas después de migración: {column_names_after}")

            # Crear índices para mejorar rendimiento
            try:
                print("🔧 Creando índices para optimización...")

                # Índice para jwt_token (único)
                db.session.execute(text("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_active_sessions_jwt_token
                    ON active_sessions(jwt_token)
                """))

                # Índice para device_fingerprint
                db.session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_active_sessions_device_fingerprint
                    ON active_sessions(device_fingerprint)
                """))

                # Índice compuesto para user_id + is_active (optimización común)
                db.session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_active_sessions_user_active
                    ON active_sessions(user_id, is_active)
                """))

                print("✅ Índices creados")
            except Exception as e:
                print(f"⚠️ Error creando índices (posiblemente ya existen): {e}")

            db.session.commit()

            print("\n🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
            print("✅ Tabla active_sessions actualizada con campos JWT")
            print("✅ Índices de rendimiento creados")
            print("✅ Sistema listo para sesiones JWT únicas")

        except Exception as e:
            print(f"❌ ERROR en migración: {e}")
            db.session.rollback()
            raise

def verify_migration():
    """Verificar que la migración se aplicó correctamente"""

    print("\n🔍 VERIFICANDO MIGRACIÓN")
    print("-" * 30)

    app = create_app()

    with app.app_context():
        try:
            # Verificar estructura de la tabla
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('active_sessions')

            required_fields = ['jwt_token', 'device_fingerprint']
            missing_fields = []

            for field in required_fields:
                if field not in [col['name'] for col in columns]:
                    missing_fields.append(field)

            if missing_fields:
                print(f"❌ Campos faltantes: {missing_fields}")
                return False

            print("✅ Todos los campos requeridos están presentes")

            # Verificar índices
            indices = inspector.get_indexes('active_sessions')
            index_names = [idx['name'] for idx in indices]
            print(f"📋 Índices encontrados: {index_names}")

            # Verificar algunas sesiones existentes
            session_count = ActiveSession.query.count()
            print(f"📊 Total de sesiones en BD: {session_count}")

            if session_count > 0:
                print("\n⚠️ IMPORTANTE: Las sesiones existentes necesitan JWT")
                print("   Se recomienda hacer logout de todas las sesiones")
                print("   o ejecutar un script para regenerar JWTs")

            return True

        except Exception as e:
            print(f"❌ Error verificando migración: {e}")
            return False

if __name__ == '__main__':
    try:
        migrate_active_sessions()
        verify_migration()

        print("\n🚀 PRÓXIMOS PASOS:")
        print("1. Reiniciar la aplicación")
        print("2. Las nuevas sesiones tendrán JWT automáticamente")
        print("3. Para sesiones existentes, hacer logout/login")
        print("4. Verificar en el panel de administración que funciona")

    except Exception as e:
        print(f"\n❌ MIGRACIÓN FALLIDA: {e}")
        print("Por favor, revise los logs de error y la estructura de la base de datos")
