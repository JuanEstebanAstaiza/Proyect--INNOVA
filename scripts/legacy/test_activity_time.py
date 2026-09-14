#!/usr/bin/env python3
"""
Script para probar el cálculo de tiempo de actividad
"""

import os
import sys
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import ActiveSession, User

def test_activity_calculation():
    """Probar el cálculo de tiempo de actividad"""
    app = create_app()
    app.app_context().push()

    print("🧪 PRUEBA DE CÁLCULO DE TIEMPO DE ACTIVIDAD")
    print("=" * 50)

    # Obtener usuario admin
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        print("❌ Usuario admin no encontrado")
        return

    # Obtener sesiones activas del admin
    sessions = ActiveSession.query.filter_by(
        user_id=admin.id,
        is_active=True
    ).all()

    if not sessions:
        print("❌ No hay sesiones activas para el usuario admin")
        return

    print(f"✅ Encontradas {len(sessions)} sesiones activas para {admin.username}")
    print()

    for i, session in enumerate(sessions, 1):
        print(f"📊 SESIÓN {i}:")
        print(f"   ID de sesión: {session.session_id}")
        print(f"   Usuario: {session.user.username if session.user else 'N/A'}")
        print(f"   Login time: {session.login_time}")
        print(f"   Last activity: {session.last_activity}")
        print()

        # Calcular tiempos
        now = datetime.utcnow()
        active_duration = session.get_active_duration()
        inactive_duration = session.get_inactive_duration()

        print("⏱️  CÁLCULOS:")
        print(f"   Hora actual: {now}")
        print(".1f")
        print(".1f")
        print()

        # Verificar cálculos manualmente
        login_delta = now - session.login_time
        activity_delta = now - session.last_activity

        manual_active_minutes = login_delta.total_seconds() / 60
        manual_inactive_minutes = activity_delta.total_seconds() / 60

        print("🔍 VERIFICACIÓN MANUAL:")
        print(".1f")
        print(".1f")
        print()

        # Comparar con cálculos del modelo
        active_diff = abs(active_duration - manual_active_minutes)
        inactive_diff = abs(inactive_duration - manual_inactive_minutes)

        print("⚖️  COMPARACIÓN:")
        print(".3f")
        print(".3f")

        if active_diff < 0.1 and inactive_diff < 0.1:
            print("✅ CÁLCULOS CORRECTOS")
        else:
            print("❌ DIFERENCIAS SIGNIFICATIVAS")
        print()

        # Información adicional
        print("📋 INFORMACIÓN ADICIONAL:")
        print(f"   Estado: {'Activa' if session.is_active else 'Inactiva'}")
        print(f"   JWT válido: {session.validate_jwt()}")
        print(f"   JWT expirado: {session.is_jwt_expired()}")
        print(f"   Es inactiva (>20min): {session.is_inactive()}")
        print()

    print("🎯 RESUMEN:")
    print("=" * 50)
    print("Si los cálculos son correctos, el problema estaba en el template")
    print("que usaba get_inactive_duration() en lugar de get_active_duration().")
    print()
    print("Los cambios realizados:")
    print("1. ✅ Agregado método get_active_duration() al modelo")
    print("2. ✅ Actualizado template para usar get_active_duration()")
    print("3. ✅ Ahora debería mostrar el tiempo real de actividad")

if __name__ == "__main__":
    test_activity_calculation()
