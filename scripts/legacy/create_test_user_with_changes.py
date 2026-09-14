#!/usr/bin/env python3
"""
Script para crear un usuario de pruebas con cambios realizados para probar el panel de auditoría
"""
from app import create_app, db
from app.models import User, PlanDesarrollo, EditJustification, IndicadorProducto, Proyecto, Programa, Componente, LineaEstrategica
from audit_file_system import create_audit_file
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

def create_test_user_with_changes():
    """Crear usuario de pruebas con cambios realizados"""
    print("🧪 Creando usuario de pruebas con cambios para auditoría...")

    with create_app().app_context():
        try:
            # Crear usuario de pruebas
            test_username = "auditor_pruebas"
            test_email = "auditor.pruebas@example.com"
            test_password = "auditor123"

            # Verificar si el usuario ya existe
            existing_user = User.query.filter_by(username=test_username).first()
            if existing_user:
                print(f"✅ Usuario de pruebas ya existe: {test_username}")
                test_user = existing_user
            else:
                # Crear nuevo usuario
                test_user = User(
                    username=test_username,
                    email=test_email,
                    password_hash=generate_password_hash(test_password),
                    first_name="Auditor",
                    last_name="de Pruebas",
                    position="Auditor de Pruebas",
                    municipality="Municipio de Pruebas",
                    department="Departamento de Pruebas",
                    municipality_code="TEST-001",
                    is_active=True,
                    legacy_role="editor"
                )
                db.session.add(test_user)
                db.session.flush()
                print(f"✅ Usuario de pruebas creado: {test_username}")
                print(f"   📧 Email: {test_email}")
                print(f"   🔑 Password: {test_password}")

            # Obtener plan activo
            active_plan = PlanDesarrollo.query.filter_by(estado='activo').first()
            if not active_plan:
                print("❌ No hay plan activo")
                return False

            print(f"✅ Plan activo: {active_plan.titulo}")

            # Crear estructura básica si no existe
            indicador = IndicadorProducto.query.join(Proyecto).join(Programa).join(Componente).join(LineaEstrategica).filter(LineaEstrategica.plan_id == active_plan.id).first()
            if not indicador:
                print("📝 Creando estructura básica para pruebas...")

                # Crear línea estratégica
                linea = LineaEstrategica(
                    plan_id=active_plan.id,
                    cod_linea=99,
                    nombre="Línea Estratégica de Pruebas",
                    presupuesto_asignado=500000.0
                )
                db.session.add(linea)
                db.session.flush()

                # Crear componente
                componente = Componente(
                    linea_estrategica_id=linea.id,
                    cod_componente="99.1",
                    nombre="Componente de Pruebas",
                    presupuesto_asignado=250000.0
                )
                db.session.add(componente)
                db.session.flush()

                # Crear programa
                programa = Programa(
                    componente_id=componente.id,
                    cod_programa="TEST-001",
                    nombre="Programa de Pruebas",
                    dependencia_responsable="Departamento de Pruebas",
                    presupuesto_asignado=150000.0
                )
                db.session.add(programa)
                db.session.flush()

                # Crear proyecto
                proyecto = Proyecto(
                    programa_id=programa.id,
                    nombre="Proyecto de Auditoría de Pruebas",
                    presupuesto_total=100000.0
                )
                db.session.add(proyecto)
                db.session.flush()

                # Crear indicador
                indicador = IndicadorProducto(
                    proyecto_id=proyecto.id,
                    cod_indicador="TEST-001",
                    nombre="Indicador de Pruebas de Auditoría",
                    tipo_indicador="Resultado",
                    linea_base=25.0,
                    sentido="positivo",
                    tipologia="Cuantitativo",
                    unidad="unidades",
                    meta_cuatrienio=200.0,
                    meta_2024=75.0
                )
                db.session.add(indicador)
                db.session.flush()

                print("✅ Estructura de pruebas creada")

            # Crear cambios de ejemplo para el usuario de pruebas
            sample_changes = [
                {
                    'column_name': 'meta_2024',
                    'old_value': '50.0',
                    'new_value': '75.0',
                    'justification': 'Ajuste de meta basado en análisis de capacidad operativa. Se incrementa la meta considerando la mejora en procesos y recursos disponibles para el proyecto.',
                    'days_ago': 1,
                    'support_file': 'analisis_capacidad.pdf'
                },
                {
                    'column_name': 'linea_base',
                    'old_value': '20.0',
                    'new_value': '25.0',
                    'justification': 'Corrección de línea base basada en datos históricos más precisos del año anterior. Los nuevos datos provienen del sistema de información municipal.',
                    'days_ago': 3,
                    'support_file': 'datos_historicos.xlsx'
                },
                {
                    'column_name': 'unidad',
                    'old_value': 'items',
                    'new_value': 'unidades',
                    'justification': 'Homologación de unidades de medida según estándares municipales. Esta corrección mejora la consistencia en los reportes.',
                    'days_ago': 5,
                    'support_file': 'estandares_medicion.docx'
                },
                {
                    'column_name': 'meta_cuatrienio',
                    'old_value': '150.0',
                    'new_value': '200.0',
                    'justification': 'Actualización de meta cuatrienal considerando proyecciones de crecimiento realistas y recursos adicionales aprobados por la dirección.',
                    'days_ago': 7,
                    'support_file': 'proyecciones_2027.pdf'
                },
                {
                    'column_name': 'sentido',
                    'old_value': 'negativo',
                    'new_value': 'positivo',
                    'justification': 'Corrección del sentido del indicador. Al ser un indicador de resultados positivos, debe tener sentido positivo para reflejar correctamente el progreso.',
                    'days_ago': 10,
                    'support_file': 'metodologia_indicadores.pdf'
                }
            ]

            created_changes = 0
            for i, change_data in enumerate(sample_changes):
                # Calcular fecha del cambio
                change_date = datetime.now() - timedelta(days=change_data['days_ago'])

                # Crear archivo de soporte simulado
                support_file_path = None
                if change_data.get('support_file'):
                    # Simular la creación de un archivo de soporte
                    support_file_path = f"uploads/justifications/{change_date.strftime('%Y%m%d')}_{test_user.id}_{change_data['support_file']}"

                # Crear justificación
                edit_justification = EditJustification(
                    plan_id=active_plan.id,
                    indicador_id=indicador.id if indicador else None,
                    column_name=change_data['column_name'],
                    old_value=change_data['old_value'],
                    new_value=change_data['new_value'],
                    justification=change_data['justification'],
                    support_file_path=support_file_path,
                    user_id=test_user.id,
                    created_at=change_date
                )

                db.session.add(edit_justification)
                db.session.flush()

                # Crear archivo de auditoría
                audit_file_path = create_audit_file(edit_justification)
                if audit_file_path:
                    print(f"✅ Archivo de auditoría creado: {audit_file_path}")

                created_changes += 1

            db.session.commit()

            # Crear resumen de auditoría
            from audit_file_system import create_user_audit_summary
            summary_path = create_user_audit_summary(test_user.id)
            if summary_path:
                print(f"✅ Resumen de auditoría creado: {summary_path}")

            print(f"\n🎯 Usuario de Pruebas Creado Exitosamente!")
            print(f"👤 Usuario: {test_username}")
            print(f"📧 Email: {test_email}")
            print(f"🔑 Password: {test_password}")
            print(f"📊 Cambios realizados: {created_changes}")
            print(f"📁 Archivos de auditoría generados: {created_changes + 1}")  # +1 por el resumen

            print(f"\n🔗 Accede al panel de auditoría:")
            print(f"1. Inicia sesión con las credenciales arriba")
            print(f"2. Ve al menú usuario → 'Panel de Auditoría'")
            print(f"3. O accede directamente a: /audit/")

            return True

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creando usuario de pruebas: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    if create_test_user_with_changes():
        print("\n🎊 ¡Usuario de pruebas listo para usar!")
        print("Ahora puedes iniciar sesión y ver el panel de auditoría con datos reales.")
    else:
        print("\n❌ Error al crear el usuario de pruebas.")
