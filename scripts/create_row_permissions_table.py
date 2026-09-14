#!/usr/bin/env python3
"""
Script para crear la tabla de permisos de fila
"""

import os
import sys

# Agregar el directorio raíz al path
# La raíz del proyecto es el directorio padre de scripts/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import RowPermission


def create_row_permissions_table():
    """Crear la tabla de permisos de fila"""
    app = create_app()
    app.app_context().push()

    print("🔧 CREANDO TABLA DE PERMISOS DE FILA")
    print("=" * 50)

    try:
        # Crear la tabla
        RowPermission.__table__.create(db.engine, checkfirst=True)
        print("✅ Tabla 'row_permissions' creada exitosamente")

        # Verificar que se creó correctamente
        with db.engine.connect() as conn:
            result = conn.execute(db.text("PRAGMA table_info(row_permissions)"))
            columns = result.fetchall()

        print(f"✅ Tabla creada con {len(columns)} columnas:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")

        print("\n📋 COLUMNAS CREADAS:")
        print("   - id (INTEGER PRIMARY KEY)")
        print("   - user_id (INTEGER, FK to users)")
        print("   - plan_id (INTEGER, FK to planes_desarrollo)")
        print("   - indicador_id (INTEGER, FK to indicadores_producto, nullable)")
        print("   - proyecto_id (INTEGER, FK to proyectos, nullable)")
        print("   - programa_id (INTEGER, FK to programas, nullable)")
        print("   - componente_id (INTEGER, FK to componentes, nullable)")
        print("   - linea_estrategica_id (INTEGER, FK to lineas_estrategicas, nullable)")
        print("   - can_view (BOOLEAN, default True)")
        print("   - can_edit (BOOLEAN, default False)")
        print("   - permission_scope (VARCHAR(50))")
        print("   - description (TEXT, nullable)")
        print("   - is_active (BOOLEAN, default True)")
        print("   - created_at (DATETIME)")
        print("   - updated_at (DATETIME)")
        print("   - assigned_by (INTEGER, FK to users)")

        print("\n🎯 FUNCIONALIDAD:")
        print("   - Permite asignar permisos específicos de fila a usuarios")
        print("   - Soporta diferentes tipos de entidades (indicadores, proyectos, etc.)")
        print("   - Vinculado a planes específicos")
        print("   - Control de permisos de vista y edición")

    except Exception as e:
        print(f"❌ Error creando tabla: {e!s}")
        return False

    print("\n✅ TABLA DE PERMISOS DE FILA CREADA EXITOSAMENTE")
    return True

if __name__ == "__main__":
    success = create_row_permissions_table()
    if success:
        print("\n🎉 ¡El sistema de permisos de fila está listo para usar!")
        print("Ahora puedes ejecutar el script de pruebas.")
    else:
        print("\n❌ Error al crear la tabla. Revisa los logs anteriores.")
