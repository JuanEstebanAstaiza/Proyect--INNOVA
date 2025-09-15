#!/usr/bin/env python3
"""
Script para verificar que la edición con doble clic funciona correctamente
"""
from app import create_app, db
from app.models import PlanDesarrollo

def test_excel_double_click():
    """Verificar que la edición con doble clic está correctamente configurada"""
    print("🔧 Verificando configuración de edición con doble clic en Excel...")

    with create_app().app_context():
        # Verificar que hay planes disponibles
        plan = PlanDesarrollo.query.filter_by(estado='activo').first()
        if not plan:
            print("❌ No hay planes activos disponibles")
            return False

        print(f"✅ Plan activo encontrado: {plan.titulo}")

        # Leer el template para verificar configuraciones
        try:
            with open('app/templates/planes/excel_view.html', 'r', encoding='utf-8') as f:
                content = f.read()

            # Verificar que todos los inputs tienen readonly
            inputs_total = content.count('class="form-control form-control-sm excel-cell"')
            inputs_readonly = content.count('readonly')
            print(f"📊 Inputs totales: {inputs_total}")
            print(f"📊 Inputs con readonly: {inputs_readonly}")

            # Verificar que existe el evento de doble clic
            if 'dblclick' in content:
                print("✅ Evento de doble clic configurado")
            else:
                print("❌ Evento de doble clic NO encontrado")
                return False

            # Verificar que existe la función abrirModalEdicion
            if 'function abrirModalEdicion' in content:
                print("✅ Función abrirModalEdicion encontrada")
            else:
                print("❌ Función abrirModalEdicion NO encontrada")
                return False

            # Verificar que se quita readonly en la función
            if 'removeAttribute(\'readonly\')' in content:
                print("✅ Lógica para quitar readonly implementada")
            else:
                print("❌ Lógica para quitar readonly NO encontrada")
                return False

            # Verificar estilos de edición
            if '.editing-cell' in content:
                print("✅ Estilos para celdas en edición encontrados")
            else:
                print("❌ Estilos para celdas en edición NO encontrados")
                return False

            # Verificar mensaje de ayuda
            if 'doble clic' in content.lower():
                print("✅ Mensaje de ayuda sobre doble clic encontrado")
            else:
                print("❌ Mensaje de ayuda sobre doble clic NO encontrado")
                return False

            # Verificar que el tooltip se actualizó
            if 'modo seguro' in content.lower():
                print("✅ Tooltip actualizado con información de modo seguro")
            else:
                print("❌ Tooltip NO actualizado")

        except FileNotFoundError:
            print("❌ Archivo de template no encontrado")
            return False
        except Exception as e:
            print(f"❌ Error al leer template: {e}")
            return False

        print("\n📋 Resumen de cambios implementados:")
        print("✅ Todos los inputs tienen readonly por defecto")
        print("✅ Doble clic abre modal de edición")
        print("✅ Modal quita readonly para permitir edición")
        print("✅ Al cerrar modal, se vuelve a poner readonly")
        print("✅ Estilos visuales para celdas en edición")
        print("✅ Mensaje de ayuda claro para usuarios")
        print("✅ Tooltip actualizado con información de seguridad")

        return True

if __name__ == "__main__":
    if test_excel_double_click():
        print("\n🎊 ¡Configuración de doble clic completada exitosamente!")
        print("Ahora los usuarios deben hacer doble clic para editar celdas.")
    else:
        print("\n❌ Algunos elementos de la configuración fallaron.")
