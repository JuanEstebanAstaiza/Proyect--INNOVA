#!/usr/bin/env python3
"""
Script para verificar la respuesta de la API de reportes
"""

from app import create_app
from app.models import User, PlanDesarrollo
import json

app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    plan = PlanDesarrollo.query.filter_by(municipio=admin).first()

    if plan:
        print(f"Plan encontrado: {plan.titulo} (ID: {plan.id})")

        # Crear un cliente de prueba
        with app.test_client() as client:
            # Login primero
            login_response = client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            }, follow_redirects=True)

            print(f"Login status: {login_response.status_code}")

            # Verificar API de reportes
            api_response = client.get(f'/planes/{plan.id}/reportes/datos')
            print(f"API status: {api_response.status_code}")
            print(f"Content-Type: {api_response.content_type}")
            print(f"Content-Length: {len(api_response.get_data())}")

            if api_response.status_code == 200:
                try:
                    data = api_response.get_json()
                    print("\n✅ API funcionando correctamente")
                    print(f"Response type: {type(data)}")
                    print(f"Keys: {list(data.keys())}")
                    print(f"Success: {data.get('success')}")

                    if 'indicadores' in data:
                        print(f"Indicadores: {len(data['indicadores'])} encontrados")

                    # Mostrar el JSON completo para debugging
                    print("\n--- JSON Response ---")
                    print(json.dumps(data, indent=2, ensure_ascii=False))

                except Exception as e:
                    print(f"\n❌ Error al parsear JSON: {e}")
                    raw_data = api_response.get_data(as_text=True)
                    print(f"Raw response: {raw_data[:500]}...")
            else:
                print(f"\n❌ Error en API: {api_response.status_code}")
                raw_data = api_response.get_data(as_text=True)
                print(f"Response: {raw_data}")
    else:
        print("No hay plan disponible")
