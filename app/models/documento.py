import os
from app import db
from datetime import datetime
try:
    from werkzeug.utils import secure_filename
except ImportError:
    from werkzeug.security import safe_join
    def secure_filename(filename):
        # Implementación básica si no está disponible
        return filename.replace('/', '').replace('\\', '').replace('..', '')

class Documento(db.Model):
    __tablename__ = 'documentos'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)

    # Información del archivo
    nombre_original = db.Column(db.String(255), nullable=False)
    nombre_archivo = db.Column(db.String(255), nullable=False)  # nombre seguro del archivo
    ruta_archivo = db.Column(db.String(500), nullable=False)  # ruta completa al archivo
    tamano = db.Column(db.Integer, nullable=False)  # tamaño en bytes
    tipo_mime = db.Column(db.String(100), nullable=False)
    extension = db.Column(db.String(10), nullable=False)

    # Clasificación del documento
    tipo_documento = db.Column(db.String(50), nullable=False)  # plan, informe, evidencia, contrato, etc.
    categoria = db.Column(db.String(100))  # administrativa, tecnica, financiera, etc.
    confidencialidad = db.Column(db.String(20), default='publico')  # publico, interno, confidencial

    # Estado del documento
    estado = db.Column(db.String(20), default='activo')  # activo, archivado, eliminado
    version = db.Column(db.Integer, default=1)

    # Relaciones - un documento puede estar asociado a diferentes elementos
    plan_id = db.Column(db.Integer, db.ForeignKey('planes_desarrollo.id'), nullable=True)
    linea_estrategica_id = db.Column(db.Integer, db.ForeignKey('lineas_estrategicas.id'), nullable=True)
    componente_id = db.Column(db.Integer, db.ForeignKey('componentes.id'), nullable=True)
    programa_id = db.Column(db.Integer, db.ForeignKey('programas.id'), nullable=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyectos.id'), nullable=True)
    indicador_id = db.Column(db.Integer, db.ForeignKey('indicadores_producto.id'), nullable=True)

    # Usuario que subió el documento
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    usuario = db.relationship('User', backref=db.backref('documentos_subidos', lazy=True))

    # Fechas
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fecha_expiracion = db.Column(db.DateTime)  # fecha de expiración si aplica

    # Metadatos adicionales
    etiquetas = db.Column(db.Text)  # etiquetas separadas por comas
    numero_referencias = db.Column(db.String(50))  # número de referencia institucional
    idioma = db.Column(db.String(10), default='es')  # idioma del documento

    def __init__(self, **kwargs):
        super(Documento, self).__init__(**kwargs)
        if self.tipo_documento not in ['plan', 'informe', 'evidencia', 'contrato', 'estudio', 'foto', 'video', 'otro']:
            self.tipo_documento = 'otro'
        if self.confidencialidad not in ['publico', 'interno', 'confidencial']:
            self.confidencialidad = 'publico'
        if self.estado not in ['activo', 'archivado', 'eliminado']:
            self.estado = 'activo'

    @staticmethod
    def generar_nombre_seguro(filename):
        """Genera un nombre seguro para el archivo"""
        return secure_filename(filename)

    @staticmethod
    def get_ruta_upload(plan_id=None, linea_estrategica_id=None, componente_id=None,
                       programa_id=None, proyecto_id=None, indicador_id=None):
        """Genera la ruta de subida basada en las relaciones"""
        base_path = 'uploads'
        if plan_id:
            return f"{base_path}/planes/{plan_id}"
        elif linea_estrategica_id:
            return f"{base_path}/lineas_estrategicas/{linea_estrategica_id}"
        elif componente_id:
            return f"{base_path}/componentes/{componente_id}"
        elif programa_id:
            return f"{base_path}/programas/{programa_id}"
        elif proyecto_id:
            return f"{base_path}/proyectos/{proyecto_id}"
        elif indicador_id:
            return f"{base_path}/indicadores/{indicador_id}"
        else:
            return f"{base_path}/general"

    def get_tamano_legible(self):
        """Retorna el tamaño del archivo en formato legible"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.tamano < 1024.0:
                return ".1f"
            self.tamano /= 1024.0
        return ".1f"

    def es_imagen(self):
        """Verifica si el documento es una imagen"""
        return self.tipo_mime.startswith('image/')

    def es_pdf(self):
        """Verifica si el documento es un PDF"""
        return self.tipo_mime == 'application/pdf'

    def puede_descargar(self, usuario):
        """Verifica si un usuario puede descargar el documento"""
        if self.confidencialidad == 'publico':
            # Todos los usuarios del municipio pueden descargar
            return True
        else:  # confidencial
            # Solo el propietario, administradores o editores
            return (usuario.id == self.usuario_id or
                   usuario.is_admin() or
                   usuario.is_editor())

    def get_etiquetas_lista(self):
        """Retorna las etiquetas como una lista"""
        if not self.etiquetas:
            return []
        return [tag.strip() for tag in self.etiquetas.split(',')]

    def set_etiquetas_lista(self, etiquetas_lista):
        """Establece las etiquetas desde una lista"""
        if etiquetas_lista:
            self.etiquetas = ', '.join(etiquetas_lista)
        else:
            self.etiquetas = None

    @property
    def tipo_archivo(self):
        """Retorna el tipo de archivo basado en la extensión"""
        if not self.extension:
            return 'desconocido'

        ext = self.extension.lower()
        if ext in ['pdf']:
            return 'pdf'
        elif ext in ['doc', 'docx']:
            return ext
        elif ext in ['xls', 'xlsx']:
            return ext
        elif ext in ['ppt', 'pptx']:
            return ext
        elif ext in ['txt']:
            return 'txt'
        elif ext in ['jpg', 'jpeg', 'png', 'gif']:
            return 'imagen'
        elif ext in ['mp4', 'avi', 'mov']:
            return 'video'
        else:
            return 'otro'

    @property
    def tamano_archivo(self):
        """Alias para tamano para compatibilidad con templates"""
        return self.tamano

    def __repr__(self):
        return f'<Documento {self.titulo} - {self.tipo_documento}>'
