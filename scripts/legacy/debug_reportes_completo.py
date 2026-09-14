#!/usr/bin/env python3
"""
Script completo para debuggear el sistema de reportes BI
"""

from app import create_app, db
from app.models.user import User
from app.models.plan_desarrollo import PlanDesarrollo
from app.models.indicador_producto import IndicadorProducto

app = create_app()

def debug_reportes():
    with app.app_context():
        print("🔍 DEBUG COMPLETO DEL SISTEMA DE REPORTES BI")
        print("=" * 50)

        # 1. Verificar usuario y plan
        print("\n1️⃣ VERIFICACIÓN DE DATOS BÁSICOS")
        print("-" * 30)

        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("❌ ERROR: No hay usuario admin")
            return

        print(f"✅ Usuario admin: {admin.username} (ID: {admin.id})")

        plan = PlanDesarrollo.query.filter_by(municipio=admin, estado='activo').first()
        if not plan:
            print("❌ ERROR: No hay plan activo")
            return

        print(f"✅ Plan activo: {plan.titulo} (ID: {plan.id})")
        print(f"   Estado: {plan.estado}")
        print(f"   Presupuesto: ${plan.presupuesto_total:,.0f}")

        # 2. Verificar indicadores
        print("\n2️⃣ VERIFICACIÓN DE INDICADORES")
        print("-" * 30)

        indicadores = IndicadorProducto.query.all()
        print(f"✅ Total indicadores: {len(indicadores)}")

        if indicadores:
            print("Primeros 3 indicadores:")
            for i, ind in enumerate(indicadores[:3]):
                print(f"   {i+1}. {ind.nombre}")
                print(f"      Meta 2024: {ind.meta_2024}")
                print(f"      Tipo: {ind.tipo_indicador}")
                print(f"      Unidad: {ind.unidad}")
        else:
            print("❌ ERROR: No hay indicadores en la base de datos")

        # 3. Probar login
        print("\n3️⃣ PRUEBA DE LOGIN")
        print("-" * 30)

        with app.test_client() as client:
            # Intentar login
            login_response = client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            }, follow_redirects=True)

            print(f"Login status: {login_response.status_code}")

            if login_response.status_code != 200:
                print("❌ ERROR: Login falló")
                print(f"Respuesta: {login_response.get_data(as_text=True)[:200]}...")
                return

            print("✅ Login exitoso")

            # 4. Probar página de reportes
            print("\n4️⃣ PRUEBA DE PÁGINA DE REPORTES")
            print("-" * 30)

            reportes_response = client.get(f'/planes/{plan.id}/reportes')
            print(f"Página reportes status: {reportes_response.status_code}")

            if reportes_response.status_code != 200:
                print("❌ ERROR: Página de reportes no carga")
                print(f"Respuesta: {reportes_response.get_data(as_text=True)[:200]}...")
                return

            print("✅ Página de reportes carga correctamente")

            # Verificar que contiene elementos clave
            content = reportes_response.get_data(as_text=True)
            checks = [
                ('Título de reportes', 'Reportes y Análisis' in content),
                ('Select tipo análisis', 'tipo-analisis' in content),
                ('Select período', 'periodo' in content),
                ('Contenedor de gráficos', 'chart-container' in content),
                ('Tabla de datos', 'datos-detallados' in content),
                ('Chart.js', 'chart.js' in content.lower()),
                ('Función cargarDatosReportes', 'cargarDatosReportes' in content),
                ('Token CSRF', 'csrfToken' in content or 'csrf_token' in content)
            ]

            print("Verificación de elementos en template:")
            for check_name, found in checks:
                status = "✅" if found else "❌"
                print(f"   {status} {check_name}")

            # 5. Probar API de datos
            print("\n5️⃣ PRUEBA DE API DE DATOS")
            print("-" * 30)

            api_response = client.get(f'/planes/{plan.id}/reportes/datos')
            print(f"API datos status: {api_response.status_code}")

            if api_response.status_code != 200:
                print("❌ ERROR: API de datos no responde")
                print(f"Respuesta: {api_response.get_data(as_text=True)[:200]}...")
                return

            print("✅ API de datos responde correctamente")

            try:
                data = api_response.get_json()
                print("✅ Respuesta JSON válida")
                print(f"   Success: {data.get('success')}")
                print(f"   Plan: {data.get('plan_titulo')}")
                print(f"   Indicadores: {len(data.get('indicadores', []))}")
                print(f"   Tendencias: {'Sí' if data.get('tendencias') else 'No'}")
                print(f"   Métricas: {len(data.get('metricas', {}))}")

                # Mostrar estructura de respuesta
                print("\nEstructura de respuesta:")
                print(f"   Keys: {list(data.keys())}")
                if data.get('indicadores'):
                    print(f"   Primer indicador: {data['indicadores'][0].get('nombre', 'N/A')}")

            except Exception as e:
                print("❌ ERROR: Respuesta no es JSON válido")
                print(f"   Error: {e}")
                print(f"   Respuesta cruda: {api_response.get_data(as_text=True)[:300]}...")

        print("\n🎯 DIAGNÓSTICO COMPLETADO")
        print("=" * 30)

        print("\n📋 SIGUIENTE PASOS:")
        print("1. Si hay errores arriba, corregirlos")
        print("2. Abrir navegador con F12 (Developer Tools)")
        print("3. Ir a Console y buscar errores de JavaScript")
        print("4. Verificar que Chart.js se carga correctamente")
        print("5. Comprobar que las funciones JavaScript existen")

        print("\n🔧 POSIBLES PROBLEMAS A REVISAR:")
        print("- JavaScript no se ejecuta (DOMContentLoaded)")
        print("- Chart.js no se carga")
        print("- Funciones JavaScript no definidas")
        print("- Errores de CORS o CSRF")
        print("- Problemas con el DOM")

if __name__ == '__main__':
    debug_reportes()
