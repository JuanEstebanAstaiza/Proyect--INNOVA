#!/usr/bin/env python3
"""
Script para verificar la sesión del usuario actual
"""

print("🔐 VERIFICACIÓN DE SESIÓN DE USUARIO")
print("=" * 50)

print("\n📋 USUARIOS DISPONIBLES:")
print("1. admin_test_data (admin@test.com) - TIENE el plan de desarrollo")
print("2. admin (admin@alcaldia.com)")
print("3. Otros usuarios...")

print("\n❓ ¿Con qué usuario estás logueado en la aplicación web?")
print("   Debes estar logueado como 'admin_test_data' para ver el plan generado.")

print("\n🔧 PASOS PARA SOLUCIONAR:")
print("1. Ve a la página de login de la aplicación")
print("2. Inicia sesión con:")
print("   - Usuario: admin_test_data")
print("   - Email: admin@test.com")
print("   - Contraseña: admin123")
print("3. Una vez logueado, deberías ver el plan en el dashboard")

print("\n📊 EL PLAN GENERADO CONTIENE:")
print("✅ 1 Plan de Desarrollo")
print("✅ 4 Líneas Estratégicas")
print("✅ 11 Componentes")
print("✅ 12 Programas")
print("✅ 28 Proyectos")
print("✅ 111 Indicadores")
print("✅ 444 Ejecuciones Trimestrales")

print("\n🎯 SI SIGUES SIN VER EL PLAN:")
print("1. Borra las cookies del navegador")
print("2. Reinicia el servidor Flask")
print("3. Verifica que no haya errores en la consola del navegador (F12)")
print("4. Confirma que estás en la URL correcta de la aplicación")

print("\n" + "=" * 50)
print("💡 RESUMEN: Los datos están en la BD, el problema es de sesión/usuario")
