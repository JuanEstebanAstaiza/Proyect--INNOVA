#!/usr/bin/env python3
"""
Prueba de la API de reportes sin login para verificar funcionalidad
"""

from app import create_app
from app.models.user import User
from app.models.plan_desarrollo import PlanDesarrollo

app = create_app()

def test_api_sin_login():
    print("🧪 PRUEBA DE API SIN LOGIN (simulando usuario autenticado)")
    print("=" * 60)

    with app.app_context():
        # Obtener datos directamente sin login
        admin = User.query.filter_by(username='admin').first()
        plan = PlanDesarrollo.query.filter_by(municipio=admin, estado='activo').first()

        if not plan:
            print("❌ No hay plan activo")
            return

        print(f"✅ Plan encontrado: {plan.titulo} (ID: {plan.id})")

        # Simular la llamada a la API directamente sin cliente HTTP
        from app.views.planes import reportes_datos
        from flask import request

        # Crear un contexto de request simulado
        with app.test_request_context(f'/planes/{plan.id}/reportes/datos'):
            # Simular que el usuario está autenticado
            from flask_login import login_user
            login_user(admin)

            try:
                # Llamar directamente a la función de la API
                response_data = reportes_datos(plan.id)

                print("✅ API llamada exitosamente")
                print(f"Tipo de respuesta: {type(response_data)}")

                if hasattr(response_data, 'get_json'):
                    # Es una Response object
                    json_data = response_data.get_json()
                else:
                    # Es un dict directamente
                    json_data = response_data

                print(f"Success: {json_data.get('success')}")
                print(f"Plan título: {json_data.get('plan_titulo')}")
                print(f"Tipo análisis: {json_data.get('tipo_analisis')}")
                print(f"Indicadores: {len(json_data.get('indicadores', []))}")
                print(f"Tiene tendencias: {'Sí' if json_data.get('tendencias') else 'No'}")
                print(f"Tiene presupuesto: {'Sí' if json_data.get('presupuesto') else 'No'}")

                # Mostrar estructura completa
                print("\nKeys en respuesta:")
                print(f"  {list(json_data.keys())}")

                # Verificar indicadores
                indicadores = json_data.get('indicadores', [])
                if indicadores:
                    print(f"\nPrimer indicador:")
                    ind = indicadores[0]
                    print(f"  Nombre: {ind.get('nombre')}")
                    print(f"  Meta: {ind.get('meta_2024')}")
                    print(f"  Avance: {ind.get('avance')}")

                # Verificar tendencias
                tendencias = json_data.get('tendencias')
                if tendencias:
                    print(f"\nTendencias:")
                    print(f"  Labels: {tendencias.get('labels', [])[:3]}...")
                    datasets = tendencias.get('datasets', [])
                    if datasets:
                        print(f"  Dataset 1: {datasets[0].get('label')}")

                print("\n✅ API FUNCIONANDO CORRECTAMENTE")

            except Exception as e:
                print(f"❌ ERROR en API: {e}")
                import traceback
                traceback.print_exc()

if __name__ == '__main__':
    test_api_sin_login()
