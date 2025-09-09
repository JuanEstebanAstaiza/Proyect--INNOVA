#!/usr/bin/env python3
"""
Script para crear datos de ejemplo en el sistema de permisos avanzado
"""

from app import create_app, db
from app.models import (
    User, PlanDesarrollo, LineaEstrategica, Componente,
    Programa, Proyecto, IndicadorProducto, EjecucionTrimestral,
    Role, UserRole, ColumnPermission, RowPermission
)

def create_sample_data():
    """Crea datos de ejemplo para probar el sistema"""

    app = create_app()
    with app.app_context():
        print("🧪 Creando datos de ejemplo para el sistema...")
        print("=" * 60)

        try:
            # Verificar si ya existen datos
            existing_plans = PlanDesarrollo.query.count()
            if existing_plans > 0:
                print(f"⚠️ Ya existen {existing_plans} planes en el sistema.")
                response = input("¿Deseas continuar y agregar más datos? (s/N): ")
                if response.lower() != 's':
                    print("❌ Operación cancelada por el usuario.")
                    return False

            # Crear plan de desarrollo de ejemplo
            print("🏗️ Creando plan de desarrollo de ejemplo...")
            plan = PlanDesarrollo(
                titulo="Plan de Desarrollo Municipal 2024-2027",
                descripcion="Plan estratégico para el desarrollo sostenible del municipio",
                anio_inicio=2024,
                anio_fin=2027,
                presupuesto_total=5000000.00,
                prioridad="alta",
                municipio_id=1  # Asumiendo que el admin es el usuario 1
            )
            db.session.add(plan)
            db.session.commit()
            print(f"✅ Plan creado: {plan.titulo}")

            # Crear línea estratégica
            print("🏗️ Creando línea estratégica...")
            linea = LineaEstrategica(
                plan_id=plan.id,
                cod_linea=1,
                nombre="Desarrollo Económico Sostenible",
                descripcion="Fortalecimiento de la economía local y generación de empleo"
            )
            db.session.add(linea)
            db.session.commit()
            print(f"✅ Línea estratégica creada: {linea.nombre}")

            # Crear componente
            print("🏗️ Creando componente...")
            componente = Componente(
                linea_estrategica_id=linea.id,
                cod_componente=1.1,
                nombre="Fortalecimiento del Sector Productivo",
                descripcion="Apoyo a emprendedores y empresas locales"
            )
            db.session.add(componente)
            db.session.commit()
            print(f"✅ Componente creado: {componente.nombre}")

            # Crear programa
            print("🏗️ Creando programa...")
            programa = Programa(
                componente_id=componente.id,
                cod_programa="PDM-001",
                nombre="Programa de Apoyo a Emprendimientos",
                descripcion="Capacitación y financiamiento para nuevos emprendedores",
                dependencia_responsable="Dirección de Desarrollo Económico",
                bpim="BPIM-2024-001"
            )
            db.session.add(programa)
            db.session.commit()
            print(f"✅ Programa creado: {programa.nombre}")

            # Crear proyecto
            print("🏗️ Creando proyecto...")
            proyecto = Proyecto(
                programa_id=programa.id,
                nombre="Centro de Emprendimiento Municipal",
                descripcion="Instalación física para capacitación de emprendedores",
                presupuesto_asignado=150000.00,
                estado="activo"
            )
            db.session.add(proyecto)
            db.session.commit()
            print(f"✅ Proyecto creado: {proyecto.nombre}")

            # Crear indicador
            print("🏗️ Creando indicador...")
            indicador = IndicadorProducto(
                proyecto_id=proyecto.id,
                cod_indicador="IP-001",
                nombre="Número de emprendedores capacitados",
                descripcion="Total de emprendedores que completan el programa de capacitación",
                tipo_indicador="Resultado",
                sentido="positivo",
                tipologia="Cuantitativo",
                unidad="personas",
                linea_base=50.0,
                meta_cuatrienio=500.0,
                meta_2024=150.0
            )
            db.session.add(indicador)
            db.session.commit()
            print(f"✅ Indicador creado: {indicador.nombre}")

            # Crear ejecuciones trimestrales para 2024
            print("🏗️ Creando ejecuciones trimestrales...")
            ejecuciones_data = [
                {"trimestre": 1, "ejecucion": 35.0, "cumplimiento": 23.3, "poblacion": 35, "observacion": "Buen inicio del programa"},
                {"trimestre": 2, "ejecucion": 45.0, "cumplimiento": 30.0, "poblacion": 42, "observacion": "Incremento en participación"},
                {"trimestre": 3, "ejecucion": 38.0, "cumplimiento": 25.3, "poblacion": 38, "observacion": "Consolidación de resultados"},
                {"trimestre": 4, "ejecucion": 52.0, "cumplimiento": 34.7, "poblacion": 48, "observacion": "Cierre exitoso del año"}
            ]

            for ejec_data in ejecuciones_data:
                ejecucion = EjecucionTrimestral(
                    indicador_id=indicador.id,
                    anio=2024,
                    trimestre=ejec_data["trimestre"],
                    ejecucion_trimestral=ejec_data["ejecucion"],
                    cumplimiento_trimestral=ejec_data["cumplimiento"],
                    poblacion_impactada_trimestral=ejec_data["poblacion"],
                    observacion_trimestral=ejec_data["observacion"]
                )
                db.session.add(ejecucion)

            db.session.commit()
            print("✅ Ejecuciones trimestrales creadas (4 trimestres)")

            # Crear usuario adicional para pruebas de permisos
            print("👤 Creando usuario adicional para pruebas...")
            test_user = User.query.filter_by(username='usuario_prueba').first()
            if not test_user:
                test_user = User(
                    username='usuario_prueba',
                    email='usuario.prueba@alcaldia.gob.sv',
                    password='prueba123',
                    first_name='María',
                    last_name='González',
                    position='Técnico en Desarrollo',
                    municipality='Municipio Central',
                    department='San Salvador',
                    municipality_code='MC-001'
                )
                db.session.add(test_user)
                db.session.commit()
                print(f"✅ Usuario de prueba creado: {test_user.username}")
                print("   📧 Email: usuario.prueba@alcaldia.gob.sv")
                print("   🔑 Contraseña: prueba123")
                # Asignar rol de Editor de Ejecución al usuario de prueba
                editor_ejecucion = Role.query.filter_by(name='Editor de Ejecución').first()
                if editor_ejecucion:
                    user_role_assignment = UserRole(
                        user_id=test_user.id,
                        role_id=editor_ejecucion.id,
                        assigned_by=1,  # Admin
                        notes='Usuario de prueba para sistema de permisos'
                    )
                    db.session.add(user_role_assignment)
                    db.session.commit()
                    print(f"✅ Rol asignado: {editor_ejecucion.name}")

                    # Crear un permiso de fila específico para este usuario
                    row_permission = RowPermission(
                        user_id=test_user.id,
                        indicador_id=indicador.id,
                        can_edit=True,
                        search_term='emprendedores',
                        assigned_by=1
                    )
                    db.session.add(row_permission)
                    db.session.commit()
                    print("✅ Permiso de fila específico asignado")

            print("\n" + "=" * 60)
            print("🎉 ¡Datos de ejemplo creados exitosamente!")
            print("\n📋 Resumen de datos creados:")
            print(f"   • 1 Plan de Desarrollo: '{plan.titulo}'")
            print(f"   • 1 Línea Estratégica: '{linea.nombre}'")
            print(f"   • 1 Componente: '{componente.nombre}'")
            print(f"   • 1 Programa: '{programa.nombre}'")
            print(f"   • 1 Proyecto: '{proyecto.nombre}'")
            print(f"   • 1 Indicador: '{indicador.nombre}'")
            print("   • 4 Ejecuciones trimestrales (2024)")
            print("   • 1 Usuario adicional de prueba")
            print("   • 1 Asignación de rol específica")
            print("   • 1 Permiso de fila personalizado")

            print("\n🚀 Cuentas de usuario disponibles:")
            print("   👑 Administrador:")
            print("      • Usuario: admin")
            print("      • Email: admin@alcaldia.gob.sv")
            print("      • Permisos: Control total del sistema")
            print("\n   👤 Usuario de Prueba:")
            print("      • Usuario: usuario_prueba")
            print("      • Email: usuario.prueba@alcaldia.gob.sv")
            print("      • Contraseña: prueba123")
            print("      • Rol: Editor de Ejecución")
            print("      • Permiso especial: Puede editar el indicador de emprendedores")

            print("\n💡 Para probar el sistema:")
            print("   1. Inicia sesión como 'admin' para ver control total")
            print("   2. Inicia sesión como 'usuario_prueba' para ver permisos limitados")
            print("   3. Compara las diferencias en la Vista Excel")
            print("   4. Prueba el Panel de Administración (/admin)")

            return True

        except Exception as e:
            print(f"❌ Error creando datos de ejemplo: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = create_sample_data()
    if success:
        print("\n🎯 ¡Sistema listo para pruebas completas!")
    else:
        print("\n❌ Falló la creación de datos de ejemplo.")
