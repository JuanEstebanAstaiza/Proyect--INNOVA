from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, FloatField, SelectField, FileField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from app.models import PlanDesarrollo, LineaEstrategica

class PlanForm(FlaskForm):
    titulo = StringField('Título del Plan',
                        validators=[DataRequired(message='El título es obligatorio'),
                                  Length(min=5, max=200, message='El título debe tener entre 5 y 200 caracteres')])

    descripcion = TextAreaField('Descripción',
                               validators=[Optional(),
                                         Length(max=1000, message='La descripción no puede exceder 1000 caracteres')])

    anio_inicio = IntegerField('Año de Inicio',
                              validators=[DataRequired(message='El año de inicio es obligatorio'),
                                        NumberRange(min=2020, max=2030, message='El año debe estar entre 2020 y 2030')])

    anio_fin = IntegerField('Año de Fin',
                           validators=[DataRequired(message='El año de fin es obligatorio'),
                                     NumberRange(min=2020, max=2030, message='El año debe estar entre 2020 y 2030')])

    presupuesto_total = FloatField('Presupuesto Total',
                                  validators=[Optional(),
                                            NumberRange(min=0, message='El presupuesto debe ser positivo')])

    prioridad = SelectField('Prioridad',
                           choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta'), ('critica', 'Crítica')],
                           validators=[DataRequired(message='La prioridad es obligatoria')])

    submit = SubmitField('Guardar Plan')

class LineaEstrategicaForm(FlaskForm):
    cod_linea = IntegerField('Código de Línea',
                            validators=[DataRequired(message='El código es obligatorio'),
                                      NumberRange(min=1, max=999, message='El código debe estar entre 1 y 999')])

    nombre = StringField('Nombre de la Línea Estratégica',
                        validators=[DataRequired(message='El nombre es obligatorio'),
                                  Length(min=5, max=200, message='El nombre debe tener entre 5 y 200 caracteres')])

    descripcion = TextAreaField('Descripción',
                               validators=[Optional(),
                                         Length(max=1000, message='La descripción no puede exceder 1000 caracteres')])

    presupuesto_asignado = FloatField('Presupuesto Asignado',
                                     validators=[Optional(),
                                               NumberRange(min=0, message='El presupuesto debe ser positivo')])

    prioridad = SelectField('Prioridad',
                           choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta'), ('critica', 'Crítica')],
                           validators=[DataRequired(message='La prioridad es obligatoria')])

    submit = SubmitField('Crear Línea Estratégica')

class EditarLineaEstrategicaForm(FlaskForm):
    cod_linea = IntegerField('Código de Línea',
                            validators=[DataRequired(message='El código es obligatorio'),
                                      NumberRange(min=1, max=999, message='El código debe estar entre 1 y 999')])

    nombre = StringField('Nombre de la Línea Estratégica',
                        validators=[DataRequired(message='El nombre es obligatorio'),
                                  Length(min=5, max=200, message='El nombre debe tener entre 5 y 200 caracteres')])

    descripcion = TextAreaField('Descripción',
                               validators=[Optional(),
                                         Length(max=1000, message='La descripción no puede exceder 1000 caracteres')])

    presupuesto_asignado = FloatField('Presupuesto Asignado',
                                     validators=[Optional(),
                                               NumberRange(min=0, message='El presupuesto debe ser positivo')])

    prioridad = SelectField('Prioridad',
                           choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta'), ('critica', 'Crítica')],
                           validators=[DataRequired(message='La prioridad es obligatoria')])

    submit = SubmitField('Actualizar Línea Estratégica')

class ComponenteForm(FlaskForm):
    cod_componente = StringField('Código de Componente',
                                validators=[DataRequired(message='El código es obligatorio'),
                                          Length(min=3, max=10, message='El código debe tener entre 3 y 10 caracteres')])

    nombre = StringField('Nombre del Componente',
                        validators=[DataRequired(message='El nombre es obligatorio'),
                                  Length(min=5, max=200, message='El nombre debe tener entre 5 y 200 caracteres')])

    descripcion = TextAreaField('Descripción',
                               validators=[Optional(),
                                         Length(max=1000, message='La descripción no puede exceder 1000 caracteres')])

    presupuesto_asignado = FloatField('Presupuesto Asignado',
                                     validators=[Optional(),
                                               NumberRange(min=0, message='El presupuesto debe ser positivo')])

    prioridad = SelectField('Prioridad',
                           choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta'), ('critica', 'Crítica')],
                           validators=[DataRequired(message='La prioridad es obligatoria')])

    submit = SubmitField('Crear Componente')

