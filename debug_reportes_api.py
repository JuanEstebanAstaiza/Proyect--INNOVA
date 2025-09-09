#!/usr/bin/env python3
"""
Script para debuggear la API de reportes
"""

from app import create_app
from app.models import User, PlanDesarrollo

app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    plan = PlanDesarrollo.query.filter_by(municipio=admin).first()

    if plan:
        print(f'Plan encontrado: {plan.titulo} (ID: {plan.id})')

        # Probar la API de reportes
        with app.test_client() as client:
            # Login
            login_response = client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'})
            print(f'Login status: {login_response.status_code}')

            # Probar API de datos
            api_response = client.get(f'/planes/{plan.id}/reportes/datos')
            print(f'API status: {api_response.status_code}')

            if api_response.status_code == 200:
                data = api_response.get_json()
                print('API Response:')
                print(f'  Success: {data.get("success")}')
                print(f'  Tipo análisis: {data.get("tipo_analisis")}')
                print(f'  Indicadores count: {len(data.get("indicadores", []))}')
                print(f'  Métricas keys: {list(data.get("metricas", {}).keys())}')

                # Mostrar primeros 2 indicadores
                indicadores = data.get('indicadores', [])
                if indicadores:
                    print('Primeros indicadores:')
                    for i, ind in enumerate(indicadores[:2]):
                        print(f'  {i+1}. {ind.get("nombre", "N/A")} - Meta: {ind.get("meta_2024", 0)} - Avance: {ind.get("avance", 0)}%')
                else:
                    print('No hay indicadores en la respuesta')
            else:
                print(f'Error en API: {api_response.get_data(as_text=True)}')
    else:
        print('No hay plan disponible')
