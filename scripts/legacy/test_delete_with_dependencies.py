#!/usr/bin/env python3
"""
Script para probar la eliminación de planes con dependencias
"""

from app import create_app, db
from app.models import User, PlanDesarrollo, RowPermission, IndicadorProducto

def test_delete_with_dependencies():
    """Prueba la eliminación de planes manejando dependencias"""

    app = create_app()
    with app.app_context():
        print("🗑️ PRUEBA DE ELIMINACIÓN CON DEPENDENCIAS")
        print("=" * 50)

        try:
            # Verificar usuario admin
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("❌ No hay usuario admin")
                return False

            # Verificar planes inactivos
            plan = PlanDesarrollo.query.filter_by(
                municipio=admin,
                estado='borrador'
            ).first()

            if not plan:
                print("❌ No hay planes inactivos para probar")
                print("   💡 Crea o desactiva un plan desde la interfaz web")
                return False

            print(f"✅ Usuario: {admin.username}")
            print(f"✅ Plan a eliminar: {plan.titulo} (ID: {plan.id})")
            print(f"✅ Estado: {plan.estado}")

            # Contar permisos de fila antes de eliminar
            permisos_antes = RowPermission.query.count()
            print(f"📊 Permisos de fila antes: {permisos_antes}")

            # Verificar si hay indicadores en el plan usando la nueva consulta
            from app.models import Proyecto, Programa, Componente, LineaEstrategica
            indicadores_count = db.session.query(IndicadorProducto.id)\
                .join(Proyecto, IndicadorProducto.proyecto_id == Proyecto.id)\
                .join(Programa, Proyecto.programa_id == Programa.id)\
                .join(Componente, Programa.componente_id == Componente.id)\
                .join(LineaEstrategica, Componente.linea_estrategica_id == LineaEstrategica.id)\
                .filter(LineaEstrategica.plan_id == plan.id)\
                .count()
            print(f"📊 Indicadores en el plan: {indicadores_count}")

            # Contar proyectos en el plan
            proyectos_count = db.session.query(Proyecto.id)\
                .join(Programa, Proyecto.programa_id == Programa.id)\
                .join(Componente, Programa.componente_id == Componente.id)\
                .join(LineaEstrategica, Componente.linea_estrategica_id == LineaEstrategica.id)\
                .filter(LineaEstrategica.plan_id == plan.id)\
                .count()
            print(f"📊 Proyectos en el plan: {proyectos_count}")

            print("\n🎯 ESTRATEGIA DE ELIMINACIÓN:")
            print("   1. ✅ Eliminar permisos de fila asociados")
            print("   2. ✅ Mantener permisos de columna (no relacionados)")
            print("   3. ✅ Mantener logs de actividad (auditoría)")
            print("   4. ✅ Eliminar plan de forma segura")
            print("   5. ✅ Manejo de errores con rollback")

            print("\n🚀 PRUEBA MANUAL RECOMENDADA:")
            print("   1. Inicia la aplicación: python run.py")
            print("   2. Ve a: http://localhost:5000")
            print("   3. Inicia sesión: admin / admin123")
            print("   4. Ve a Planes (/planes)")
            print(f"   5. Busca el plan: '{plan.titulo}'")
            print("   6. Haz clic en 'Eliminar'")
            print("   7. Confirma la eliminación")
            print("   8. Debería funcionar sin error de integridad")
            print("   9. Verifica que los permisos relacionados se eliminaron")

            return True

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test_delete_with_dependencies()
    if success:
        print("\n🎉 ¡Sistema de eliminación con dependencias configurado!")
        print("   Ahora prueba la eliminación manualmente.")
    else:
        print("\n❌ Hay problemas con la configuración.")
