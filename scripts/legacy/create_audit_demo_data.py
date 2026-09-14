#!/usr/bin/env python3
"""
Script para crear datos de ejemplo para el panel de auditoría
"""
from app import create_app, db
from app.models import User, PlanDesarrollo, EditJustification, IndicadorProducto
from audit_file_system import create_audit_file
from datetime import datetime, timedelta
import random

def create_demo_audit_data():
    """Crear datos de ejemplo para el panel de auditoría"""
    print("🎭 Creando datos de ejemplo para auditoría...")

    with create_app().app_context():
        try:
            # Obtener usuarios y plan activo
            users = User.query.all()
            active_plan = PlanDesarrollo.query.filter_by(estado='activo').first()

            if not users:
                print("❌ No hay usuarios en el sistema")
                return False

            if not active_plan:
                print("❌ No hay plan activo")
                return False

            print(f"✅ Usuarios encontrados: {len(users)}")
            print(f"✅ Plan activo: {active_plan.titulo}")

            # Crear algunos indicadores de ejemplo si no existen
            if not IndicadorProducto.query.filter_by(plan_id=active_plan.id).first():
                from app.models import Proyecto, Programa, Componente, LineaEstrategica

                # Crear línea estratégica
                linea = LineaEstrategica(
                    plan_id=active_plan.id,
                    cod_linea=1,
                    nombre="Desarrollo Económico Sostenible",
                    presupuesto_asignado=1000000.0
                )
                db.session.add(linea)
                db.session.flush()

                # Crear componente
                componente = Componente(
                    linea_estrategica_id=linea.id,
                    cod_componente="1.1",
                    nombre="Fortalecimiento del Sector Productivo",
                    presupuesto_asignado=500000.0
                )
                db.session.add(componente)
                db.session.flush()

                # Crear programa
                programa = Programa(
                    componente_id=componente.id,
                    cod_programa="PDM-001",
                    nombre="Programa de Apoyo a Emprendimientos",
                    dependencia_responsable="Dirección de Desarrollo Económico",
                    presupuesto_asignado=300000.0
                )
                db.session.add(programa)
                db.session.flush()

                # Crear proyecto
                proyecto = Proyecto(
                    programa_id=programa.id,
                    nombre="Centro de Emprendimiento Municipal",
                    presupuesto_total=200000.0
                )
                db.session.add(proyecto)
                db.session.flush()

                # Crear indicador
                indicador = IndicadorProducto(
                    proyecto_id=proyecto.id,
                    cod_indicador="IP-001",
                    nombre="Número de emprendedores capacitados",
                    tipo_indicador="Resultado",
                    linea_base=50.0,
                    sentido="positivo",
                    tipologia="Cuantitativo",
                    unidad="personas",
                    meta_cuatrienio=500.0,
                    meta_2024=150.0
                )
                db.session.add(indicador)
                db.session.flush()

                print("✅ Datos básicos creados para auditoría")

            # Obtener el indicador creado
            indicador = IndicadorProducto.query.filter_by(plan_id=active_plan.id).first()

            # Crear justificaciones de ejemplo para diferentes usuarios
            sample_changes = [
                {
                    'column_name': 'meta_2024',
                    'old_value': '120.0',
                    'new_value': '150.0',
                    'justification': 'Incremento de meta debido al aumento en la demanda de servicios y mejora en la capacidad operativa del proyecto. Los recursos adicionales han sido aprobados por la dirección municipal.',
                    'days_ago': 1
                },
                {
                    'column_name': 'linea_base',
                    'old_value': '40.0',
                    'new_value': '50.0',
                    'justification': 'Ajuste en la línea base basado en datos históricos más precisos del año anterior.',
                    'days_ago': 3
                },
                {
                    'column_name': 'unidad',
                    'old_value': 'unidades',
                    'new_value': 'personas',
                    'justification': 'Corrección de la unidad de medida para mayor claridad en el indicador.',
                    'days_ago': 5
                },
                {
                    'column_name': 'meta_cuatrienio',
                    'old_value': '400.0',
                    'new_value': '500.0',
                    'justification': 'Actualización de meta cuatrienal basada en proyecciones realistas del crecimiento esperado.',
                    'days_ago': 7
                }
            ]

            created_changes = 0
            for i, change_data in enumerate(sample_changes):
                # Seleccionar usuario aleatoriamente
                user = random.choice(users)

                # Calcular fecha del cambio
                change_date = datetime.now() - timedelta(days=change_data['days_ago'])

                # Crear justificación
                edit_justification = EditJustification(
                    plan_id=active_plan.id,
                    indicador_id=indicador.id if indicador else None,
                    column_name=change_data['column_name'],
                    old_value=change_data['old_value'],
                    new_value=change_data['new_value'],
                    justification=change_data['justification'],
                    user_id=user.id,
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
            print(f"✅ Creados {created_changes} cambios de ejemplo")
            print("✅ Datos de auditoría de ejemplo listos")

            return True

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creando datos de ejemplo: {e}")
            return False

if __name__ == "__main__":
    if create_demo_audit_data():
        print("\n🎊 ¡Datos de ejemplo creados exitosamente!")
        print("Ahora puedes acceder al panel de auditoría para ver los cambios registrados.")
    else:
        print("\n❌ Error al crear datos de ejemplo.")
