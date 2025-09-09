from app import db
from datetime import datetime
import os

class EditJustification(db.Model):
    __tablename__ = 'edit_justifications'

    id = db.Column(db.Integer, primary_key=True)

    # Información de la edición
    plan_id = db.Column(db.Integer, db.ForeignKey('planes_desarrollo.id'), nullable=False)
    indicador_id = db.Column(db.Integer, db.ForeignKey('indicadores_producto.id'), nullable=True)

    # Detalles de la celda editada
    column_name = db.Column(db.String(100), nullable=False)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text, nullable=False)

    # Justificación
    justification = db.Column(db.Text, nullable=False)

    # Archivo de soporte (opcional)
    support_file_path = db.Column(db.String(500))

    # Usuario que realizó la edición
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    plan = db.relationship('PlanDesarrollo', backref=db.backref('edit_justifications', lazy=True))
    indicador = db.relationship('IndicadorProducto', backref=db.backref('edit_justifications', lazy=True))
    user = db.relationship('User', backref=db.backref('edit_justifications', lazy=True))

    def __init__(self, **kwargs):
        super(EditJustification, self).__init__(**kwargs)

    def get_support_file_url(self):
        """Retorna la URL del archivo de soporte si existe"""
        if self.support_file_path and os.path.exists(self.support_file_path):
            return f"/uploads/justifications/{os.path.basename(self.support_file_path)}"
        return None

    def get_column_display_name(self):
        """Retorna el nombre legible de la columna"""
        column_names = {
            'cod_linea': 'Código de Línea',
            'lineas_estrategicas': 'Líneas Estratégicas',
            'cod_componente': 'Código de Componente',
            'componentes': 'Componentes',
            'cod_programa': 'Código de Programa',
            'programa_pdm': 'Programa PDM',
            'dependencia_responsable': 'Dependencia Responsable',
            'bpim': 'BPIM',
            'nombre_proyecto': 'Nombre del Proyecto',
            'indicadores': 'Indicadores',
            'cod_indicador_de_producto': 'Código del Indicador',
            'indicador_de_producto': 'Indicador de Producto',
            'tipo_de_indicador': 'Tipo de Indicador',
            'linea_base': 'Línea Base',
            'sentido': 'Sentido',
            'tipologia': 'Tipología',
            'unidad': 'Unidad',
            'meta_cuatrienio': 'Meta Cuatrienio',
            'meta_2024': 'Meta 2024'
        }

        # Para columnas trimestrales
        if self.column_name and '_trimestre' in self.column_name:
            parts = self.column_name.split('_')
            trimestre = parts[1] if len(parts) > 1 else '?'
            tipo = parts[0] if parts else self.column_name

            tipos_trimestrales = {
                'ejecucion': 'Ejecución',
                'cumplimiento': '% Cumplimiento',
                'poblacion_impactada': 'Población Impactada',
                'observacion': 'Observación'
            }

            return f"{tipos_trimestrales.get(tipo, tipo)} Trimestre {trimestre}"

        if self.column_name:
            return column_names.get(self.column_name, self.column_name.replace('_', ' ').title())
        else:
            return 'N/A'

    def __repr__(self):
        return f'<EditJustification {self.column_name}: {self.old_value} → {self.new_value}>'
