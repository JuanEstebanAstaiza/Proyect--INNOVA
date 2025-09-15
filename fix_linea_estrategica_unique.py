#!/usr/bin/env python3
"""
Script para corregir la restricción UNIQUE en lineas_estrategicas.cod_linea
"""
from app import create_app, db
from sqlalchemy import text

def fix_unique_constraint():
    """Cambiar la restricción UNIQUE global por una restricción compuesta por plan"""
    print("🔧 Corrigiendo restricción UNIQUE en lineas_estrategicas.cod_linea...")

    try:
        with create_app().app_context():
            # Verificar el estado actual de la tabla
            result = db.session.execute(text("""
                SELECT sql FROM sqlite_master
                WHERE type='table' AND name='lineas_estrategicas'
            """)).fetchone()

            if result:
                print("📋 Estructura actual de la tabla:")
                print(result[0])

            # Crear una nueva tabla con la estructura corregida
            print("\n📝 Creando nueva estructura...")

            # Paso 1: Crear tabla temporal con la nueva estructura
            db.session.execute(text("""
                CREATE TABLE lineas_estrategicas_temp (
                    id INTEGER PRIMARY KEY,
                    cod_linea INTEGER NOT NULL,
                    nombre VARCHAR(200) NOT NULL,
                    descripcion TEXT,
                    plan_id INTEGER NOT NULL,
                    estado VARCHAR(20) DEFAULT 'activo',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    prioridad VARCHAR(20) DEFAULT 'media',
                    presupuesto_asignado REAL DEFAULT 0.0,
                    FOREIGN KEY (plan_id) REFERENCES planes_desarrollo (id),
                    UNIQUE(plan_id, cod_linea)
                )
            """))

            # Paso 2: Copiar datos de la tabla original
            print("📋 Copiando datos existentes...")
            db.session.execute(text("""
                INSERT INTO lineas_estrategicas_temp
                SELECT id, cod_linea, nombre, descripcion, plan_id, estado, created_at, updated_at, prioridad, presupuesto_asignado
                FROM lineas_estrategicas
            """))

            # Paso 3: Eliminar tabla original
            print("🗑️ Eliminando tabla original...")
            db.session.execute(text("DROP TABLE lineas_estrategicas"))

            # Paso 4: Renombrar tabla temporal
            print("📝 Renombrando tabla temporal...")
            db.session.execute(text("ALTER TABLE lineas_estrategicas_temp RENAME TO lineas_estrategicas"))

            # Confirmar cambios
            db.session.commit()

            print("✅ Restricción UNIQUE corregida exitosamente")
            print("✅ Ahora se permite cod_linea duplicado por plan diferente")

            # Verificar la nueva estructura
            result = db.session.execute(text("""
                SELECT sql FROM sqlite_master
                WHERE type='table' AND name='lineas_estrategicas'
            """)).fetchone()

            if result:
                print("\n📋 Nueva estructura de la tabla:")
                print(result[0])

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al corregir la restricción UNIQUE: {e}")
        return False

    return True

if __name__ == "__main__":
    if fix_unique_constraint():
        print("\n🎊 ¡Restricción UNIQUE corregida exitosamente!")
        print("Ahora puedes importar Excels con códigos de línea duplicados en diferentes planes.")
    else:
        print("\n❌ Falló la corrección de la restricción UNIQUE.")
