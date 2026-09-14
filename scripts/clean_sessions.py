#!/usr/bin/env python3
"""
Script para limpiar todas las sesiones activas e inactivas de la base de datos
Esto es útil para probar el panel de monitoreo de sesiones con un estado limpio
"""

from app import create_app, db
from app.models import ActiveSession, User

def clean_all_sessions():
    """Elimina todas las sesiones activas e inactivas"""

    app = create_app()
    with app.app_context():
        print("🧹 Limpiando todas las sesiones de la base de datos...")
        print("=" * 60)

        try:
            # Contar sesiones antes de limpiar
            total_sessions = ActiveSession.query.count()
            active_sessions = ActiveSession.query.filter_by(is_active=True).count()
            inactive_sessions = ActiveSession.query.filter_by(is_active=False).count()

            print("📊 Estado actual de sesiones:")
            print(f"   • Total de sesiones: {total_sessions}")
            print(f"   • Sesiones activas: {active_sessions}")
            print(f"   • Sesiones inactivas: {inactive_sessions}")

            if total_sessions == 0:
                print("\n✅ No hay sesiones para limpiar. La base de datos ya está limpia.")
                return True

            # Mostrar sesiones por usuario antes de limpiar
            print("\n👥 Sesiones por usuario:")
            user_sessions = db.session.query(
                User.username,
                db.func.count(ActiveSession.id).label('session_count')
            ).join(ActiveSession).group_by(User.username).all()

            for username, count in user_sessions:
                print(f"   • {username}: {count} sesiones")

            # Confirmar antes de proceder
            print("\n⚠️  ATENCIÓN:")
            print("   Esta acción eliminará TODAS las sesiones activas e inactivas.")
            print("   Los usuarios podrán seguir iniciando sesión normalmente.")
            print("   Solo se perderá el historial de sesiones actuales.")
            response = input("\n¿Está seguro de que desea continuar? (sí/no): ")

            if response.lower() not in ['sí', 'si', 's', 'yes', 'y']:
                print("\n❌ Operación cancelada por el usuario.")
                return False

            # Eliminar todas las sesiones
            print("\n🗑️  Eliminando sesiones...")
            deleted_count = ActiveSession.query.delete()

            # Confirmar cambios
            db.session.commit()

            print("\n✅ Limpieza completada exitosamente!")
            print(f"   • Sesiones eliminadas: {deleted_count}")

            # Verificar que se eliminaron todas
            remaining_sessions = ActiveSession.query.count()
            print(f"   • Sesiones restantes: {remaining_sessions}")

            if remaining_sessions == 0:
                print("\n🎉 Base de datos completamente limpia de sesiones!")
                print("\n💡 Próximos pasos:")
                print("   1. Reinicia la aplicación si es necesario")
                print("   2. Inicia sesión con cualquier usuario")
                print("   3. Ve al panel de administración (/admin/sessions)")
                print("   4. Observa el panel completamente limpio")
                print("   5. El sistema comenzará a registrar nuevas sesiones automáticamente")
                return True
            else:
                print(f"\n⚠️  Advertencia: Aún quedan {remaining_sessions} sesiones en la base de datos.")
                return False

        except Exception as e:
            print(f"\n❌ Error durante la limpieza: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

def clean_old_sessions(days=7):
    """Elimina sesiones inactivas más antiguas que X días"""

    app = create_app()
    with app.app_context():
        print(f"🧹 Limpiando sesiones inactivas más antiguas de {days} días...")
        print("=" * 60)

        try:
            from datetime import datetime, timedelta

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Contar sesiones que serán eliminadas
            old_sessions = ActiveSession.query.filter(
                ActiveSession.last_activity < cutoff_date
            ).count()

            print(f"📊 Sesiones inactivas a eliminar: {old_sessions}")

            if old_sessions == 0:
                print("✅ No hay sesiones antiguas para limpiar.")
                return True

            # Eliminar sesiones antiguas
            deleted_count = ActiveSession.query.filter(
                ActiveSession.last_activity < cutoff_date
            ).delete()

            db.session.commit()

            print("\n✅ Limpieza de sesiones antiguas completada!")
            print(f"   • Sesiones eliminadas: {deleted_count}")

            return True

        except Exception as e:
            print(f"\n❌ Error durante la limpieza: {str(e)}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("🧹 SCRIPT DE LIMPIEZA DE SESIONES")
    print("=" * 60)
    print("Opciones disponibles:")
    print("1. Limpiar TODAS las sesiones (activas e inactivas)")
    print("2. Limpiar solo sesiones antiguas (> 7 días)")
    print("3. Cancelar")

    choice = input("\nSeleccione una opción (1-3): ").strip()

    if choice == '1':
        success = clean_all_sessions()
        if success:
            print("\n🎯 Sistema listo para pruebas con panel completamente limpio!")
        status = "SUCCESS" if success else "FAILED"
    elif choice == '2':
        days = input("¿Cuántos días de antigüedad? (por defecto 7): ").strip()
        days = int(days) if days.isdigit() else 7
        success = clean_old_sessions(days)
        if success:
            print(f"\n🎯 Sesiones antiguas (> {days} días) eliminadas exitosamente!")
        status = "SUCCESS" if success else "FAILED"
    else:
        print("\n❌ Operación cancelada.")
        status = "CANCELLED"

    print("\n" + "=" * 60)
    print(f"Operación: {status}")
