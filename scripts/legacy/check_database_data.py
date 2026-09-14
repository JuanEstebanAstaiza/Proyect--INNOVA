#!/usr/bin/env python3
"""
Script para verificar los datos en la base de datos
"""

from app import create_app, db

app = create_app()

def check_database_data():
    """Verificar qué datos existen en la base de datos"""

    with app.app_context():
        print("🔍 VERIFICANDO DATOS EN LA BASE DE DATOS")
        print("=" * 45)

        from app.models.user import User
        from app.models.plan_desarrollo import PlanDesarrollo
        from app.models.linea_estrategica import LineaEstrategica
        from app.models.componente import Componente
        from app.models.programa import Programa
        from app.models.proyecto import Proyecto
        from app.models.indicador_producto import IndicadorProducto
        from app.models.ejecucion_trimestral import EjecucionTrimestral

        # Verificar usuario admin
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print(f"✅ Usuario admin: {admin.username} ({admin.first_name})")
        else:
            print("❌ No hay usuario admin")

        # Verificar planes
        planes = PlanDesarrollo.query.all()
        print(f"📋 Total de planes: {len(planes)}")

        for plan in planes:
            print(f"   - {plan.titulo} (ID: {plan.id}, Estado: {plan.estado})")
            print(".0f"            print(".0f"
        # Verificar estructura jerárquica
        plan_activo = PlanDesarrollo.query.filter_by(estado='activo').first()
        if plan_activo:
            print(f"\n🏗️ ESTRUCTURA DEL PLAN ACTIVO: {plan_activo.titulo}")
            print("=" * 50)

            # Líneas estratégicas
            lineas = LineaEstrategica.query.filter_by(plan=plan_activo).all()
            print(f"🏛️ Líneas Estratégicas: {len(lineas)}")
            for linea in lineas:
                print(f"   {linea.cod_linea}. {linea.nombre}")

            # Componentes
            componentes = Componente.query.join(LineaEstrategica).filter(LineaEstrategica.plan == plan_activo).all()
            print(f"🔧 Componentes: {len(componentes)}")
            for componente in componentes:
                print(f"   {componente.cod_componente}. {componente.nombre}")

            # Programas
            programas = Programa.query.join(Componente).join(LineaEstrategica).filter(LineaEstrategica.plan == plan_activo).all()
            print(f"📚 Programas: {len(programas)}")
            for programa in programas:
                print(f"   {programa.cod_programa}. {programa.nombre}")

            # Proyectos
            proyectos = Proyecto.query.join(Programa).join(Componente).join(LineaEstrategica).filter(LineaEstrategica.plan == plan_activo).all()
            print(f"🚀 Proyectos: {len(proyectos)}")
            for proyecto in proyectos:
                print(f"   - {proyecto.nombre}")

            # Indicadores
            indicadores = IndicadorProducto.query.join(Proyecto).join(Programa).join(Componente).join(LineaEstrategica).filter(LineaEstrategica.plan == plan_activo).all()
            print(f"📊 Indicadores: {len(indicadores)}")
            for indicador in indicadores[:5]:  # Mostrar solo los primeros 5
                print(f"   - {indicador.nombre}: Meta {indicador.meta_2024}, Q1: {indicador.ejecucion_q1}, Q2: {indicador.ejecucion_q2}")

            # Ejecuciones trimestrales
            ejecuciones = EjecucionTrimestral.query.join(IndicadorProducto).join(Proyecto).join(Programa).join(Componente).join(LineaEstrategica).filter(LineaEstrategica.plan == plan_activo).all()
            print(f"📈 Registros de Ejecución: {len(ejecuciones)}")

            if ejecuciones:
                print("   Ejemplos de ejecución:")
                for ejecucion in ejecuciones[:3]:
                    print(f"   - {ejecucion.indicador.nombre}: {ejecucion.anio} Q{ejecucion.trimestre} = {ejecucion.valor_ejecutado}")

        print("\n🧪 PRUEBA DEL SISTEMA:")
        print("1. python run.py")
        print("2. http://localhost:5000")
        print("3. Login: admin / admin123")
        print("4. Dashboard → 'Ver Reportes'")
        print("5. Verificar que la tabla se carga con datos")
        print("6. Probar diferentes tipos de análisis")
        print("7. Cambiar período y tipo de gráfico")

        if indicadores:
            print("\n✅ ¡BASE DE DATOS POBLADA!")
            print("   El sistema de reportes BI tiene datos para probar.")
        else:
            print("\n⚠️ BASE DE DATOS VACÍA")
            print("   Necesitas crear datos de prueba.")

if __name__ == '__main__':
    check_database_data()
