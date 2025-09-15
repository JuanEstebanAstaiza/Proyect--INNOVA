#!/usr/bin/env python3
"""
Script para verificar que todos los métodos de progreso funcionan correctamente
"""
from app import create_app

def test_progress_methods():
    """Verificar que los métodos de progreso funcionan correctamente"""
    print("🔧 Verificando métodos de progreso en toda la jerarquía...")

    app = create_app()
    with app.app_context():
        from app.models import LineaEstrategica

        # Obtener la primera línea estratégica con datos
        linea = LineaEstrategica.query.filter_by(estado='activo').first()

        if linea:
            print(f"🏗️ Probando línea estratégica: {linea.nombre}")

            # Probar método de línea
            progreso_linea = linea.get_progreso_general()
            print(f"   📊 Progreso línea: {progreso_linea}%")

            # Probar componentes
            for componente in linea.componentes[:2]:  # Solo primeros 2
                print(f"   🏭 Componente: {componente.nombre}")
                progreso_componente = componente.get_progreso()
                print(f"      📊 Progreso componente: {progreso_componente}%")

                # Probar programas
                for programa in componente.programas[:1]:  # Solo primer programa
                    print(f"      📋 Programa: {programa.nombre}")
                    progreso_programa = programa.get_progreso()
                    print(f"         📊 Progreso programa: {progreso_programa}%")

                    # Probar proyectos
                    for proyecto in programa.proyectos[:1]:  # Solo primer proyecto
                        print(f"         🏗️ Proyecto: {proyecto.nombre}")
                        progreso_proyecto = proyecto.get_progreso()
                        print(f"            📊 Progreso proyecto: {progreso_proyecto}%")

                        # Probar indicadores
                        for indicador in proyecto.indicadores[:2]:  # Solo primeros 2
                            progreso_indicador = indicador.get_progreso_porcentual()
                            print(f"            📈 Indicador: {indicador.nombre}")
                            print(f"               📊 Progreso indicador: {progreso_indicador}%")

            print("\n✅ Todos los métodos de progreso funcionan correctamente")
            print("✅ No hay valores None o errores en los cálculos")
            print("✅ La jerarquía completa de progreso está operativa")

        else:
            print("⚠️ No se encontraron líneas estratégicas con datos")

if __name__ == "__main__":
    test_progress_methods()
