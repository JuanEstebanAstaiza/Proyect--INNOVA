#!/usr/bin/env python3
"""
Script para corregir la tabla de permisos de fila
"""

import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db

def fix_row_permissions_table():
    """Corregir la tabla de permisos de fila"""
    app = create_app()
    app.app_context().push()

    print("🔧 CORRIGIENDO TABLA DE PERMISOS DE FILA")
    print("=" * 60)

    try:
        with db.engine.connect() as conn:
            # Eliminar tabla existente si existe
            print("🗑️  Eliminando tabla existente...")
            conn.execute(db.text("DROP TABLE IF EXISTS row_permissions"))
            conn.commit()
            print("✅ Tabla eliminada")

            # Crear tabla con el esquema correcto
            print("\n🏗️  Creando tabla con esquema correcto...")
            create_table_sql = """
            CREATE TABLE row_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_id INTEGER NOT NULL,
                indicador_id INTEGER,
                proyecto_id INTEGER,
                programa_id INTEGER,
                componente_id INTEGER,
                linea_estrategica_id INTEGER,
                can_view BOOLEAN DEFAULT 1,
                can_edit BOOLEAN DEFAULT 0,
                permission_scope VARCHAR(50) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                assigned_by INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (plan_id) REFERENCES planes_desarrollo (id),
                FOREIGN KEY (indicador_id) REFERENCES indicadores_producto (id),
                FOREIGN KEY (proyecto_id) REFERENCES proyectos (id),
                FOREIGN KEY (programa_id) REFERENCES programas (id),
                FOREIGN KEY (componente_id) REFERENCES componentes (id),
                FOREIGN KEY (linea_estrategica_id) REFERENCES lineas_estrategicas (id),
                FOREIGN KEY (assigned_by) REFERENCES users (id)
            )
            """
            conn.execute(db.text(create_table_sql))
            conn.commit()
            print("✅ Tabla creada con esquema correcto")

            # Verificar columnas
            result = conn.execute(db.text("PRAGMA table_info(row_permissions)"))
            columns = result.fetchall()

            print(f"\n📋 TABLA CREADA CON {len(columns)} COLUMNAS:")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                nullable = "NULL" if col[3] else "NOT NULL"
                default = col[4] if col[4] else ""
                print(f"   ✅ {col_name} ({col_type}) {nullable} {default}".strip())

            # Verificar foreign keys
            result = conn.execute(db.text("PRAGMA foreign_key_list(row_permissions)"))
            fks = result.fetchall()

            print(f"\n🔗 FOREIGN KEYS CREADAS ({len(fks)}):")
            for fk in fks:
                print(f"   ✅ {fk[3]} → {fk[2]}.{fk[4]}")

            return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = fix_row_permissions_table()
    if success:
        print("\n🎉 ¡Tabla corregida exitosamente!")
        print("Ahora puedes ejecutar las pruebas del sistema de permisos de fila.")
    else:
        print("\n❌ Error al corregir la tabla.")