class EditarComponenteForm(FlaskForm):
    cod_componente = StringField('Código de Componente',
                                validators=[DataRequired(message='El código es obligatorio'),
                                          Length(min=3, max=10, message='El código debe tener entre 3 y 10 caracteres')])

    nombre = StringField('Nombre del Componente',
                        validators=[DataRequired(message='El nombre es obligatorio'),
                                  Length(min=5, max=200, message='El nombre debe tener entre 5 y 200 caracteres')])

    descripcion = TextAreaField('Descripción',
                               validators=[Optional(),
                                         Length(max=1000, message='La descripción no puede exceder 1000 caracteres')])

    presupuesto_asignado = FloatField('Presupuesto Asignado',
                                     validators=[Optional(),
                                               NumberRange(min=0, message='El presupuesto debe ser positivo')])

    prioridad = SelectField('Prioridad',
                           choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta'), ('critica', 'Crítica')],
                           validators=[DataRequired(message='La prioridad es obligatoria')])

    submit = SubmitField('Actualizar Componente')

class ProgramaForm(FlaskForm):
    cod_programa = StringField('Código del Programa',
                              validators=[DataRequired(message='El código es obligatorio'),
                                        Length(min=3, max=20, message='El código debe tener entre 3 y 20 caracteres')])

    nombre = StringField('Nombre del Programa PDM',
                        validators=[DataRequired(message='El nombre es obligatorio'),
                                  Length(min=5, max=200, message='El nombre debe tener entre 5 y 200 caracteres')])

    descripcion = TextAreaField('Descripción',
                               validators=[Optional(),
                                         Length(max=1000, message='La descripción no puede exceder 1000 caracteres')])

    dependencia_responsable = StringField('Dependencia Responsable',
                                         validators=[Optional(),
                                                   Length(max=200, message='La dependencia no puede exceder 200 caracteres')])

    bpim = StringField('BPIM',
                      validators=[Optional(),
                                Length(max=20, message='BPIM no puede exceder 20 caracteres')])

    submit = SubmitField('Crear Programa')

class EditarProgramaForm(FlaskForm):
    cod_programa = StringField('Código del Programa',
                              validators=[DataRequired(message='El código es obligatorio'),
                                        Length(min=3, max=20, message='El código debe tener entre 3 y 20 caracteres')])

    nombre = StringField('Nombre del Programa PDM',
                        validators=[DataRequired(message='El nombre es obligatorio'),
                                  Length(min=5, max=200, message='El nombre debe tener entre 5 y 200 caracteres')])

    descripcion = TextAreaField('Descripción',
                               validators=[Optional(),
                                         Length(max=1000, message='La descripción no puede exceder 1000 caracteres')])

    dependencia_responsable = StringField('Dependencia Responsable',
                                         validators=[Optional(),
                                                   Length(max=200, message='La dependencia no puede exceder 200 caracteres')])

    bpim = StringField('BPIM',
                      validators=[Optional(),
                                Length(max=20, message='BPIM no puede exceder 20 caracteres')])

    submit = SubmitField('Actualizar Programa')

class ProyectoForm(FlaskForm):
    nombre = StringField('Nombre del Proyecto',
                        validators=[DataRequired(message='El nombre es obligatorio'),
                                  Length(min=5, max=200, message='El nombre debe tener entre 5 y 200 caracteres')])

    descripcion = TextAreaField('Descripción',
                               validators=[Optional(),
                                         Length(max=1000, message='La descripción no puede exceder 1000 caracteres')])

    presupuesto_total = FloatField('Presupuesto Total',
                                  validators=[Optional(),
                                            NumberRange(min=0, message='El presupuesto debe ser positivo')])

    ubicacion = StringField('Ubicación',
                           validators=[Optional(),
                                     Length(max=200, message='La ubicación no puede exceder 200 caracteres')])

    sector = StringField('Sector',
                        validators=[Optional(),
                                  Length(max=100, message='El sector no puede exceder 100 caracteres')])

    responsable_ejecucion = StringField('Responsable de Ejecución',
                                       validators=[Optional(),
                                                 Length(max=200, message='El nombre no puede exceder 200 caracteres')])

    responsable_seguimiento = StringField('Responsable de Seguimiento',
                                         validators=[Optional(),
                                                   Length(max=200, message='El nombre no puede exceder 200 caracteres')])

    submit = SubmitField('Crear Proyecto')

