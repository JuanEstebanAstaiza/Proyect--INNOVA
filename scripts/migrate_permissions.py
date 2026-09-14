#!/usr/bin/env python3
"""
Script de migración para agregar el sistema de permisos avanzado a la base de datos existente
"""

import os
import sys

# Permite ejecutar este script desde cualquier directorio: anade la raiz del
# proyecto al sys.path para poder importar el paquete `app`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# La consola de Windows usa cp1252 y no puede imprimir acentos ni simbolos.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, 'reconfigure'):
        _stream.reconfigure(encoding='utf-8', errors='replace')


import os
import sqlite3


def migrate_database():
    """Migra la base de datos existente para incluir el sistema de permisos avanzado"""

    db_path = 'instance/alcaldias_dev.db'
    backup_path = 'instance/alcaldias_dev_backup.db'

    if not os.path.exists(db_path):
        print("❌ Error: No se encontró la base de datos existente")
        return False

    print("🔄 Iniciando migración del sistema de permisos avanzado...")

    # Crear backup de la base de datos
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup creado: {backup_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verificar si ya existe la columna legacy_role
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'legacy_role' not in column_names:
            print("📝 Agregando columna legacy_role a la tabla users...")
            cursor.execute("ALTER TABLE users ADD COLUMN legacy_role VARCHAR(20) DEFAULT 'viewer'")
            print("✅ Columna legacy_role agregada")

            # Migrar roles existentes al legacy_role
            cursor.execute("UPDATE users SET legacy_role = role WHERE role IS NOT NULL")
            print("✅ Roles existentes migrados a legacy_role")

        # Crear tabla roles
        print("🏗️ Creando tabla roles...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                color VARCHAR(7) DEFAULT '#007bff',
                is_active BOOLEAN DEFAULT 1,
                is_system_role BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Tabla roles creada")

        # Crear tabla column_permissions
        print("🏗️ Creando tabla column_permissions...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS column_permissions (
                id INTEGER PRIMARY KEY,
                role_id INTEGER NOT NULL,
                column_name VARCHAR(200) NOT NULL,
                can_view BOOLEAN DEFAULT 1,
                can_edit BOOLEAN DEFAULT 0,
                category VARCHAR(50) DEFAULT 'general',
                FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE
            )
        """)
        print("✅ Tabla column_permissions creada")

        # Crear tabla row_permissions
        print("🏗️ Creando tabla row_permissions...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS row_permissions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                indicador_id INTEGER NOT NULL,
                can_edit BOOLEAN DEFAULT 1,
                search_term VARCHAR(200),
                assigned_by INTEGER,
                assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (indicador_id) REFERENCES indicadores_producto (id) ON DELETE CASCADE,
                FOREIGN KEY (assigned_by) REFERENCES users (id)
            )
        """)
        print("✅ Tabla row_permissions creada")

        # Crear tabla user_roles
        print("🏗️ Creando tabla user_roles...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_roles (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                assigned_by INTEGER,
                assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE,
                FOREIGN KEY (assigned_by) REFERENCES users (id)
            )
        """)
        print("✅ Tabla user_roles creada")

        # Crear índices para mejor performance
        print("📊 Creando índices...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_column_permissions_role ON column_permissions(role_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_column_permissions_column ON column_permissions(column_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_row_permissions_user ON row_permissions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_row_permissions_indicador ON row_permissions(indicador_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_roles_active ON user_roles(is_active)")
        print("✅ Índices creados")

        # Insertar roles por defecto
        print("🎭 Insertando roles por defecto...")

        roles_data = [
            (1, 'Administrador', 'Acceso completo al sistema. Puede gestionar usuarios, roles y editar todos los planes.', '#dc3545', 1, 1),
            (2, 'Editor General', 'Puede editar planes de desarrollo pero no gestionar usuarios o roles.', '#28a745', 1, 1),
            (3, 'Editor de Ejecución', 'Puede editar datos de ejecución trimestral y porcentajes de cumplimiento.', '#007bff', 1, 0),
            (4, 'Visualizador', 'Solo puede ver información del plan de desarrollo.', '#6c757d', 1, 1),
            (5, 'Editor de Metas', 'Puede editar metas, indicadores y datos básicos del plan.', '#ffc107', 1, 0)
        ]

        cursor.executemany("""
            INSERT OR IGNORE INTO roles (id, name, description, color, is_active, is_system_role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, roles_data)
        print("✅ Roles por defecto insertados")

        # Insertar permisos de columna por defecto para cada rol
        print("🔐 Configurando permisos de columna por defecto...")

        # Columnas disponibles en el sistema
        columns = [
            'CÓD LINEA', 'LINEAS ESTRATEGICAS', 'CÓD COMPONENTE', 'COMPONENTES',
            'CÓD PROGRAMA', 'PROGRAMA PDM', 'DEPENDENCIA RESPOSABLE', 'BPIM',
            'NOMBRE PROYECTO', 'INDICADORES ', 'CÓD INDICADOR DE PRODUCTO',
            'INDICADOR DE PRODUCTO', 'TIPO DE INDICADOR', 'LINEA BASE', 'SENTIDO',
            'TIPOLOGÍA', 'UNIDAD', 'META CUATRIENIO (2024-2027)', 'META 2024',
            'EJECUCIÓN I TRIMESTRE ', 'EJECUCIÓN II TRIMESTRE ',
            'EJECUCIÓN III TRIMESTRE ', 'EJECUCIÓN IV TRIMESTRE ',
            'EJECUCIÓN ACUMULADA', '% CUMPLIMIENTO I TRIMESTRE',
            '% CUMPLIMIENTO II TRIMESTRE', '% CUMPLIMIENTO III TRIMESTRE',
            '% CUMPLIMIENTO IV TRIMESTRE', '% CUMPLIMIENTO ACUMULADO',
            'POBLACIÓN IMPACTADA POR SECTOR I TRIMESTRE',
            'POBLACIÓN IMPACTADA POR SECTOR II TRIMESTRE',
            'POBLACIÓN IMPACTADA POR SECTOR III TRIMESTRE',
            'POBLACIÓN IMPACTADA POR SECTOR IV TRIMESTRE',
            'OBSERVACIÓN AL CUMPLIMIENTO ITRIMESTRE',
            'OBSERVACIÓN AL CUMPLIMIENTO II TRIMESTRE',
            'OBSERVACIÓN AL CUMPLIMIENTO III TRIMESTRE',
            'OBSERVACIÓN AL CUMPLIMIENTO IV TRIMESTRE'
        ]

        # Definir permisos por rol
        role_permissions = {
            1: {  # Administrador - todo editable
                'view_all': True,
                'edit_all': True
            },
            2: {  # Editor General - casi todo editable excepto estructura
                'view_all': True,
                'edit_all': True,
                'exclude_edit': ['DEPENDENCIA RESPOSABLE', 'CÓD LINEA', 'CÓD COMPONENTE', 'CÓD PROGRAMA']
            },
            3: {  # Editor de Ejecución - solo ejecución y cumplimiento
                'view_all': True,
                'edit_only': [
                    'EJECUCIÓN I TRIMESTRE ', 'EJECUCIÓN II TRIMESTRE ',
                    'EJECUCIÓN III TRIMESTRE ', 'EJECUCIÓN IV TRIMESTRE ',
                    'EJECUCIÓN ACUMULADA', '% CUMPLIMIENTO I TRIMESTRE',
                    '% CUMPLIMIENTO II TRIMESTRE', '% CUMPLIMIENTO III TRIMESTRE',
                    '% CUMPLIMIENTO IV TRIMESTRE', '% CUMPLIMIENTO ACUMULADO',
                    'POBLACIÓN IMPACTADA POR SECTOR I TRIMESTRE',
                    'POBLACIÓN IMPACTADA POR SECTOR II TRIMESTRE',
                    'POBLACIÓN IMPACTADA POR SECTOR III TRIMESTRE',
                    'POBLACIÓN IMPACTADA POR SECTOR IV TRIMESTRE',
                    'OBSERVACIÓN AL CUMPLIMIENTO ITRIMESTRE',
                    'OBSERVACIÓN AL CUMPLIMIENTO II TRIMESTRE',
                    'OBSERVACIÓN AL CUMPLIMIENTO III TRIMESTRE',
                    'OBSERVACIÓN AL CUMPLIMIENTO IV TRIMESTRE'
                ]
            },
            4: {  # Visualizador - solo lectura
                'view_all': True,
                'edit_all': False
            },
            5: {  # Editor de Metas - metas e indicadores
                'view_all': True,
                'edit_only': [
                    'INDICADORES ', 'CÓD INDICADOR DE PRODUCTO',
                    'INDICADOR DE PRODUCTO', 'TIPO DE INDICADOR', 'LINEA BASE',
                    'SENTIDO', 'TIPOLOGÍA', 'UNIDAD',
                    'META CUATRIENIO (2024-2027)', 'META 2024'
                ]
            }
        }

        # Insertar permisos para cada rol
        for role_id, permissions in role_permissions.items():
            for column in columns:
                can_view = permissions.get('view_all', False)
                can_edit = False

                if permissions.get('edit_all', False):
                    can_edit = column not in permissions.get('exclude_edit', [])
                elif permissions.get('edit_only'):
                    can_edit = column in permissions['edit_only']
                else:
                    can_edit = False

                # Determinar categoría
                category = 'general'
                if any(keyword in column.upper() for keyword in ['CÓD', 'LINEA', 'COMPONENTE', 'PROGRAMA', 'PROYECTO']):
                    category = 'estructura'
                elif any(keyword in column.upper() for keyword in ['INDICADOR', 'META', 'BASE', 'TIPO', 'UNIDAD']):
                    category = 'indicadores'
                elif any(keyword in column.upper() for keyword in ['EJECUCIÓN', 'TRIMESTRE']):
                    category = 'ejecucion'
                elif any(keyword in column.upper() for keyword in ['CUMPLIMIENTO', '%']):
                    category = 'cumplimiento'
                elif 'POBLACIÓN' in column.upper():
                    category = 'poblacion'
                elif 'OBSERVACIÓN' in column.upper():
                    category = 'observaciones'

                cursor.execute("""
                    INSERT OR IGNORE INTO column_permissions
                    (role_id, column_name, can_view, can_edit, category)
                    VALUES (?, ?, ?, ?, ?)
                """, (role_id, column, can_view, can_edit, category))

        print("✅ Permisos de columna configurados")

        # Migrar usuarios existentes a roles
        print("👥 Migrando usuarios existentes a roles...")

        # Obtener usuarios existentes
        cursor.execute("SELECT id, legacy_role FROM users WHERE is_active = 1")
        users = cursor.fetchall()

        for user_id, legacy_role in users:
            role_id = None
            if legacy_role == 'admin':
                role_id = 1  # Administrador
            elif legacy_role == 'editor':
                role_id = 2  # Editor General
            else:
                role_id = 4  # Visualizador

            if role_id:
                cursor.execute("""
                    INSERT OR IGNORE INTO user_roles
                    (user_id, role_id, is_active, assigned_by, notes)
                    VALUES (?, ?, 1, 1, 'Asignación automática desde sistema legacy')
                """, (user_id, role_id))

        print("✅ Usuarios migrados a roles")

        # Confirmar cambios
        conn.commit()
        print("✅ Migración completada exitosamente!")

        return True

    except Exception as e:
        print(f"❌ Error durante la migración: {e!s}")
        conn.rollback()
        return False

    finally:
        conn.close()

def verify_migration():
    """Verifica que la migración se realizó correctamente"""
    print("\n🔍 Verificando migración...")

    try:
        conn = sqlite3.connect('instance/alcaldias_dev.db')
        cursor = conn.cursor()

        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]

        required_tables = ['roles', 'column_permissions', 'row_permissions', 'user_roles']
        missing_tables = [table for table in required_tables if table not in table_names]

        if missing_tables:
            print(f"❌ Faltan las siguientes tablas: {missing_tables}")
            return False

        # Verificar columna legacy_role
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'legacy_role' not in column_names:
            print("❌ Falta la columna legacy_role en la tabla users")
            return False

        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM roles")
        roles_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM column_permissions")
        permissions_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM user_roles")
        user_roles_count = cursor.fetchone()[0]

        print("✅ Verificación completada:")
        print(f"   • {roles_count} roles creados")
        print(f"   • {permissions_count} permisos de columna configurados")
        print(f"   • {user_roles_count} asignaciones de usuario-rol creadas")

        return True

    except Exception as e:
        print(f"❌ Error en verificación: {e!s}")
        return False

    finally:
        conn.close()

if __name__ == '__main__':
    print("🚀 Iniciando migración de base de datos para sistema de permisos avanzado")
    print("=" * 70)

    success = migrate_database()

    if success:
        verify_migration()
        print("\n" + "=" * 70)
        print("🎉 ¡Migración completada exitosamente!")
        print("\n📋 Próximos pasos:")
        print("  1. Reinicia la aplicación: python run.py")
        print("  2. Accede como administrador para gestionar roles")
        print("  3. Asigna roles específicos a los usuarios")
        print("  4. Configura permisos de fila si es necesario")
        print("\n💾 Backup guardado en: instance/alcaldias_dev_backup.db")
    else:
        print("\n❌ La migración falló. Revisa los errores anteriores.")
        print("💾 Puedes restaurar desde: instance/alcaldias_dev_backup.db")
