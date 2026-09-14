#!/usr/bin/env python3
"""
Script para verificar el esquema de la tabla row_permissions
"""

import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db

def check_table_schema():
    """Verificar el esquema de la tabla row_permissions"""
    app = create_app()
    app.app_context().push()

    print("🔍 VERIFICANDO ESQUEMA DE TABLA ROW_PERMISSIONS")
    print("=" * 60)

    try:
        with db.engine.connect() as conn:
            # Verificar si la tabla existe
            result = conn.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='row_permissions'"))
            if not result.fetchone():
                print("❌ La tabla 'row_permissions' no existe")
                return False

            print("✅ Tabla 'row_permissions' encontrada")

            # Obtener información de las columnas
            result = conn.execute(db.text("PRAGMA table_info(row_permissions)"))
            columns = result.fetchall()

            print(f"\n📋 COLUMNAS ENCONTRADAS ({len(columns)}):")
            print("-" * 40)

            expected_columns = [
                'id', 'user_id', 'plan_id', 'indicador_id', 'proyecto_id',
                'programa_id', 'componente_id', 'linea_estrategica_id',
                'can_view', 'can_edit', 'permission_scope', 'description',
                'is_active', 'created_at', 'updated_at', 'assigned_by'
            ]

            found_columns = []
            missing_columns = []

            for col in columns:
                col_name = col[1]
                col_type = col[2]
                found_columns.append(col_name)
                print(f"   ✅ {col_name} ({col_type})")

            print(f"\n🔍 ANÁLISIS:")
            print(f"   Columnas encontradas: {len(found_columns)}")
            print(f"   Columnas esperadas: {len(expected_columns)}")

            # Verificar columnas faltantes
            for expected_col in expected_columns:
                if expected_col not in found_columns:
                    missing_columns.append(expected_col)
                    print(f"   ❌ COLUMNA FALTANTE: {expected_col}")

            if missing_columns:
                print(f"\n❌ FALTAN {len(missing_columns)} COLUMNAS:")
                for col in missing_columns:
                    print(f"   - {col}")
                return False
            else:
                print("\n✅ TODAS LAS COLUMNAS ESTÁN PRESENTES")

            # Verificar índices/foreign keys
            print(f"\n🔗 VERIFICANDO RESTRICCIONES:")
            result = conn.execute(db.text("PRAGMA foreign_key_list(row_permissions)"))
            fks = result.fetchall()

            if fks:
                print(f"   ✅ Encontradas {len(fks)} foreign keys")
                for fk in fks:
                    print(f"      - {fk[3]} → {fk[2]}.{fk[4]}")
            else:
                print("   ⚠️  No se encontraron foreign keys (esto puede ser normal en SQLite)")

            return True

    except Exception as e:
        print(f"❌ Error verificando esquema: {str(e)}")
        return False

if __name__ == "__main__":
    success = check_table_schema()
    if not success:
        print("\n🔧 RECOMENDACIONES:")
        print("   1. Elimina la tabla existente:")
        print("      DROP TABLE IF EXISTS row_permissions;")
        print("   2. Vuelve a ejecutar el script de creación")
        print("   3. O ejecuta las migraciones de Flask-Migrate")
