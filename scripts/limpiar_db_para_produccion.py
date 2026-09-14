#!/usr/bin/env python3
"""
Script para limpiar la base de datos y dejarla lista para producción
Elimina todos los datos pero mantiene la estructura de las tablas
"""

import os
import sys
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    User, Role, ColumnPermission, RowPermission, UserRole,
    PlanDesarrollo, LineaEstrategica, Componente, Programa,
    Proyecto, IndicadorProducto, Actividad, EjecucionTrimestral,
    Documento, EditJustification, ActivityLog, SMTPConfig, UserTempPassword
)

def limpiar_base_datos():
    """Limpia completamente la base de datos"""

    print("🧹 INICIANDO LIMPIEZA DE BASE DE DATOS PARA PRODUCCIÓN")
    print("=" * 60)

    try:
        with create_app().app_context():

            # Paso 1: Eliminar datos en orden inverso de dependencias
            print("\n📋 PASO 1: Eliminando datos existentes...")

            # Eliminar archivos físicos de documentos
            print("   🗂️ Eliminando archivos de documentos...")
            documentos = Documento.query.all()
            for doc in documentos:
                if doc.ruta_archivo and os.path.exists(doc.ruta_archivo):
                    try:
                        os.remove(doc.ruta_archivo)
                        print(f"      ✅ Eliminado: {os.path.basename(doc.ruta_archivo)}")
                    except Exception as e:
                        print(f"      ⚠️ Error eliminando {doc.ruta_archivo}: {e}")

            # Eliminar datos de las tablas en orden inverso de dependencias
            tablas_a_limpiar = [
                ('UserTempPassword', UserTempPassword),
                ('EditJustification', EditJustification),
                ('ActivityLog', ActivityLog),
                ('Documento', Documento),
                ('EjecucionTrimestral', EjecucionTrimestral),
                ('IndicadorProducto', IndicadorProducto),
                ('Actividad', Actividad),
                ('Proyecto', Proyecto),
                ('Programa', Programa),
                ('Componente', Componente),
                ('LineaEstrategica', LineaEstrategica),
                ('PlanDesarrollo', PlanDesarrollo),
                ('RowPermission', RowPermission),
                ('UserRole', UserRole),
                ('ColumnPermission', ColumnPermission),
                ('SMTPConfig', SMTPConfig),
                ('Role', Role),
                ('User', User)
            ]

            for nombre_tabla, modelo in tablas_a_limpiar:
                try:
                    cantidad = modelo.query.count()
                    if cantidad > 0:
                        modelo.query.delete()
                        print(f"   🗑️ {nombre_tabla}: {cantidad} registros eliminados")
                    else:
                        print(f"   ⏭️ {nombre_tabla}: sin registros")
                except Exception as e:
                    print(f"   ❌ Error en {nombre_tabla}: {e}")

            # Confirmar eliminación
            db.session.commit()
            print("\n✅ PASO 1 COMPLETADO: Todos los datos eliminados")

            # Paso 2: Crear roles básicos del sistema
            print("\n📋 PASO 2: Creando roles del sistema...")

            roles_basicos = [
                {'name': 'Administrador', 'description': 'Control total del sistema', 'is_system_role': True, 'color': '#dc3545'},
                {'name': 'Editor General', 'description': 'Edición completa de datos y documentos', 'is_system_role': True, 'color': '#28a745'},
                {'name': 'Editor de Ejecución', 'description': 'Edición de datos de ejecución', 'is_system_role': True, 'color': '#007bff'},
                {'name': 'Editor de Metas', 'description': 'Edición de metas y objetivos', 'is_system_role': True, 'color': '#ffc107'},
                {'name': 'Visualizador', 'description': 'Solo lectura', 'is_system_role': True, 'color': '#6c757d'}
            ]

            for rol_data in roles_basicos:
                rol = Role(
                    name=rol_data['name'],
                    description=rol_data['description'],
                    is_system_role=rol_data['is_system_role'],
                    color=rol_data['color'],
                    is_active=True
                )
                db.session.add(rol)
                print(f"   👥 Creado rol: {rol.name}")

            # Paso 3: Crear permisos de columna para cada rol
            print("\n📋 PASO 3: Creando permisos de columna...")

            columnas_sistema = [
                'cod_linea', 'lineas_estrategicas', 'cod_componente', 'componentes',
                'cod_programa', 'programa_pdm', 'dependencia_responsable', 'bpim',
                'nombre_proyecto', 'indicadores', 'cod_indicador_de_producto',
                'indicador_de_producto', 'tipo_de_indicador', 'linea_base', 'sentido',
                'tipologia', 'unidad', 'meta_cuatrienio', 'meta_2024',
                'ejecucion_1_trimestre', 'cumplimiento_1_trimestre', 'poblacion_impactada_1_trimestre', 'observacion_1_trimestre',
                'ejecucion_2_trimestre', 'cumplimiento_2_trimestre', 'poblacion_impactada_2_trimestre', 'observacion_2_trimestre',
                'ejecucion_3_trimestre', 'cumplimiento_3_trimestre', 'poblacion_impactada_3_trimestre', 'observacion_3_trimestre',
                'ejecucion_4_trimestre', 'cumplimiento_4_trimestre', 'poblacion_impactada_4_trimestre', 'observacion_4_trimestre',
                'ejecucion_acumulada', 'cumplimiento_acumulado', 'poblacion_impactada_acumulada', 'observacion_acumulada'
            ]

            roles = Role.query.all()
            for rol in roles:
                permisos_creados = 0
                for columna in columnas_sistema:
                    # Administrador puede editar todo
                    if rol.name == 'Administrador':
                        puede_editar = True
                        puede_ver = True
                    # Editores pueden editar según su especialización
                    elif 'Editor' in rol.name:
                        # Lógica específica para cada tipo de editor
                        if rol.name == 'Editor General':
                            puede_editar = True
                            puede_ver = True
                        elif rol.name == 'Editor de Ejecución':
                            puede_editar = columna.startswith(('ejecucion_', 'cumplimiento_', 'poblacion_', 'observacion_'))
                            puede_ver = True
                        elif rol.name == 'Editor de Metas':
                            puede_editar = columna.startswith(('meta_', 'linea_base', 'sentido', 'tipologia', 'unidad'))
                            puede_ver = True
                        else:
                            puede_editar = False
                            puede_ver = True
                    # Visualizador solo puede ver
                    else:
                        puede_editar = False
                        puede_ver = True

                    permiso = ColumnPermission(
                        role_id=rol.id,
                        column_name=columna,
                        can_edit=puede_editar,
                        can_view=puede_ver
                    )
                    db.session.add(permiso)
                    permisos_creados += 1

                print(f"   🔧 {rol.name}: {permisos_creados} permisos creados")

            # Paso 4: Crear usuario administrador
            print("\n📋 PASO 4: Creando usuario administrador...")

            from werkzeug.security import generate_password_hash

            admin_user = User(
                username='admin',
                email='admin@municipio.gob',
                password_hash=generate_password_hash('admin123'),
                first_name='Administrador',
                last_name='Sistema',
                position='Administrador del Sistema',
                municipality='Municipio Principal',
                department='Tecnología',
                municipality_code='MP001',
                legacy_role='admin',
                is_active=True
            )
            db.session.add(admin_user)

            # Asignar rol de Administrador
            admin_role = Role.query.filter_by(name='Administrador').first()
            if admin_role:
                user_role = UserRole(
                    user_id=admin_user.id,
                    role_id=admin_role.id,
                    is_active=True
                )
                db.session.add(user_role)

            print("   👤 Usuario administrador creado: admin / admin123")
            print("   📧 Email: admin@municipio.gob")

            # Paso 5: Crear plan de desarrollo básico
            print("\n📋 PASO 5: Creando plan de desarrollo básico...")

            plan = PlanDesarrollo(
                titulo='Plan de Desarrollo Municipal 2025-2027',
                descripcion='Plan estratégico para el desarrollo integral del municipio',
                anio_inicio=2025,
                anio_fin=2027,
                presupuesto_total=10000000.00,
                prioridad='alta',
                municipio_id=admin_user.id  # Asignar el usuario admin como municipio
            )
            db.session.add(plan)
            db.session.commit()  # Commit para obtener el ID del plan
            print("   📋 Plan creado: Plan de Desarrollo Municipal 2025-2027")

            # Crear línea estratégica básica
            linea = LineaEstrategica(
                cod_linea=1,
                nombre='Desarrollo Económico Sostenible',
                descripcion='Fortalecimiento de la economía local',
                presupuesto_asignado=3000000.00,
                prioridad='alta',
                plan_id=plan.id
            )
            db.session.add(linea)
            db.session.commit()  # Commit para obtener el ID
            print("   🏗️ Línea estratégica creada: Desarrollo Económico Sostenible")

            # Crear componente básico
            componente = Componente(
                cod_componente='1.1',
                nombre='Fortalecimiento del Sector Productivo',
                descripcion='Apoyo a emprendedores y empresas locales',
                presupuesto_asignado=1500000.00,
                prioridad='alta',
                linea_estrategica_id=linea.id
            )
            db.session.add(componente)
            db.session.commit()  # Commit para obtener el ID
            print("   🧩 Componente creado: Fortalecimiento del Sector Productivo")

            # Crear programa básico
            programa = Programa(
                cod_programa='PDM-001',
                nombre='Programa de Apoyo a Emprendimientos',
                descripcion='Capacitación y financiamiento para nuevos emprendedores',
                dependencia_responsable='Dirección de Desarrollo Económico',
                bpim='BPIM-2025-001',
                componente_id=componente.id
            )
            db.session.add(programa)
            db.session.commit()  # Commit para obtener el ID
            print("   📋 Programa creado: Programa de Apoyo a Emprendimientos")

            # Crear proyecto básico
            proyecto = Proyecto(
                nombre='Centro de Emprendimiento Municipal',
                descripcion='Instalación dedicada al desarrollo emprendedor',
                presupuesto_total=500000.00,
                ubicacion='Centro Histórico',
                sector='Desarrollo Económico',
                responsable_ejecucion='Juan Pérez',
                responsable_seguimiento='María González',
                programa_id=programa.id
            )
            db.session.add(proyecto)
            db.session.commit()  # Commit para obtener el ID
            print("   🎯 Proyecto creado: Centro de Emprendimiento Municipal")

            # Crear indicador básico
            indicador = IndicadorProducto(
                cod_indicador='IP-001',
                nombre='Número de emprendedores capacitados',
                descripcion='Total de emprendedores que reciben capacitación',
                tipo_indicador='Resultado',
                linea_base=50.0,
                sentido='positivo',
                tipologia='Cuantitativo',
                unidad='personas',
                meta_cuatrienio=500.0,
                meta_2024=150.0,
                proyecto_id=proyecto.id
            )
            db.session.add(indicador)
            db.session.commit()  # Commit final
            print("   📊 Indicador creado: Número de emprendedores capacitados")
            print("\n✅ PASO 5 COMPLETADO: Estructura básica creada")

            # Paso 6: Verificación final
            print("\n📋 PASO 6: Verificación final...")

            # Contar registros en cada tabla
            verificaciones = [
                ('Usuarios', User.query.count()),
                ('Roles', Role.query.count()),
                ('Permisos de columna', ColumnPermission.query.count()),
                ('Planes', PlanDesarrollo.query.count()),
                ('Líneas estratégicas', LineaEstrategica.query.count()),
                ('Componentes', Componente.query.count()),
                ('Programas', Programa.query.count()),
                ('Proyectos', Proyecto.query.count()),
                ('Indicadores', IndicadorProducto.query.count())
            ]

            print("\n📊 RESUMEN DE REGISTROS CREADOS:")
            for nombre, cantidad in verificaciones:
                print(f"   • {nombre}: {cantidad}")

            # Verificar que el directorio de uploads existe
            from flask import current_app
            upload_dir = current_app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir, exist_ok=True)
                print(f"\n📁 Directorio de uploads creado: {upload_dir}")
            else:
                print(f"\n📁 Directorio de uploads existente: {upload_dir}")

            print("\n🎉 ¡LIMPIEZA COMPLETADA EXITOSAMENTE!")
            print("=" * 60)
            print("✅ Base de datos limpia y lista para producción")
            print("✅ Estructura completa recreada")
            print("✅ Usuario administrador creado")
            print("✅ Plan básico configurado")
            print("✅ Roles y permisos establecidos")
            print()
            print("🔐 CREDENCIALES DE ACCESO:")
            print("   👤 Usuario: admin")
            print("   🔑 Contraseña: admin123")
            print("   📧 Email: admin@municipio.gob")
            print()
            print("🚀 URLs PARA ACCEDER:")
            print("   📱 Login: http://127.0.0.1:5000/login")
            print("   🏠 Dashboard: http://127.0.0.1:5000/dashboard")
            print("   📋 Plan: http://127.0.0.1:5000/planes/1/ver")
            print("   📁 Documentos: http://127.0.0.1:5000/planes/1/documentos")

    except Exception as e:
        print(f"\n❌ ERROR DURANTE LA LIMPIEZA: {e}")
        import traceback
        traceback.print_exc()

        # Manejar el rollback con cuidado para evitar errores de contexto
        try:
            db.session.rollback()
        except RuntimeError as rollback_error:
            if "Working outside of application context" in str(rollback_error):
                print("   ⚠️ Error de contexto durante rollback (esperado)")
            else:
                print(f"   ❌ Error durante rollback: {rollback_error}")

        return False

    return True

if __name__ == '__main__':
    print("⚠️  ADVERTENCIA: Esta acción eliminará TODOS los datos existentes")
    respuesta = input("¿Está seguro de que desea continuar? (escriba 'SI' para confirmar): ")

    if respuesta.upper() == 'SI':
        if limpiar_base_datos():
            print("\n🎊 Base de datos lista para producción y pruebas!")
        else:
            print("\n❌ Error durante la limpieza. Verifique los logs.")
    else:
        print("\n❌ Operación cancelada por el usuario.")
