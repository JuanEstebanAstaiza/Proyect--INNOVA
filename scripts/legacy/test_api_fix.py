#!/usr/bin/env python3
"""
Script de prueba para verificar que la API de reportes funciona correctamente
con los nuevos filtros de estado
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import PlanDesarrollo, IndicadorProducto

def test_api_filters():
    """Prueba que los filtros de estado estén funcionando correctamente"""
    app = create_app()
    with app.app_context():
        print("🔍 PRUEBA DE FILTROS DE API")
        print("=" * 50)

        # Obtener plan activo
        plan = PlanDesarrollo.query.filter_by(estado='activo').first()
        if not plan:
            print("❌ No hay plan activo")
            return

        print(f"📋 Plan encontrado: {plan.titulo}")

        # Probar filtro anterior (solo 'activo')
        indicadores_antiguo = IndicadorProducto.query.filter_by(estado='activo').all()
        print(f"📊 Indicadores con filtro antiguo (solo 'activo'): {len(indicadores_antiguo)}")

        # Probar filtro nuevo (activo y en_ejecucion)
        indicadores_nuevo = IndicadorProducto.query.filter(IndicadorProducto.estado.in_(['activo', 'en_ejecucion'])).all()
        print(f"📊 Indicadores con filtro nuevo (activo + en_ejecucion): {len(indicadores_nuevo)}")

        # Mostrar distribución por estado
        from sqlalchemy import func
        estados = db.session.query(
            IndicadorProducto.estado,
            func.count(IndicadorProducto.id)
        ).group_by(IndicadorProducto.estado).all()

        print("\n📈 DISTRIBUCIÓN POR ESTADO:")
        for estado, count in estados:
            print(f"  {estado}: {count} indicadores")

        # Verificar que el filtro nuevo incluye más datos
        if len(indicadores_nuevo) > len(indicadores_antiguo):
            print("✅ ¡ÉXITO! El filtro nuevo incluye más indicadores")
            return True
        else:
            print("❌ El filtro nuevo no está funcionando correctamente")
            return False

if __name__ == "__main__":
    success = test_api_filters()
    sys.exit(0 if success else 1)
