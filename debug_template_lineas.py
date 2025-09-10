#!/usr/bin/env python3
"""
Script para debug del template de líneas estratégicas
"""
from app import create_app
from app.models import PlanDesarrollo

def debug_template_lineas():
    """Debug del cálculo de presupuesto en el template de líneas"""
    print("🔧 Debug del template de líneas estratégicas...")

    app = create_app()
    with app.app_context():
        plan = PlanDesarrollo.query.filter_by(estado='activo').first()
        if not plan:
            print("❌ No hay plan activo")
            return

        print(f"📋 Plan: {plan.titulo}")
        print(f"📊 Líneas en plan.lineas_estrategicas: {len(plan.lineas_estrategicas)}")

        # Simular exactamente lo que hace el template
        total_presupuesto = 0
        print("\n🔄 Simulando cálculo del template:")

        for linea in plan.lineas_estrategicas:
            print(f"  Procesando línea {linea.cod_linea}: {linea.nombre[:30]}...")
            presupuesto_raw = linea.presupuesto_asignado
            presupuesto_or_0 = presupuesto_raw or 0

            print(f"    presupuesto_asignado raw: {repr(presupuesto_raw)}")
            print(f"    presupuesto_asignado or 0: {presupuesto_or_0}")

            total_presupuesto = total_presupuesto + presupuesto_or_0
            print(f"    total_presupuesto acumulado: {total_presupuesto}")

        total_en_k = total_presupuesto / 1000 if total_presupuesto > 0 else 0
        print(f"\n💰 Resultado final:")
        print(f"  Total presupuesto: ${total_presupuesto:,.0f}")
        print(f"  Total en K: ${total_en_k:,.1f}K")
        print(f"  Formateado: ${{ '%.1f'|format(total_en_k) }}K")

if __name__ == "__main__":
    debug_template_lineas()
