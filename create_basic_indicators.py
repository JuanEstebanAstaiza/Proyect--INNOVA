#!/usr/bin/env python3
"""
Script para crear indicadores básicos para el sistema de reportes
"""

from app import create_app, db

app = create_app()

def create_basic_indicators():
    with app.app_context():
        print("📊 CREANDO INDICADORES BÁSICOS PARA REPORTES")
        print("=" * 50)

        from app.models.user import User
        from app.models.plan_desarrollo import PlanDesarrollo
        from app.models.linea_estrategica import LineaEstrategica
        from app.models.componente import Componente
        from app.models.programa import Programa
        from app.models.proyecto import Proyecto
        from app.models.indicador_producto import IndicadorProducto

        # Obtener plan activo
        admin = User.query.filter_by(username='admin').first()
        plan = PlanDesarrollo.query.filter_by(municipio=admin, estado='activo').first()

        if not plan:
            print("❌ No hay plan activo")
            return

        print(f"✅ Plan activo: {plan.titulo}")

        # Verificar si ya hay indicadores
        indicadores_existentes = IndicadorProducto.query.count()
        if indicadores_existentes > 0:
            print(f"⚠️ Ya existen {indicadores_existentes} indicadores")
            return

        # Obtener líneas estratégicas
        lineas = LineaEstrategica.query.filter_by(plan=plan).all()
        if not lineas:
            print("❌ No hay líneas estratégicas")
            return

        print(f"✅ Encontradas {len(lineas)} líneas estratégicas")

        # Crear componentes básicos para cada línea
        componentes_creados = []
        for linea in lineas:
            # Crear componente básico
            componente = Componente(
                cod_componente=float(linea.cod_linea) + 0.1,
                nombre=f"Componente {linea.nombre}",
                descripcion=f"Componente principal de {linea.nombre}",
                linea_estrategica=linea
            )
            db.session.add(componente)
            componentes_creados.append(componente)

        db.session.commit()
        print(f"✅ {len(componentes_creados)} componentes creados")

        # Crear programas básicos
        programas_creados = []
        for i, componente in enumerate(componentes_creados):
            programa = Programa(
                cod_programa=f"P{i+1:03d}",
                nombre=f"Programa {componente.nombre}",
                descripcion=f"Programa principal para {componente.nombre}",
                componente=componente
            )
            db.session.add(programa)
            programas_creados.append(programa)

        db.session.commit()
        print(f"✅ {len(programas_creados)} programas creados")

        # Crear proyectos básicos
        proyectos_creados = []
        for i, programa in enumerate(programas_creados):
            proyecto = Proyecto(
                nombre=f"Proyecto {programa.nombre.replace('Programa ', '')}",
                descripcion=f"Proyecto principal para {programa.nombre}",
                programa=programa
            )
            db.session.add(proyecto)
            proyectos_creados.append(proyecto)

        db.session.commit()
        print(f"✅ {len(proyectos_creados)} proyectos creados")

        # Crear indicadores básicos
        indicadores_data = [
            ("Cobertura de servicios básicos", "% población con acceso", "Porcentaje", 85),
            ("Tasa de empleo juvenil", "% jóvenes empleados", "Porcentaje", 65),
            ("Índice de satisfacción ciudadana", "Escala 1-100", "Índice", 78),
            ("Reducción de pobreza", "% disminución", "Porcentaje", 45),
            ("Cobertura educativa", "% niños escolarizados", "Porcentaje", 92),
            ("Acceso a salud", "% con cobertura médica", "Porcentaje", 88),
            ("Eficiencia energética", "% ahorro energético", "Porcentaje", 70),
            ("Recolección de residuos", "% cobertura", "Porcentaje", 75)
        ]

        indicadores_creados = []
        for i, (nombre, descripcion, unidad, meta) in enumerate(indicadores_data):
            proyecto = proyectos_creados[i % len(proyectos_creados)]
            indicador = IndicadorProducto(
                cod_indicador=f"I{i+1:03d}",
                nombre=nombre,
                descripcion=descripcion,
                tipo_indicador="Producto",
                unidad=unidad,
                meta_2024=meta,
                sentido="positivo",
                proyecto=proyecto
            )
            db.session.add(indicador)
            indicadores_creados.append(indicador)

        db.session.commit()
        print(f"✅ {len(indicadores_creados)} indicadores creados")

        # Nota: Los datos de ejecución trimestral requieren campos adicionales
        # Por ahora solo creamos los indicadores básicos
        print("ℹ️  Nota: Los datos de ejecución trimestral requieren configuración adicional")
        print("   Los indicadores están listos para que el sistema funcione")

        print("\n🎯 RESUMEN FINAL:")
        print("=" * 30)
        print(f"📋 Plan: {plan.titulo}")
        print(f"🏛️ Líneas: {len(lineas)}")
        print(f"🔧 Componentes: {len(componentes_creados)}")
        print(f"📚 Programas: {len(programas_creados)}")
        print(f"🚀 Proyectos: {len(proyectos_creados)}")
        print(f"📊 Indicadores: {len(indicadores_creados)}")

        print("\n🧪 PRUEBA EL SISTEMA:")
        print("1. python run.py")
        print("2. http://localhost:5000")
        print("3. Login: admin / admin123")
        print("4. Dashboard → 'Ver Reportes'")
        print("5. Verificar que aparecen datos en la tabla")
        print("6. Probar diferentes tipos de análisis")

        print("\n✅ ¡DATOS DE PRUEBA CREADOS!")
        print("   Sistema de reportes BI listo para pruebas completas.")

if __name__ == '__main__':
    create_basic_indicators()