class EditarProyectoForm(FlaskForm):
    nombre = StringField('Nombre del Proyecto',
                        validators=[DataRequired(message='El nombre es obligatorio'),
                                  Length(min=5, max=200, message='El nombre debe tener entre 5 y 200 caracteres')])

    descripcion = TextAreaField('Descripción',
                               validators=[Optional(),
                                         Length(max=1000, message='La descripción no puede exceder 1000 caracteres')])

    presupuesto_total = FloatField('Presupuesto Total',
                                  validators=[Optional(),
                                            NumberRange(min=0, message='El presupuesto debe ser positivo')])

    ubicacion = StringField('Ubicación',
                           validators=[Optional(),
                                     Length(max=200, message='La ubicación no puede exceder 200 caracteres')])

    sector = StringField('Sector',
                        validators=[Optional(),
                                  Length(max=100, message='El sector no puede exceder 100 caracteres')])

    responsable_ejecucion = StringField('Responsable de Ejecución',
                                       validators=[Optional(),
                                                 Length(max=200, message='El nombre no puede exceder 200 caracteres')])

    responsable_seguimiento = StringField('Responsable de Seguimiento',
                                         validators=[Optional(),
                                                   Length(max=200, message='El nombre no puede exceder 200 caracteres')])

    submit = SubmitField('Actualizar Proyecto')

class IndicadorForm(FlaskForm):
    cod_indicador = StringField('Código del Indicador',
                               validators=[Optional(),
                                         Length(max=20, message='El código no puede exceder 20 caracteres')])

    nombre = StringField('Nombre del Indicador',
                        validators=[DataRequired(message='El nombre es obligatorio'),
                                  Length(min=5, max=200, message='El nombre debe tener entre 5 y 200 caracteres')])

    descripcion = TextAreaField('Descripción',
                               validators=[Optional(),
                                         Length(max=1000, message='La descripción no puede exceder 1000 caracteres')])

    tipo_indicador = StringField('Tipo de Indicador',
                                validators=[Optional(),
                                          Length(max=100, message='El tipo no puede exceder 100 caracteres')])

    linea_base = FloatField('Línea Base',
                           validators=[Optional(),
                                     NumberRange(min=0, message='La línea base debe ser positiva')])

    sentido = SelectField('Sentido',
                         choices=[('positivo', 'Positivo'), ('negativo', 'Negativo'), ('neutral', 'Neutral')],
                         validators=[DataRequired(message='El sentido es obligatorio')])

    tipologia = StringField('Tipología',
                           validators=[Optional(),
                                     Length(max=100, message='La tipología no puede exceder 100 caracteres')])

    unidad = StringField('Unidad',
                        validators=[Optional(),
                                  Length(max=50, message='La unidad no puede exceder 50 caracteres')])

    meta_cuatrienio = FloatField('Meta Cuatrienio (2024-2027)',
                                validators=[DataRequired(message='La meta es obligatoria'),
                                          NumberRange(min=0, message='La meta debe ser positiva')])

    meta_2024 = FloatField('Meta 2024',
                          validators=[Optional(),
                                    NumberRange(min=0, message='La meta debe ser positiva')])

    submit = SubmitField('Crear Indicador')

class DocumentoForm(FlaskForm):
    titulo = StringField('Título del Documento',
                        validators=[DataRequired(message='El título es obligatorio'),
                                  Length(min=3, max=200, message='El título debe tener entre 3 y 200 caracteres')])

    descripcion = TextAreaField('Descripción',
                               validators=[Optional(),
                                         Length(max=500, message='La descripción no puede exceder 500 caracteres')])

    tipo_documento = SelectField('Tipo de Documento',
                                choices=[
                                    ('plan', 'Plan'),
                                    ('informe', 'Informe'),
                                    ('evidencia', 'Evidencia'),
                                    ('contrato', 'Contrato'),
                                    ('estudio', 'Estudio'),
                                    ('foto', 'Foto'),
                                    ('video', 'Video'),
                                    ('otro', 'Otro')
                                ],
                                validators=[DataRequired(message='El tipo es obligatorio')])

    categoria = StringField('Categoría',
                           validators=[Optional(),
                                     Length(max=100, message='La categoría no puede exceder 100 caracteres')])

    confidencialidad = SelectField('Confidencialidad',
                                  choices=[
                                      ('publico', 'Público'),
                                      ('interno', 'Interno'),
                                      ('confidencial', 'Confidencial')
                                  ],
                                  validators=[DataRequired(message='La confidencialidad es obligatoria')])

    archivo = FileField('Archivo',
                       validators=[DataRequired(message='Debe seleccionar un archivo')])

    submit = SubmitField('Subir Documento')

    def validate_archivo(self, archivo):
        if archivo.data:
            # Verificar extensión del archivo
            allowed_extensions = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                                'txt', 'rtf', 'jpg', 'jpeg', 'png', 'gif', 'bmp',
                                'zip', 'rar', '7z', 'mp4', 'avi', 'mov', 'wmv'}

            filename = archivo.data.filename.lower()
            if not any(filename.endswith(ext) for ext in allowed_extensions):
                raise ValidationError('Tipo de archivo no permitido. Extensiones permitidas: ' +
                                    ', '.join(allowed_extensions))

