#!/usr/bin/env python3
"""
Generador de PDFs de auditoría con marca de agua profesional
"""
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.colors import Color
from app.models import EditJustification, User, PlanDesarrollo

def setup_pdf_styles():
    """Configurar estilos para el PDF"""
    styles = getSampleStyleSheet()

    # Estilo para el título principal
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue,
    ))

    # Estilo para subtítulos
    styles.add(ParagraphStyle(
        name='CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=20,
        textColor=colors.darkgreen,
        borderColor=colors.grey,
        borderWidth=1,
        borderPadding=5,
    ))

    # Estilo para el contenido normal
    styles.add(ParagraphStyle(
        name='CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        alignment=TA_LEFT,
    ))

    # Estilo para información destacada
    styles.add(ParagraphStyle(
        name='CustomInfo',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=20,
    ))

    return styles

def add_watermark(canvas, doc):
    """Agregar marca de agua al PDF"""
    canvas.saveState()

    # Configurar la marca de agua
    canvas.setFont('Helvetica', 60)
    canvas.setFillColor(Color(0.9, 0.9, 0.9, 0.3))  # Gris claro y transparente

    # Rotar y posicionar la marca de agua
    canvas.rotate(45)
    canvas.drawCentredString(300, 400, "DOCUMENTO AUTOGENERADO")
    canvas.drawCentredString(300, 300, "POR LA APLICACIÓN")

    # Agregar fecha de generación
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(Color(0.7, 0.7, 0.7, 0.5))
    canvas.rotate(-45)  # Restaurar rotación
    canvas.drawString(30, 30, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    canvas.restoreState()

def create_audit_pdf(edit_justification):
    """Crear PDF de auditoría con marca de agua"""

    # Obtener información del usuario y plan
    user = User.query.get(edit_justification.user_id)
    plan = PlanDesarrollo.query.get(edit_justification.plan_id)

    # Crear directorio del usuario
    audit_dir = f'audit_files/user_{edit_justification.user_id}'
    os.makedirs(audit_dir, exist_ok=True)

    # Generar nombre del archivo
    timestamp = edit_justification.created_at.strftime('%Y%m%d_%H%M%S')
    plan_id = edit_justification.plan_id
    column = edit_justification.column_name or 'unknown'
    filename = f"{timestamp}_plan_{plan_id}_{column}.pdf"
    filepath = os.path.join(audit_dir, filename)

    # Configurar el documento PDF
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    styles = setup_pdf_styles()
    story = []

    # Título principal
    title = Paragraph("AUDITORÍA DE CAMBIO - PLAN DE DESARROLLO", styles['CustomTitle'])
    story.append(title)
    story.append(Spacer(1, 12))

    # Línea separadora
    story.append(Paragraph("=" * 60, styles['CustomNormal']))
    story.append(Spacer(1, 20))

    # Información General
    story.append(Paragraph("INFORMACIÓN GENERAL", styles['CustomHeading']))

    # Crear tabla con información general
    info_data = [
        ["Fecha y Hora:", edit_justification.created_at.strftime('%d/%m/%Y %H:%M:%S')],
        ["Usuario:", f"{user.username if user else 'N/A'} ({user.email if user else 'N/A'})"],
        ["Plan:", f"{plan.titulo if plan else 'N/A'} (ID: {edit_justification.plan_id})"],
    ]

    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    # Detalles del Cambio
    story.append(Paragraph("DETALLES DEL CAMBIO", styles['CustomHeading']))

    change_data = [
        ["Columna Editada:", edit_justification.get_column_display_name()],
        ["Valor Anterior:", edit_justification.old_value or 'N/A'],
        ["Valor Nuevo:", edit_justification.new_value],
    ]

    change_table = Table(change_data, colWidths=[2*inch, 4*inch])
    change_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(change_table)
    story.append(Spacer(1, 20))

    # Justificación
    story.append(Paragraph("JUSTIFICACIÓN", styles['CustomHeading']))
    justification_text = edit_justification.justification or "No se proporcionó justificación"
    story.append(Paragraph(justification_text, styles['CustomNormal']))
    story.append(Spacer(1, 20))

    # Archivos Anexados
    story.append(Paragraph("ARCHIVOS ANEXADOS", styles['CustomHeading']))

    if edit_justification.support_file_path and os.path.exists(edit_justification.support_file_path):
        filename = os.path.basename(edit_justification.support_file_path)
        file_size = os.path.getsize(edit_justification.support_file_path)

        attachment_data = [
            ["Archivo:", filename],
            ["Tamaño:", f"{file_size} bytes"],
            ["Ubicación:", edit_justification.support_file_path],
            ["URL de descarga:", edit_justification.get_support_file_url() or 'N/A'],
        ]
    else:
        attachment_data = [["Estado:", "No se anexaron archivos de soporte."]]

    attachment_table = Table(attachment_data, colWidths=[2*inch, 4*inch])
    attachment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(attachment_table)
    story.append(Spacer(1, 20))

    # Información del Indicador (si existe)
    if edit_justification.indicador_id:
        from app.models import IndicadorProducto
        indicador = IndicadorProducto.query.get(edit_justification.indicador_id)
        if indicador:
            story.append(Paragraph("INFORMACIÓN DEL INDICADOR", styles['CustomHeading']))

            indicator_data = [
                ["Indicador:", indicador.nombre],
                ["Código:", indicador.cod_indicador],
                ["Proyecto:", indicador.proyecto.nombre if indicador.proyecto else 'N/A'],
                ["Programa:", indicador.proyecto.programa.nombre if indicador.proyecto and indicador.proyecto.programa else 'N/A'],
                ["Componente:", indicador.proyecto.programa.componente.nombre if indicador.proyecto and indicador.proyecto.programa and indicador.proyecto.programa.componente else 'N/A'],
                ["Línea Estratégica:", indicador.proyecto.programa.componente.linea_estrategica.nombre if indicador.proyecto and indicador.proyecto.programa and indicador.proyecto.programa.componente and indicador.proyecto.programa.componente.linea_estrategica else 'N/A'],
            ]

            indicator_table = Table(indicator_data, colWidths=[2*inch, 4*inch])
            indicator_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightyellow),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(indicator_table)
            story.append(Spacer(1, 20))

    # Pie de página con información del sistema
    story.append(Paragraph("=" * 80, styles['CustomNormal']))
    footer_text = f"""
    <para alignment="center">
    <font size="8" color="gray">
    Documento autogenerado por la aplicación de gestión de planes de desarrollo<br/>
    Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br/>
    Este documento tiene carácter oficial y forma parte del registro de auditoría del sistema.
    </font>
    </para>
    """
    story.append(Paragraph(footer_text, styles['CustomInfo']))

    # Generar el PDF
    try:
        doc.build(story, onFirstPage=add_watermark, onLaterPages=add_watermark)
        print(f"✅ PDF de auditoría generado: {filepath}")
        return filepath
    except Exception as e:
        print(f"❌ Error generando PDF de auditoría: {e}")
        return None

