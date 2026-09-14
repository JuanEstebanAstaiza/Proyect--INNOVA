#!/usr/bin/env python3
"""
Script simple para verificar datos en la base de datos
"""

from app import create_app, db

app = create_app()

def check_data():
    with app.app_context():
        print("🔍 VERIFICANDO DATOS EN BASE DE DATOS")
        print("=" * 40)

        from app.models.user import User
        from app.models.plan_desarrollo import PlanDesarrollo
        from app.models.linea_estrategica import LineaEstrategica
        from app.models.indicador_producto import IndicadorProducto

        # Usuario admin
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print(f"✅ Admin: {admin.username}")
        else:
            print("❌ No admin")

        # Planes
        planes = PlanDesarrollo.query.all()
        print(f"📋 Planes: {len(planes)}")
        for plan in planes:
            print(f"   - {plan.titulo} (Estado: {plan.estado})")

        # Plan activo
        plan_activo = PlanDesarrollo.query.filter_by(estado='activo').first()
        if plan_activo:
            print(f"✅ Plan activo: {plan_activo.titulo}")

            # Líneas
            lineas = LineaEstrategica.query.filter_by(plan=plan_activo).all()
            print(f"🏛️ Líneas estratégicas: {len(lineas)}")

            # Indicadores
            indicadores = IndicadorProducto.query.all()
            print(f"📊 Indicadores: {len(indicadores)}")

            if indicadores:
                print("   Algunos indicadores:")
                for ind in indicadores[:3]:
                    print(f"   - {ind.nombre}: Meta {ind.meta_2024}")
            else:
                print("❌ No hay indicadores")
        else:
            print("❌ No hay plan activo")

        print("\n🧪 PRUEBA:")
        print("1. python run.py")
        print("2. http://localhost:5000")
        print("3. Login: admin / admin123")
        print("4. Dashboard → Ver Reportes")

if __name__ == '__main__':
    check_data()
