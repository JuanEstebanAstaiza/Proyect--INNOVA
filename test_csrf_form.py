#!/usr/bin/env python3
"""
Script para probar que el formulario de eliminación incluye correctamente el token CSRF
"""

from app import create_app
from flask import render_template

def test_csrf_form():
    """Prueba que el formulario de eliminación incluye el token CSRF"""

    app = create_app()
    with app.app_context():
        print("🔒 PRUEBA DEL FORMULARIO DE ELIMINACIÓN CON CSRF")
        print("=" * 60)

        try:
            from app.models import User, PlanDesarrollo

            # Buscar usuario admin
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("❌ No se encontró usuario admin")
                return False

            # Obtener un plan para probar
            plan = PlanDesarrollo.query.filter_by(municipio=admin).first()
            if not plan:
                print("❌ No se encontró ningún plan para probar")
                return False

            print(f"👤 Usuario: {admin.username}")
            print(f"📋 Plan de prueba: {plan.titulo} (ID: {plan.id})")

            # Probar renderizado del template con CSRF
            from flask_wtf.csrf import generate_csrf

            with app.test_request_context():
                # Necesitamos definir csrf_token en el contexto de Jinja2
                from flask_wtf.csrf import generate_csrf
                csrf_token_value = generate_csrf()

                # Crear contexto con csrf_token disponible
                rendered = render_template('planes/index.html',
                                         planes=[plan],
                                         mostrar_todos=True,
                                         csrf_token=lambda: csrf_token_value)

                print("\n🔍 Verificando elementos del formulario:")
                # Verificar que contiene el modal
                if 'eliminarModal' in rendered:
                    print("   ✅ Modal de eliminación encontrado")
                else:
                    print("   ❌ Modal de eliminación NO encontrado")
                    return False

                # Verificar que contiene el formulario
                if 'eliminarForm' in rendered:
                    print("   ✅ Formulario de eliminación encontrado")
                else:
                    print("   ❌ Formulario de eliminación NO encontrado")
                    return False

                # Verificar que contiene el token CSRF
                if 'name="csrf_token"' in rendered and csrf_token_value in rendered:
                    print("   ✅ Token CSRF incluido en el formulario")
                else:
                    print("   ❌ Token CSRF NO incluido en el formulario")
                    return False

                # Verificar que contiene el JavaScript
                if 'confirmarEliminar' in rendered:
                    print("   ✅ Función JavaScript confirmarEliminar encontrada")
                else:
                    print("   ❌ Función JavaScript confirmarEliminar NO encontrada")
                    return False

                # Verificar que contiene la función getCsrfToken
                if 'getCsrfToken' in rendered:
                    print("   ✅ Función JavaScript getCsrfToken encontrada")
                else:
                    print("   ❌ Función JavaScript getCsrfToken NO encontrada")
                    return False

                # Verificar que contiene actualizarCsrfToken
                if 'actualizarCsrfToken' in rendered:
                    print("   ✅ Función JavaScript actualizarCsrfToken encontrada")
                else:
                    print("   ❌ Función JavaScript actualizarCsrfToken NO encontrada")
                    return False

                print("\n✅ Verificación completada exitosamente!")
                print("\n📋 Resumen:")
                print("   • Template renderizado correctamente")
                print("   • Modal de eliminación presente")
                print("   • Formulario con token CSRF")
                print("   • JavaScript para manejo de CSRF")
                print("   • Funciones auxiliares implementadas")

                return True

        except Exception as e:
            print(f"\n❌ Error durante la prueba: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test_csrf_form()
    if success:
        print("\n🎉 ¡El formulario de eliminación está listo para funcionar correctamente!")
        print("\n💡 El error CSRF debería estar resuelto. Prueba:")
        print("   1. Inicia sesión en la aplicación")
        print("   2. Ve a la lista de planes")
        print("   3. Intenta eliminar un plan")
        print("   4. Debería funcionar sin errores CSRF")
    else:
        print("\n❌ Hay problemas con el formulario de eliminación.")