class ActividadForm(FlaskForm):
    nombre = StringField('Nombre de la Actividad',
                        validators=[DataRequired(message='El nombre es obligatorio'),
                                  Length(min=5, max=200, message='El nombre debe tener entre 5 y 200 caracteres')])

    descripcion = TextAreaField('Descripción',
                               validators=[Optional(),
                                         Length(max=1000, message='La descripción no puede exceder 1000 caracteres')])

    tipo_actividad = SelectField('Tipo de Actividad',
                                choices=[('construccion', 'Construcción'),
                                        ('capacitacion', 'Capacitación'),
                                        ('compra', 'Compra de Equipos'),
                                        ('mantenimiento', 'Mantenimiento'),
                                        ('supervision', 'Supervisión'),
                                        ('evaluacion', 'Evaluación'),
                                        ('planificacion', 'Planificación'),
                                        ('otro', 'Otro')],
                                validators=[Optional()])

    prioridad = SelectField('Prioridad',
                           choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta'), ('critica', 'Crítica')],
                           validators=[DataRequired(message='La prioridad es obligatoria')])

    presupuesto_asignado = FloatField('Presupuesto Asignado',
                                     validators=[Optional(),
                                               NumberRange(min=0, message='El presupuesto debe ser positivo')])

    responsable_ejecucion = StringField('Responsable de Ejecución',
                                       validators=[Optional(),
                                                 Length(max=200, message='El nombre no puede exceder 200 caracteres')])

    responsable_supervision = StringField('Responsable de Supervisión',
                                         validators=[Optional(),
                                                   Length(max=200, message='El nombre no puede exceder 200 caracteres')])

    fecha_inicio = DateField('Fecha de Inicio',
                            validators=[Optional()],
                            format='%Y-%m-%d')

    fecha_fin = DateField('Fecha de Fin',
                         validators=[Optional()],
                         format='%Y-%m-%d')

    progreso_porcentual = FloatField('Progreso (%)',
                                    validators=[Optional(),
                                              NumberRange(min=0, max=100, message='El progreso debe estar entre 0 y 100')])

    observaciones = TextAreaField('Observaciones',
                                 validators=[Optional(),
                                           Length(max=1000, message='Las observaciones no pueden exceder 1000 caracteres')])

    submit = SubmitField('Crear Actividad')

class EditarActividadForm(FlaskForm):
    nombre = StringField('Nombre de la Actividad',
                        validators=[DataRequired(message='El nombre es obligatorio'),
                                  Length(min=5, max=200, message='El nombre debe tener entre 5 y 200 caracteres')])

    descripcion = TextAreaField('Descripción',
                               validators=[Optional(),
                                         Length(max=1000, message='La descripción no puede exceder 1000 caracteres')])

    tipo_actividad = SelectField('Tipo de Actividad',
                                choices=[('construccion', 'Construcción'),
                                        ('capacitacion', 'Capacitación'),
                                        ('compra', 'Compra de Equipos'),
                                        ('mantenimiento', 'Mantenimiento'),
                                        ('supervision', 'Supervisión'),
                                        ('evaluacion', 'Evaluación'),
                                        ('planificacion', 'Planificación'),
                                        ('otro', 'Otro')],
                                validators=[Optional()])

    prioridad = SelectField('Prioridad',
                           choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta'), ('critica', 'Crítica')],
                           validators=[DataRequired(message='La prioridad es obligatoria')])

    presupuesto_asignado = FloatField('Presupuesto Asignado',
                                     validators=[Optional(),
                                               NumberRange(min=0, message='El presupuesto debe ser positivo')])

    responsable_ejecucion = StringField('Responsable de Ejecución',
                                       validators=[Optional(),
                                                 Length(max=200, message='El nombre no puede exceder 200 caracteres')])

    responsable_supervision = StringField('Responsable de Supervisión',
                                         validators=[Optional(),
                                                   Length(max=200, message='El nombre no puede exceder 200 caracteres')])

    fecha_inicio = DateField('Fecha de Inicio',
                            validators=[Optional()],
                            format='%Y-%m-%d')

    fecha_fin = DateField('Fecha de Fin',
                         validators=[Optional()],
                         format='%Y-%m-%d')

    progreso_porcentual = FloatField('Progreso (%)',
                                    validators=[Optional(),
                                              NumberRange(min=0, max=100, message='El progreso debe estar entre 0 y 100')])

    observaciones = TextAreaField('Observaciones',
                                 validators=[Optional(),
                                           Length(max=1000, message='Las observaciones no pueden exceder 1000 caracteres')])

    submit = SubmitField('Actualizar Actividad')
