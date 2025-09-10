#!/usr/bin/env python3
"""
Script para crear un archivo de auditoría de ejemplo
"""
import os
from datetime import datetime

def create_sample_audit_file():
    """Crear un archivo de auditoría de ejemplo"""

    # Crear directorio si no existe
    audit_dir = 'audit_files/user_1'
    os.makedirs(audit_dir, exist_ok=True)

    # Nombre del archivo
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_plan_1_meta_2024.txt"
    filepath = os.path.join(audit_dir, filename)

    # Contenido del archivo
    content = """AUDITORÍA DE CAMBIO - PLAN DE DESARROLLO
==================================================

INFORMACIÓN GENERAL
===================
Fecha y Hora: 2024-12-19 14:30:45
Usuario: administrador (admin@example.com)
Plan: Plan de Desarrollo TEST 2024-2027 (ID: 1)

DETALLES DEL CAMBIO
===================
Columna Editada: Meta 2024
Valor Anterior: 150.0
Valor Nuevo: 200.0

JUSTIFICACIÓN
=============
Se incrementa la meta del indicador debido al aumento en la demanda de servicios y la mejora en la capacidad operativa del proyecto. Los recursos adicionales han sido aprobados por la dirección municipal.

ARCHIVOS ANEXADOS
=================
Archivo: presupuesto_aprobado_2024.pdf
Tamaño: 2457600 bytes
Ubicación: uploads/justifications/20241219_1_admin_presupuesto_aprobado_2024.pdf
URL de descarga: /uploads/justifications/20241219_1_admin_presupuesto_aprobado_2024.pdf

Archivo: analisis_demanda.xlsx
Tamaño: 1843200 bytes
Ubicación: uploads/justifications/20241219_1_admin_analisis_demanda.xlsx
URL de descarga: /uploads/justifications/20241219_1_admin_analisis_demanda.xlsx

INFORMACIÓN DEL INDICADOR
=========================
Indicador: Número de emprendedores capacitados
Código: IP-001
Proyecto: Centro de Emprendimiento Municipal
Programa: Programa de Apoyo a Emprendimientos
Componente: Fortalecimiento del Sector Productivo
Línea Estratégica: Desarrollo Económico Sostenible

==================================================
FIN DEL REGISTRO DE AUDITORÍA
"""

    # Crear el archivo
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Archivo de auditoría de ejemplo creado: {filepath}")

    # Crear también el resumen
    summary_path = os.path.join(audit_dir, 'resumen_auditoria.txt')
    summary_content = """RESUMEN DE AUDITORÍA - USUARIO 1
==================================================

Total de cambios registrados: 1
Fecha de generación: 2024-12-19 14:30:45

LISTADO DE CAMBIOS
==================
1. 2024-12-19 14:30:45
   Columna: Meta 2024
   Cambio: 150.0 → 200.0
   Archivo: 20241219_143045_plan_1_meta_2024.txt

==================================================
FIN DEL RESUMEN
"""

    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_content)

    print(f"✅ Resumen de auditoría creado: {summary_path}")

if __name__ == "__main__":
    create_sample_audit_file()
    print("\n🎯 Ejemplo de archivos de auditoría creados exitosamente!")
    print("Estos archivos demuestran el formato y contenido que se genera automáticamente.")
