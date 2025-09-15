#!/usr/bin/env python3
"""
Script para agregar readonly a todos los inputs de Excel que no lo tienen
"""
import re

def add_readonly_to_inputs():
    """Agregar readonly a todos los inputs de Excel que no lo tienen"""

    # Leer el archivo
    with open('app/templates/planes/excel_view.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Patrón para encontrar inputs que no tienen readonly
    pattern = r'(<input type="[^"]*" class="form-control form-control-sm excel-cell")([^>]*>)'

    def replacement(match):
        tag_start = match.group(1)
        rest = match.group(2)

        # Si ya tiene readonly, devolver sin cambios
        if 'readonly' in rest:
            return match.group(0)

        # Agregar readonly antes del cierre >
        return f'{tag_start} readonly{rest}'

    # Aplicar el reemplazo
    new_content = re.sub(pattern, replacement, content)

    # Guardar el archivo
    with open('app/templates/planes/excel_view.html', 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("✅ Atributo readonly agregado a todos los inputs de Excel")

    # Contar cuántos inputs tienen readonly ahora
    readonly_count = len(re.findall(r'input.*excel-cell.*readonly', new_content))
    total_inputs = len(re.findall(r'input.*excel-cell', new_content))

    print(f"📊 Inputs con readonly: {readonly_count}/{total_inputs}")

if __name__ == "__main__":
    add_readonly_to_inputs()
