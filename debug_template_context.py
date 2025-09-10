#!/usr/bin/env python3
"""
Script para debug del contexto del template de líneas
"""
from app import create_app
from app.models import PlanDesarrollo
from jinja2 import Template

def debug_template_context():
    """Debug del contexto del template"""
    print("🔧 Debug del contexto del template de líneas...")

    app = create_app()
    with app.app_context():
        plan = PlanDesarrollo.query.filter_by(estado='activo').first()
        if not plan:
            print("❌ No hay plan activo")
            return

        print(f"📋 Plan: {plan.titulo}")
        print(f"📊 Líneas: {len(plan.lineas_estrategicas)}")

        # Simular exactamente el código corregido del template
        template_code = '''
{% set total_presupuesto = namespace(value=0) %}
{% for linea in plan.lineas_estrategicas %}
    {% set presupuesto = linea.presupuesto_asignado or 0 %}
    {% set total_presupuesto.value = total_presupuesto.value + presupuesto %}
    Línea {{ linea.cod_linea }}: {{ presupuesto }} (Acumulado: {{ total_presupuesto.value }})
{% endfor %}
{% set total_presupuesto = total_presupuesto.value %}
Resultado final: ${{ "%.1f"|format(total_presupuesto / 1000) }}K
'''

        try:
            from jinja2 import Environment, BaseLoader
            env = Environment(loader=BaseLoader())
            template = env.from_string(template_code)

            result = template.render(plan=plan)
            print("📄 Resultado del template:")
            print(result)

        except Exception as e:
            print(f"❌ Error en template: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_template_context()
