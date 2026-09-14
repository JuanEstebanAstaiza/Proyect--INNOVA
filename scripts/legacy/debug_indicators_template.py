#!/usr/bin/env python3
"""
Script para debug del template de indicadores corregido
"""
from app import create_app
from app.models import Proyecto
from jinja2 import Template

def debug_indicators_template():
    """Debug del cálculo de progreso promedio en indicadores"""
    print("🔧 Debug del template de indicadores corregido...")

    app = create_app()
    with app.app_context():
        proyecto = Proyecto.query.filter(Proyecto.indicadores.any()).first()

        if proyecto:
            print(f"🏗️ Proyecto: {proyecto.nombre}")
            print(f"📊 Indicadores: {len(proyecto.indicadores)}")

            # Simular el template corregido
            template_code = '''
{% set total_progreso = namespace(value=0) %}
{% set indicadores_validos = namespace(value=0) %}
{% for indicador in proyecto.indicadores %}
    {% set progreso_indicador = indicador.get_progreso_porcentual() %}
    {% if progreso_indicador and progreso_indicador > 0 %}
        {% set total_progreso.value = total_progreso.value + progreso_indicador %}
        {% set indicadores_validos.value = indicadores_validos.value + 1 %}
        Indicador: {{ indicador.nombre }} - Progreso: {{ progreso_indicador }}%
    {% endif %}
{% endfor %}
{% set promedio_progreso = total_progreso.value / indicadores_validos.value if indicadores_validos.value > 0 else 0 %}
Resultado: {{ "%.1f"|format(promedio_progreso) }}% promedio de {{ indicadores_validos.value }} indicadores válidos
'''

            try:
                from jinja2 import Environment, BaseLoader
                env = Environment(loader=BaseLoader())
                template = env.from_string(template_code)

                result = template.render(proyecto=proyecto)
                print("📄 Resultado del template:")
                print(result)

            except Exception as e:
                print(f"❌ Error en template: {e}")
                import traceback
                traceback.print_exc()

        else:
            print("❌ No se encontraron proyectos con indicadores")

if __name__ == "__main__":
    debug_indicators_template()