def create_user_audit_summary_pdf(user_id):
    """Crear resumen de auditoría en PDF para un usuario"""
    from app.models import PlanDesarrollo

    # Obtener usuario y plan activo
    user = User.query.get(user_id)
    active_plan = PlanDesarrollo.query.filter_by(estado='activo').first()

    if not user or not active_plan:
        print("❌ Usuario o plan activo no encontrado")
        return None

    # Obtener cambios del usuario
    changes = EditJustification.query.filter_by(
        user_id=user_id,
        plan_id=active_plan.id
    ).order_by(EditJustification.created_at.desc()).all()

    # Crear directorio del usuario
    audit_dir = f'audit_files/user_{user_id}'
    os.makedirs(audit_dir, exist_ok=True)

    # Nombre del archivo
    filename = 'resumen_auditoria.pdf'
    filepath = os.path.join(audit_dir, filename)

    # Configurar el documento PDF
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    styles = setup_pdf_styles()
    story = []

    # Título principal
    title = Paragraph("RESUMEN DE AUDITORÍA", styles['CustomTitle'])
    story.append(title)
    story.append(Spacer(1, 12))

    # Información del usuario y plan
    story.append(Paragraph("INFORMACIÓN GENERAL", styles['CustomHeading']))

    general_data = [
        ["Usuario:", f"{user.username} ({user.email})"],
        ["Plan Activo:", active_plan.titulo],
        ["Total de Cambios:", str(len(changes))],
        ["Fecha de Generación:", datetime.now().strftime('%d/%m/%Y %H:%M:%S')],
    ]

    general_table = Table(general_data, colWidths=[2*inch, 4*inch])
    general_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(general_table)
    story.append(Spacer(1, 20))

    # Lista de cambios
    if changes:
        story.append(Paragraph("LISTADO DE CAMBIOS", styles['CustomHeading']))

        # Crear tabla con todos los cambios
        table_data = [["#", "Fecha", "Columna", "Cambio", "Archivo PDF"]]

        for i, change in enumerate(changes, 1):
            fecha = change.created_at.strftime('%d/%m/%Y %H:%M')
            columna = change.get_column_display_name()
            cambio = f"{change.old_value or 'N/A'} → {change.new_value}"
            archivo = f"{change.created_at.strftime('%Y%m%d_%H%M%S')}_plan_{change.plan_id}_{change.column_name}.pdf"

            table_data.append([str(i), fecha, columna, cambio, archivo])

        # Crear tabla
        changes_table = Table(table_data, colWidths=[0.3*inch, 1.2*inch, 1.5*inch, 2*inch, 2.5*inch])
        changes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        story.append(changes_table)
    else:
        story.append(Paragraph("No se encontraron cambios registrados.", styles['CustomNormal']))

    story.append(Spacer(1, 20))

    # Pie de página
    story.append(Paragraph("=" * 80, styles['CustomNormal']))
    footer_text = f"""
    <para alignment="center">
    <font size="8" color="gray">
    Resumen autogenerado por la aplicación de gestión de planes de desarrollo<br/>
    Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br/>
    Este documento consolida todos los cambios realizados por el usuario.
    </font>
    </para>
    """
    story.append(Paragraph(footer_text, styles['CustomInfo']))

    # Generar el PDF
    try:
        doc.build(story, onFirstPage=add_watermark, onLaterPages=add_watermark)
        print(f"✅ PDF resumen de auditoría generado: {filepath}")
        return filepath
    except Exception as e:
        print(f"❌ Error generando PDF resumen de auditoría: {e}")
        return None

def convert_existing_txt_to_pdf():
    """Convertir archivos TXT existentes a PDF"""
    print("🔄 Convirtiendo archivos TXT existentes a PDF...")

    import glob

    # Buscar todos los archivos TXT de auditoría
    txt_files = glob.glob('audit_files/user_*/**/*.txt', recursive=True)

    converted = 0
    for txt_file in txt_files:
        if 'resumen_auditoria.txt' in txt_file:
            # Convertir resumen
            user_id = txt_file.split('user_')[1].split('/')[0]
            try:
                create_user_audit_summary_pdf(int(user_id))
                converted += 1
            except:
                pass
        else:
            # Para archivos individuales, necesitaríamos más lógica para reconstruir el objeto EditJustification
            # Por ahora, solo procesamos resúmenes
            pass

    print(f"✅ Convertidos {converted} archivos TXT a PDF")
    return converted

if __name__ == "__main__":
    print("🎨 Generador de PDFs de Auditoría con Marca de Agua")
    print("Funciones disponibles:")
    print("- create_audit_pdf(edit_justification): Crea PDF individual")
    print("- create_user_audit_summary_pdf(user_id): Crea resumen en PDF")
    print("- convert_existing_txt_to_pdf(): Convierte archivos existentes")
