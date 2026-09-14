import io
import os
from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

from app import db
from app.forms.planes import (
    ActividadForm,
    ComponenteForm,
    DocumentoForm,
    EditarActividadForm,
    EditarComponenteForm,
    EditarLineaEstrategicaForm,
    EditarProgramaForm,
    EditarProyectoForm,
    LineaEstrategicaForm,
    PlanForm,
    ProgramaForm,
    ProyectoForm,
)
from app.models import (
    Actividad,
    Componente,
    Documento,
    EditJustification,
    EjecucionTrimestral,
    IndicadorProducto,
    LineaEstrategica,
    PlanDesarrollo,
    Programa,
    Proyecto,
)
from app.services.edicion_celda import (
    ValorInvalido,
    aplicar_valor,
    puede_editar,
    valor_actual,
)
from app.services.matriz_plan import (
    fila_para_exportacion,
    fila_para_vista,
    recorrer_plan,
)
from app.utils.fechas import ahora_utc


def get_documentos_asociados(plan_id=None, linea_id=None, componente_id=None,
                           programa_id=None, proyecto_id=None, indicador_id=None):
    """Obtiene documentos asociados a un elemento específico del plan"""
    filters = []
    if plan_id:
        filters.append(Documento.plan_id == plan_id)
    if linea_id:
        filters.append(Documento.linea_estrategica_id == linea_id)
    if componente_id:
        filters.append(Documento.componente_id == componente_id)
    if programa_id:
        filters.append(Documento.programa_id == programa_id)
    if proyecto_id:
        filters.append(Documento.proyecto_id == proyecto_id)
    if indicador_id:
        filters.append(Documento.indicador_id == indicador_id)

    if filters:
        query = Documento.query.filter(db.or_(*filters))
        return query.filter_by(estado='activo').order_by(Documento.fecha_subida.desc()).all()

    return []

planes_bp = Blueprint('planes', __name__, url_prefix='/planes')

def get_plan_or_404(plan_id, current_user):
    """Devuelve el plan si pertenece al municipio del usuario; si no, 404."""
    return (PlanDesarrollo.visibles_para(current_user)
            .filter(PlanDesarrollo.id == plan_id)
            .first_or_404())


def build_plan_filter(current_user):
    """Condición para limitar cualquier consulta a los planes del municipio."""
    return PlanDesarrollo.filtro_visibilidad(current_user)

def get_plan_or_redirect(plan_id, current_user, redirect_endpoint='planes.index'):
    """Devuelve el plan pedido, o redirige a otro plan del municipio si no existe.

    A diferencia de `get_plan_or_404`, aquí no se corta con un 404: se lleva al
    usuario al plan activo de su municipio (o al más reciente) con un aviso.
    """
    visibles = PlanDesarrollo.visibles_para(current_user)

    plan = visibles.filter(PlanDesarrollo.id == plan_id).first()
    if plan:
        return plan

    alternativa = (visibles.filter(PlanDesarrollo.estado == 'activo').first()
                   or visibles.order_by(PlanDesarrollo.created_at.desc()).first())

    if alternativa:
        flash('El plan solicitado no fue encontrado. Redirigiendo al plan disponible.', 'info')
        return redirect(url_for('planes.ver', plan_id=alternativa.id))

    flash('No se encontraron planes disponibles. Por favor cree un plan primero.', 'warning')
    return redirect(url_for(redirect_endpoint))


# Lista de planes
@planes_bp.route('/')
@login_required
def index():
    """Lista los planes de desarrollo del municipio del usuario."""
    planes = PlanDesarrollo.visibles_para(current_user).order_by(
        PlanDesarrollo.estado.desc(),        # los activos primero
        PlanDesarrollo.created_at.desc(),
    ).all()

    # Los editores y administradores pueden crear y gestionar planes; los
    # visualizadores solo consultarlos.
    mostrar_todos = current_user.is_admin() or current_user.is_editor()

    return render_template('planes/index.html', title='Mis Planes de Desarrollo',
                         planes=planes, mostrar_todos=mostrar_todos)

# Crear nuevo plan
@planes_bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    """Crear un nuevo plan de desarrollo"""
    form = PlanForm()
    if form.validate_on_submit():
        plan = PlanDesarrollo(
            titulo=form.titulo.data,
            descripcion=form.descripcion.data,
            anio_inicio=form.anio_inicio.data,
            anio_fin=form.anio_fin.data,
            presupuesto_total=form.presupuesto_total.data,
            prioridad=form.prioridad.data,
            municipio=current_user
        )

        db.session.add(plan)
        db.session.commit()

        flash('Plan de desarrollo creado exitosamente.', 'success')
        return redirect(url_for('planes.ver', plan_id=plan.id))

    return render_template('planes/crear.html', title='Crear Plan de Desarrollo', form=form)

# Ver plan específico
@planes_bp.route('/<int:plan_id>')
@login_required
def ver(plan_id):
    """Ver detalles de un plan específico"""
    plan = get_plan_or_redirect(plan_id, current_user)

    # Si la función retorna una redirección, devolverla
    if hasattr(plan, 'status_code'):
        return plan

    # Obtener estadísticas del plan
    lineas_count = len(plan.lineas_estrategicas)
    componentes_count = sum(len(linea.componentes) for linea in plan.lineas_estrategicas)
    programas_count = sum(len(componente.programas) for componente in
                         [comp for linea in plan.lineas_estrategicas for comp in linea.componentes])
    proyectos_count = sum(len(programa.proyectos) for programa in
                         [prog for componente in
                          [comp for linea in plan.lineas_estrategicas for comp in linea.componentes]
                          for prog in componente.programas])

    return render_template('planes/ver.html',
                          title=f'Plan: {plan.titulo}',
                          plan=plan,
                          lineas_count=lineas_count,
                          componentes_count=componentes_count,
                          programas_count=programas_count,
                          proyectos_count=proyectos_count)

# Editar plan
@planes_bp.route('/<int:plan_id>/editar', methods=['GET', 'POST'])
@login_required
def editar(plan_id):
    """Editar un plan existente"""
    plan = get_plan_or_redirect(plan_id, current_user)
    if hasattr(plan, 'status_code'):
        return plan

    form = PlanForm(obj=plan)
    if form.validate_on_submit():
        form.populate_obj(plan)
        plan.updated_at = ahora_utc()

        db.session.commit()
        flash('Plan actualizado exitosamente.', 'success')
        return redirect(url_for('planes.ver', plan_id=plan.id))

    return render_template('planes/editar.html', title='Editar Plan', form=form, plan=plan)

# Eliminar plan
@planes_bp.route('/<int:plan_id>/eliminar', methods=['POST'])
@login_required
def eliminar(plan_id):
    """Eliminar un plan"""
    plan = get_plan_or_404(plan_id, current_user)

    # No permitir eliminar planes activos
    if plan.estado == 'activo':
        flash('No se puede eliminar un plan activo. Primero desactívelo.', 'danger')
        return redirect(url_for('planes.index'))

    try:
        # Eliminar dependencias en orden correcto para evitar errores de integridad

        # 1. Eliminar permisos de fila asociados a indicadores de este plan
        from app.models import (
            Componente,
            IndicadorProducto,
            LineaEstrategica,
            Programa,
            Proyecto,
            RowPermission,
        )

        # Consulta simplificada usando joins
        subquery = db.session.query(IndicadorProducto.id)\
            .join(Proyecto, IndicadorProducto.proyecto_id == Proyecto.id)\
            .join(Programa, Proyecto.programa_id == Programa.id)\
            .join(Componente, Programa.componente_id == Componente.id)\
            .join(LineaEstrategica, Componente.linea_estrategica_id == LineaEstrategica.id)\
            .filter(LineaEstrategica.plan_id == plan.id)\
            .subquery()

        RowPermission.query.filter(
            RowPermission.indicador_id.in_(subquery)
        ).delete(synchronize_session=False)

        # 2. Eliminar permisos de columna (si existen)
        # Nota: ColumnPermission no tiene relación directa con planes, así que no necesitamos eliminarlos

        # 3. Eliminar sesiones activas relacionadas (si existen)
        # Las sesiones activas no están directamente relacionadas con planes

        # 4. Eliminar logs de actividad relacionados (opcional)
        # Los logs pueden ser útiles para auditoría, así que los mantenemos

        # 5. Ahora sí podemos eliminar el plan de forma segura
        db.session.delete(plan)
        db.session.commit()

        flash('Plan eliminado exitosamente.', 'success')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error eliminando plan {plan_id}: {e!s}')
        flash('Error al eliminar el plan. Inténtalo de nuevo.', 'danger')

    return redirect(url_for('planes.index'))

# Activar plan
@planes_bp.route('/<int:plan_id>/activar', methods=['POST'])
@login_required
def activar_plan(plan_id):
    """Activar un plan (desactiva automáticamente los demás)"""
    plan = get_plan_or_404(plan_id, current_user)

    plan.activar()

    flash(f'Plan "{plan.titulo}" activado exitosamente. Los demás planes han sido desactivados.', 'success')
    return redirect(url_for('planes.index'))

# Desactivar plan
@planes_bp.route('/<int:plan_id>/desactivar', methods=['POST'])
@login_required
def desactivar_plan(plan_id):
    """Desactivar un plan"""
    plan = get_plan_or_404(plan_id, current_user)

    plan.desactivar()

    flash(f'Plan "{plan.titulo}" desactivado exitosamente.', 'success')
    return redirect(url_for('planes.index'))

# ==================== LÍNEAS ESTRATÉGICAS ====================

@planes_bp.route('/<int:plan_id>/lineas')
@login_required
def lineas(plan_id):
    """Ver líneas estratégicas de un plan"""
    plan = get_plan_or_404(plan_id, current_user)
    return render_template('planes/lineas.html', title='Líneas Estratégicas', plan=plan)

@planes_bp.route('/<int:plan_id>/lineas/crear', methods=['GET', 'POST'])
@login_required
def crear_linea(plan_id):
    """Crear nueva línea estratégica"""
    plan = get_plan_or_404(plan_id, current_user)

    form = LineaEstrategicaForm()
    if form.validate_on_submit():
        linea = LineaEstrategica(
            cod_linea=form.cod_linea.data,
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            presupuesto_asignado=form.presupuesto_asignado.data,
            prioridad=form.prioridad.data,
            plan=plan
        )

        db.session.add(linea)
        db.session.commit()

        flash('Línea estratégica creada exitosamente.', 'success')
        return redirect(url_for('planes.lineas', plan_id=plan_id))

    return render_template('planes/crear_linea.html', title='Crear Línea Estratégica', form=form, plan=plan)

@planes_bp.route('/lineas/<int:linea_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_linea(linea_id):
    """Editar línea estratégica existente"""
    linea = LineaEstrategica.query.join(PlanDesarrollo).filter(
        LineaEstrategica.id == linea_id,
        build_plan_filter(current_user)
    ).first_or_404()

    # Temporalmente deshabilitado para pruebas
    # if not current_user.can_edit_column('CÓD LINEA'):
    #     flash('No tienes permisos para editar líneas estratégicas.', 'danger')
    #     return redirect(url_for('planes.lineas', plan_id=linea.plan_id))

    form = EditarLineaEstrategicaForm(obj=linea)
    if form.validate_on_submit():
        try:
            linea.cod_linea = form.cod_linea.data
            linea.nombre = form.nombre.data
            linea.descripcion = form.descripcion.data
            linea.presupuesto_asignado = form.presupuesto_asignado.data
            linea.prioridad = form.prioridad.data

            db.session.commit()
            flash(f'Línea estratégica "{linea.nombre}" actualizada exitosamente.', 'success')
            return redirect(url_for('planes.lineas', plan_id=linea.plan_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la línea estratégica: {e!s}', 'danger')

    return render_template('planes/editar_linea.html', title='Editar Línea Estratégica',
                          form=form, linea=linea, plan=linea.plan)

@planes_bp.route('/lineas/<int:linea_id>/detalles')
@login_required
def detalles_linea(linea_id):
    """Ver detalles completos de una línea estratégica"""
    linea = LineaEstrategica.query.join(PlanDesarrollo).filter(
        LineaEstrategica.id == linea_id,
        build_plan_filter(current_user)
    ).first_or_404()

    # Calcular estadísticas para el template
    total_programas = sum(len(componente.programas) for componente in linea.componentes)
    total_proyectos = sum(len(programa.proyectos) for componente in linea.componentes for programa in componente.programas)
    total_actividades = sum(len(proyecto.actividades) for componente in linea.componentes for programa in componente.programas for proyecto in programa.proyectos)

    return render_template('planes/detalles_linea.html', title='Detalles de Línea Estratégica',
                          linea=linea, plan=linea.plan,
                          total_programas=total_programas,
                          total_proyectos=total_proyectos,
                          total_actividades=total_actividades)

# ==================== COMPONENTES ====================

@planes_bp.route('/lineas/<int:linea_id>/componentes')
@login_required
def componentes(linea_id):
    """Ver componentes de una línea estratégica"""
    linea = LineaEstrategica.query.join(PlanDesarrollo).filter(
        LineaEstrategica.id == linea_id,
        build_plan_filter(current_user)
    ).first_or_404()

    return render_template('planes/componentes.html', title='Componentes', linea=linea)

@planes_bp.route('/lineas/<int:linea_id>/componentes/crear', methods=['GET', 'POST'])
@login_required
def crear_componente(linea_id):
    """Crear nuevo componente"""
    linea = LineaEstrategica.query.join(PlanDesarrollo).filter(
        LineaEstrategica.id == linea_id,
        build_plan_filter(current_user)
    ).first_or_404()

    form = ComponenteForm()
    if form.validate_on_submit():
        componente = Componente(
            cod_componente=form.cod_componente.data,
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            presupuesto_asignado=form.presupuesto_asignado.data,
            prioridad=form.prioridad.data,
            linea_estrategica=linea
        )

        db.session.add(componente)
        db.session.commit()

        flash('Componente creado exitosamente.', 'success')
        return redirect(url_for('planes.componentes', linea_id=linea_id))

    return render_template('planes/crear_componente.html', title='Crear Componente', form=form, linea=linea)

@planes_bp.route('/componentes/<int:componente_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_componente(componente_id):
    """Editar componente existente"""
    componente = Componente.query.join(LineaEstrategica).join(PlanDesarrollo).filter(
        Componente.id == componente_id,
        PlanDesarrollo.filtro_visibilidad(current_user)
    ).first_or_404()

    if not current_user.can_edit_column('CÓD COMPONENTE'):
        flash('No tienes permisos para editar componentes.', 'danger')
        return redirect(url_for('planes.componentes', linea_id=componente.linea_estrategica_id))

    form = EditarComponenteForm(obj=componente)
    if form.validate_on_submit():
        try:
            componente.cod_componente = form.cod_componente.data
            componente.nombre = form.nombre.data
            componente.descripcion = form.descripcion.data
            componente.presupuesto_asignado = form.presupuesto_asignado.data
            componente.prioridad = form.prioridad.data

            db.session.commit()
            flash(f'Componente "{componente.nombre}" actualizado exitosamente.', 'success')
            return redirect(url_for('planes.componentes', linea_id=componente.linea_estrategica_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el componente: {e!s}', 'danger')

    return render_template('planes/editar_componente.html', title='Editar Componente',
                          form=form, componente=componente, linea=componente.linea_estrategica)

@planes_bp.route('/componentes/<int:componente_id>/detalles')
@login_required
def detalles_componente(componente_id):
    """Ver detalles completos de un componente"""
    componente = Componente.query.join(LineaEstrategica).join(PlanDesarrollo).filter(
        Componente.id == componente_id,
        PlanDesarrollo.filtro_visibilidad(current_user)
    ).first_or_404()

    # Calcular estadísticas para el template
    total_proyectos = sum(len(programa.proyectos) for programa in componente.programas)
    total_actividades = sum(len(proyecto.actividades) for programa in componente.programas for proyecto in programa.proyectos)
    total_indicadores = sum(len(proyecto.indicadores) for programa in componente.programas for proyecto in programa.proyectos)

    return render_template('planes/detalles_componente.html', title='Detalles del Componente',
                          componente=componente, linea=componente.linea_estrategica,
                          total_proyectos=total_proyectos,
                          total_actividades=total_actividades,
                          total_indicadores=total_indicadores)

# ==================== PROGRAMAS ====================

@planes_bp.route('/componentes/<int:componente_id>/programas')
@login_required
def programas(componente_id):
    """Ver programas de un componente"""
    componente = Componente.query.join(LineaEstrategica).join(PlanDesarrollo).filter(
        Componente.id == componente_id
    ).first_or_404()

    return render_template('planes/programas.html', title='Programas PDM', componente=componente)

@planes_bp.route('/componentes/<int:componente_id>/programas/crear', methods=['GET', 'POST'])
@login_required
def crear_programa(componente_id):
    """Crear nuevo programa"""
    componente = Componente.query.join(LineaEstrategica).join(PlanDesarrollo).filter(
        Componente.id == componente_id
    ).first_or_404()

    # Verificar permisos
    if not current_user.can_edit_column('CÓD PROGRAMA'):
        flash('No tienes permisos para crear programas.', 'danger')
        return redirect(url_for('planes.programas', componente_id=componente_id))

    form = ProgramaForm()
    if form.validate_on_submit():
        try:
            programa = Programa(
                cod_programa=form.cod_programa.data,
                nombre=form.nombre.data,
                descripcion=form.descripcion.data,
                dependencia_responsable=form.dependencia_responsable.data,
                bpim=form.bpim.data,
                componente_id=componente_id
            )

            db.session.add(programa)
            db.session.commit()

            flash(f'Programa "{programa.nombre}" creado exitosamente.', 'success')
            return redirect(url_for('planes.programas', componente_id=componente_id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el programa: {e!s}', 'danger')

    return render_template('planes/crear_programa.html', title='Crear Programa', form=form, componente=componente)

@planes_bp.route('/programas/<int:programa_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_programa(programa_id):
    """Editar programa existente"""
    programa = Programa.query.join(Componente).join(LineaEstrategica).join(PlanDesarrollo).filter(
        Programa.id == programa_id,
        PlanDesarrollo.filtro_visibilidad(current_user)
    ).first_or_404()

    if not current_user.can_edit_column('CÓD PROGRAMA'):
        flash('No tienes permisos para editar programas.', 'danger')
        return redirect(url_for('planes.programas', componente_id=programa.componente_id))

    form = EditarProgramaForm(obj=programa)
    if form.validate_on_submit():
        try:
            programa.cod_programa = form.cod_programa.data
            programa.nombre = form.nombre.data
            programa.descripcion = form.descripcion.data
            programa.dependencia_responsable = form.dependencia_responsable.data
            programa.bpim = form.bpim.data

            db.session.commit()
            flash(f'Programa "{programa.nombre}" actualizado exitosamente.', 'success')
            return redirect(url_for('planes.programas', componente_id=programa.componente_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el programa: {e!s}', 'danger')

    return render_template('planes/editar_programa.html', title='Editar Programa',
                          form=form, programa=programa, componente=programa.componente)

@planes_bp.route('/programas/<int:programa_id>/detalles')
@login_required
def detalles_programa(programa_id):
    """Ver detalles completos de un programa"""
    programa = Programa.query.join(Componente).join(LineaEstrategica).join(PlanDesarrollo).filter(
        Programa.id == programa_id,
        PlanDesarrollo.filtro_visibilidad(current_user)
    ).first_or_404()

    # Calcular estadísticas para el template
    total_actividades = sum(len(proyecto.actividades) for proyecto in programa.proyectos)
    total_indicadores = sum(len(proyecto.indicadores) for proyecto in programa.proyectos)

    return render_template('planes/detalles_programa.html', title='Detalles del Programa',
                          programa=programa, componente=programa.componente,
                          total_actividades=total_actividades,
                          total_indicadores=total_indicadores)

# ==================== PROYECTOS ====================

@planes_bp.route('/programas/<int:programa_id>/proyectos')
@login_required
def proyectos(programa_id):
    """Ver proyectos de un programa"""
    programa = Programa.query.join(Componente).join(LineaEstrategica).join(PlanDesarrollo).filter(
        Programa.id == programa_id
    ).first_or_404()

    return render_template('planes/proyectos.html', title='Proyectos', programa=programa)

@planes_bp.route('/programas/<int:programa_id>/proyectos/crear', methods=['GET', 'POST'])
@login_required
def crear_proyecto(programa_id):
    """Crear nuevo proyecto"""
    programa = Programa.query.join(Componente).join(LineaEstrategica).join(PlanDesarrollo).filter(
        Programa.id == programa_id
    ).first_or_404()

    # Verificar permisos
    if not current_user.can_edit_column('CÓD PROYECTO'):
        flash('No tienes permisos para crear proyectos.', 'danger')
        return redirect(url_for('planes.proyectos', programa_id=programa_id))

    form = ProyectoForm()
    if form.validate_on_submit():
        try:
            proyecto = Proyecto(
                nombre=form.nombre.data,
                descripcion=form.descripcion.data,
                presupuesto_total=form.presupuesto_total.data or 0.0,
                presupuesto_ejecutado=0.0,  # Inicialmente 0
                ubicacion=form.ubicacion.data,
                sector=form.sector.data,
                responsable_ejecucion=form.responsable_ejecucion.data,
                responsable_seguimiento=form.responsable_seguimiento.data,
                programa_id=programa_id
            )

            db.session.add(proyecto)
            db.session.commit()

            flash(f'Proyecto "{proyecto.nombre}" creado exitosamente.', 'success')
            return redirect(url_for('planes.proyectos', programa_id=programa_id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el proyecto: {e!s}', 'danger')

    return render_template('planes/crear_proyecto.html', title='Crear Proyecto', form=form, programa=programa)

@planes_bp.route('/proyectos/<int:proyecto_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_proyecto(proyecto_id):
    """Editar proyecto existente"""
    proyecto = Proyecto.query.join(Programa).join(Componente).join(LineaEstrategica).join(PlanDesarrollo).filter(
        Proyecto.id == proyecto_id,
        PlanDesarrollo.filtro_visibilidad(current_user)
    ).first_or_404()

    if not current_user.can_edit_column('CÓD PROYECTO'):
        flash('No tienes permisos para editar proyectos.', 'danger')
        return redirect(url_for('planes.proyectos', programa_id=proyecto.programa_id))

    form = EditarProyectoForm(obj=proyecto)
    if form.validate_on_submit():
        try:
            proyecto.nombre = form.nombre.data
            proyecto.descripcion = form.descripcion.data
            proyecto.presupuesto_total = form.presupuesto_total.data or 0.0
            proyecto.ubicacion = form.ubicacion.data
            proyecto.sector = form.sector.data
            proyecto.responsable_ejecucion = form.responsable_ejecucion.data
            proyecto.responsable_seguimiento = form.responsable_seguimiento.data

            db.session.commit()
            flash(f'Proyecto "{proyecto.nombre}" actualizado exitosamente.', 'success')
            return redirect(url_for('planes.proyectos', programa_id=proyecto.programa_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el proyecto: {e!s}', 'danger')

    return render_template('planes/editar_proyecto.html', title='Editar Proyecto',
                          form=form, proyecto=proyecto, programa=proyecto.programa)

@planes_bp.route('/proyectos/<int:proyecto_id>/detalles')
@login_required
def detalles_proyecto(proyecto_id):
    """Ver detalles completos de un proyecto"""
    proyecto = Proyecto.query.join(Programa).join(Componente).join(LineaEstrategica).join(PlanDesarrollo).filter(
        Proyecto.id == proyecto_id,
        PlanDesarrollo.filtro_visibilidad(current_user)
    ).first_or_404()

    # Calcular estadísticas para el template
    total_indicadores = len(proyecto.indicadores)

    return render_template('planes/detalles_proyecto.html', title='Detalles del Proyecto',
                          proyecto=proyecto, programa=proyecto.programa,
                          total_indicadores=total_indicadores)

# ==================== ACTIVIDADES ====================

@planes_bp.route('/proyectos/<int:proyecto_id>/actividades')
@login_required
def actividades(proyecto_id):
    """Ver actividades de un proyecto"""
    proyecto = Proyecto.query.join(Programa).join(Componente).join(LineaEstrategica).join(PlanDesarrollo).filter(
        Proyecto.id == proyecto_id
    ).first_or_404()

    return render_template('planes/actividades.html', title='Actividades', proyecto=proyecto)

@planes_bp.route('/proyectos/<int:proyecto_id>/indicadores')
@login_required
def indicadores_proyecto(proyecto_id):
    """Ver indicadores de un proyecto"""
    proyecto = Proyecto.query.join(Programa).join(Componente).join(LineaEstrategica).join(PlanDesarrollo).filter(
        Proyecto.id == proyecto_id
    ).first_or_404()

    return render_template('planes/indicadores_proyecto.html', title='Indicadores del Proyecto', proyecto=proyecto)

@planes_bp.route('/proyectos/<int:proyecto_id>/indicadores/<int:indicador_id>')
@login_required
def detalles_indicador(proyecto_id, indicador_id):
    """Ver detalles de un indicador específico"""
    proyecto = Proyecto.query.join(Programa).join(Componente).join(LineaEstrategica).join(PlanDesarrollo).filter(
        Proyecto.id == proyecto_id
    ).first_or_404()

    indicador = IndicadorProducto.query.filter_by(
        id=indicador_id,
        proyecto_id=proyecto_id
    ).first_or_404()

    return render_template('planes/detalles_indicador.html',
                         title=f'Detalles del Indicador: {indicador.nombre}',
                         proyecto=proyecto,
                         indicador=indicador)

@planes_bp.route('/proyectos/<int:proyecto_id>/actividades/crear', methods=['GET', 'POST'])
@login_required
def crear_actividad(proyecto_id):
    """Crear nueva actividad"""
    proyecto = Proyecto.query.join(Programa).join(Componente).join(LineaEstrategica).join(PlanDesarrollo).filter(
        Proyecto.id == proyecto_id
    ).first_or_404()

    # Verificar permisos
    if not current_user.can_edit_column('NOMBRE PROYECTO'):
        flash('No tienes permisos para crear actividades.', 'danger')
        return redirect(url_for('planes.actividades', proyecto_id=proyecto_id))

    form = ActividadForm()
    if form.validate_on_submit():
        try:
            actividad = Actividad(
                nombre=form.nombre.data,
                descripcion=form.descripcion.data,
                tipo_actividad=form.tipo_actividad.data,
                prioridad=form.prioridad.data,
                presupuesto_asignado=form.presupuesto_asignado.data or 0.0,
                responsable_ejecucion=form.responsable_ejecucion.data,
                responsable_supervision=form.responsable_supervision.data,
                fecha_inicio=form.fecha_inicio.data,
                fecha_fin=form.fecha_fin.data,
                progreso_porcentual=form.progreso_porcentual.data or 0.0,
                observaciones=form.observaciones.data,
                proyecto_id=proyecto_id
            )

            db.session.add(actividad)
            db.session.commit()

            flash(f'Actividad "{actividad.nombre}" creada exitosamente.', 'success')
            return redirect(url_for('planes.actividades', proyecto_id=proyecto_id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la actividad: {e!s}', 'danger')

    return render_template('planes/crear_actividad.html', title='Crear Actividad', form=form, proyecto=proyecto)

@planes_bp.route('/actividades/<int:actividad_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_actividad(actividad_id):
    """Editar actividad existente"""
    actividad = Actividad.query.join(Proyecto).join(Programa).join(Componente).join(LineaEstrategica).join(PlanDesarrollo).filter(
        Actividad.id == actividad_id,
        PlanDesarrollo.filtro_visibilidad(current_user)
    ).first_or_404()

    if not current_user.can_edit_column('NOMBRE PROYECTO'):  # Usando el mismo permiso que para crear
        flash('No tienes permisos para editar actividades.', 'danger')
        return redirect(url_for('planes.actividades', proyecto_id=actividad.proyecto_id))

    form = EditarActividadForm(obj=actividad)
    if form.validate_on_submit():
        try:
            actividad.nombre = form.nombre.data
            actividad.descripcion = form.descripcion.data
            actividad.tipo_actividad = form.tipo_actividad.data
            actividad.prioridad = form.prioridad.data
            actividad.presupuesto_asignado = form.presupuesto_asignado.data or 0.0
            actividad.responsable_ejecucion = form.responsable_ejecucion.data
            actividad.responsable_supervision = form.responsable_supervision.data
            actividad.fecha_inicio = form.fecha_inicio.data
            actividad.fecha_fin = form.fecha_fin.data
            actividad.progreso_porcentual = form.progreso_porcentual.data or 0.0
            actividad.observaciones = form.observaciones.data

            # Actualizar el estado basado en el progreso
            if actividad.progreso_porcentual >= 100:
                actividad.estado = 'completada'
            elif actividad.progreso_porcentual > 0:
                actividad.estado = 'en_progreso'
            else:
                actividad.estado = 'planificada'

            db.session.commit()
            flash(f'Actividad "{actividad.nombre}" actualizada exitosamente.', 'success')
            return redirect(url_for('planes.actividades', proyecto_id=actividad.proyecto_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la actividad: {e!s}', 'danger')

    return render_template('planes/editar_actividad.html', title='Editar Actividad',
                          form=form, actividad=actividad, proyecto=actividad.proyecto)

@planes_bp.route('/actividades/<int:actividad_id>/detalles')
@login_required
def detalles_actividad(actividad_id):
    """Ver detalles completos de una actividad"""
    actividad = Actividad.query.join(Proyecto).join(Programa).join(Componente).join(LineaEstrategica).join(PlanDesarrollo).filter(
        Actividad.id == actividad_id,
        PlanDesarrollo.filtro_visibilidad(current_user)
    ).first_or_404()

    return render_template('planes/detalles_actividad.html', title='Detalles de la Actividad',
                          actividad=actividad, proyecto=actividad.proyecto)

# ==================== VISTA EXCEL ====================

@planes_bp.route('/<int:plan_id>/excel')
@login_required
def ver_excel(plan_id):
    """Muestra el plan como la matriz del PDM, con los permisos del usuario."""
    plan = get_plan_or_redirect(plan_id, current_user)
    if hasattr(plan, 'status_code'):
        return plan

    user_editable_columns = current_user.get_editable_columns()
    user_viewable_columns = current_user.get_viewable_columns()

    excel_data = []
    for fila in recorrer_plan(plan):
        registro = fila_para_vista(fila)

        documentos = {
            'documentos_linea': len(get_documentos_asociados(linea_id=fila.linea.id)),
            'documentos_componente': len(get_documentos_asociados(componente_id=fila.componente.id)),
            'documentos_programa': len(get_documentos_asociados(programa_id=fila.programa.id)),
            'documentos_proyecto': len(get_documentos_asociados(proyecto_id=fila.proyecto.id)),
            'documentos_indicador': (
                len(get_documentos_asociados(indicador_id=fila.indicador.id))
                if fila.indicador else 0
            ),
        }
        registro.update(documentos)
        registro['total_documentos'] = sum(documentos.values())

        # Permisos de fila: se resuelven por indicador.
        registro['_indicador_id'] = fila.indicador.id if fila.indicador else None
        registro['_can_edit_row'] = (
            current_user.can_edit_row(fila.indicador.id, plan.id) if fila.indicador else False
        )

        excel_data.append(registro)

    # Un plan sin indicadores muestra la matriz vacía: inventar una fila de
    # ejemplo haría pasar datos ficticios por datos reales del plan.
    return render_template('planes/excel_view.html',
                           title=f'Plan Excel: {plan.titulo}',
                           plan=plan,
                           excel_data=excel_data,
                           user_editable_columns=user_editable_columns,
                           user_viewable_columns=user_viewable_columns)


# ==================== IMPORTAR/EXPORTAR EXCEL ====================

@planes_bp.route('/<int:plan_id>/exportar-excel')
@login_required
def exportar_excel(plan_id):
    """Descarga el plan completo como archivo .xlsx."""
    try:
        import pandas as pd
    except ImportError:
        flash('La funcionalidad de Excel requiere instalar pandas. Contacte al administrador.', 'error')
        return redirect(url_for('planes.ver', plan_id=plan_id))

    plan = get_plan_or_404(plan_id, current_user)

    df = pd.DataFrame([fila_para_exportacion(fila) for fila in recorrer_plan(plan)])

    # Crear archivo Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Plan Desarrollo', index=False)

    output.seek(0)

    # Nombre del archivo
    filename = f"plan_desarrollo_{plan.titulo.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@planes_bp.route('/<int:plan_id>/importar-excel', methods=['POST'])
@login_required
def importar_excel(plan_id):
    """Importar datos desde archivo Excel"""
    try:
        import pandas as pd
    except ImportError:
        flash('La funcionalidad de Excel requiere instalar pandas. Contacte al administrador.', 'error')
        return redirect(url_for('planes.ver_excel', plan_id=plan_id))

    # Comprueba que el plan existe y pertenece al municipio del usuario.
    get_plan_or_404(plan_id, current_user)

    if 'excel_file' not in request.files:
        flash('No se encontró el archivo.', 'error')
        return redirect(url_for('planes.ver_excel', plan_id=plan_id))

    file = request.files['excel_file']
    if file.filename == '':
        flash('No se seleccionó ningún archivo.', 'error')
        return redirect(url_for('planes.ver_excel', plan_id=plan_id))

    if not file.filename.endswith(('.xlsx', '.xls')):
        flash('El archivo debe ser un Excel (.xlsx o .xls).', 'error')
        return redirect(url_for('planes.ver_excel', plan_id=plan_id))

    try:
        # Leer el archivo Excel
        df = pd.read_excel(file)

        # Procesar cada fila del Excel
        filas_procesadas = 0
        for _, row in df.iterrows():
            try:
                # Buscar o crear línea estratégica
                linea = LineaEstrategica.query.filter_by(
                    plan_id=plan_id,
                    cod_linea=int(row.get('CÓD LINEA', 0))
                ).first()

                if not linea:
                    linea = LineaEstrategica(
                        plan_id=plan_id,
                        cod_linea=int(row.get('CÓD LINEA', 0)),
                        nombre=str(row.get('LINEAS ESTRATEGICAS', '')),
                        presupuesto_asignado=0.0
                    )
                    db.session.add(linea)
                    db.session.flush()

                # Buscar o crear componente
                componente = Componente.query.filter_by(
                    linea_estrategica_id=linea.id,
                    cod_componente=str(row.get('CÓD COMPONENTE', ''))
                ).first()

                if not componente:
                    componente = Componente(
                        linea_estrategica_id=linea.id,
                        cod_componente=str(row.get('CÓD COMPONENTE', '')),
                        nombre=str(row.get('COMPONENTES', '')),
                        presupuesto_asignado=0.0
                    )
                    db.session.add(componente)
                    db.session.flush()

                # Buscar o crear programa
                programa = Programa.query.filter_by(
                    componente_id=componente.id,
                    cod_programa=str(row.get('CÓD PROGRAMA', ''))
                ).first()

                if not programa:
                    programa = Programa(
                        componente_id=componente.id,
                        cod_programa=str(row.get('CÓD PROGRAMA', '')),
                        nombre=str(row.get('PROGRAMA PDM', '')),
                        dependencia_responsable=str(row.get('DEPENDENCIA RESPOSABLE', '')),
                        bpim=str(row.get('BPIM', ''))
                    )
                    db.session.add(programa)
                    db.session.flush()

                # Buscar o crear proyecto
                proyecto = Proyecto.query.filter_by(
                    programa_id=programa.id,
                    nombre=str(row.get('NOMBRE PROYECTO', ''))
                ).first()

                if not proyecto:
                    proyecto = Proyecto(
                        programa_id=programa.id,
                        nombre=str(row.get('NOMBRE PROYECTO', '')),
                        presupuesto_total=0.0
                    )
                    db.session.add(proyecto)
                    db.session.flush()

                # Buscar o crear indicador
                indicador = IndicadorProducto.query.filter_by(
                    proyecto_id=proyecto.id,
                    cod_indicador=str(row.get('CÓD INDICADOR DE PRODUCTO', ''))
                ).first()

                if not indicador:
                    indicador = IndicadorProducto(
                        proyecto_id=proyecto.id,
                        cod_indicador=str(row.get('CÓD INDICADOR DE PRODUCTO', '')),
                        nombre=str(row.get('INDICADOR DE PRODUCTO', '')),
                        tipo_indicador=str(row.get('TIPO DE INDICADOR', '')),
                        linea_base=float(row.get('LINEA BASE', 0.0)),
                        sentido=str(row.get('SENTIDO', 'positivo')),
                        tipologia=str(row.get('TIPOLOGÍA', '')),
                        unidad=str(row.get('UNIDAD', '')),
                        meta_cuatrienio=float(row.get('META CUATRIENIO (2024-2027)', 0.0)),
                        meta_2024=float(row.get('META 2024', 0.0))
                    )
                    db.session.add(indicador)
                    db.session.flush()

                # Crear o actualizar ejecuciones trimestrales
                for trimestre in range(1, 5):
                    ejecucion_existente = EjecucionTrimestral.query.filter_by(
                        indicador_id=indicador.id,
                        anio=2024,
                        trimestre=trimestre
                    ).first()

                    ejecucion_data = {
                        'ejecucion_trimestral': float(row.get(f'EJECUCIÓN {trimestre} TRIMESTRE', 0.0)),
                        'cumplimiento_trimestral': float(row.get(f'% CUMPLIMIENTO {trimestre} TRIMESTRE', 0.0)),
                        'poblacion_impactada_trimestral': int(row.get(f'POBLACIÓN IMPACTADA POR SECTOR {trimestre} TRIMESTRE', 0)),
                        'observacion_trimestral': str(row.get(f'OBSERVACIÓN AL CUMPLIMIENTO {trimestre}TRIMESTRE', ''))
                    }

                    if ejecucion_existente:
                        # Actualizar ejecución existente
                        for key, value in ejecucion_data.items():
                            setattr(ejecucion_existente, key, value)
                    else:
                        # Crear nueva ejecución
                        nueva_ejecucion = EjecucionTrimestral(
                            indicador_id=indicador.id,
                            proyecto_id=proyecto.id,
                            usuario_id=current_user.id,
                            anio=2024,
                            trimestre=trimestre,
                            **ejecucion_data
                        )
                        db.session.add(nueva_ejecucion)

                filas_procesadas += 1

            except Exception as e:
                print(f"Error procesando fila: {e}")
                continue

        db.session.commit()
        flash(f'Se procesaron exitosamente {filas_procesadas} filas del archivo Excel.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al procesar el archivo Excel: {e!s}', 'error')

    return redirect(url_for('planes.ver_excel', plan_id=plan_id))

@planes_bp.route('/<int:plan_id>/guardar-excel', methods=['POST'])
@login_required
def guardar_excel(plan_id):
    """Guardar cambios desde la vista Excel"""
    from flask import jsonify

    # Comprueba que el plan existe y pertenece al municipio del usuario.
    get_plan_or_404(plan_id, current_user)

    try:
        data = request.get_json()
        excel_data = data.get('excel_data', [])

        # Procesar cada fila de datos
        for fila_data in excel_data:
            try:
                # Buscar o crear línea estratégica
                linea = LineaEstrategica.query.filter_by(
                    plan_id=plan_id,
                    cod_linea=int(fila_data.get('cod_linea', 0))
                ).first()

                if not linea and fila_data.get('cod_linea'):
                    linea = LineaEstrategica(
                        plan_id=plan_id,
                        cod_linea=int(fila_data.get('cod_linea', 0)),
                        nombre=str(fila_data.get('lineas_estrategicas', '')),
                        presupuesto_asignado=0.0
                    )
                    db.session.add(linea)
                    db.session.flush()

                if linea:
                    # Buscar o crear componente
                    componente = Componente.query.filter_by(
                        linea_estrategica_id=linea.id,
                        cod_componente=str(fila_data.get('cod_componente', ''))
                    ).first()

                    if not componente and fila_data.get('cod_componente'):
                        componente = Componente(
                            linea_estrategica_id=linea.id,
                            cod_componente=str(fila_data.get('cod_componente', '')),
                            nombre=str(fila_data.get('componentes', '')),
                            presupuesto_asignado=0.0
                        )
                        db.session.add(componente)
                        db.session.flush()

                    if componente:
                        # Buscar o crear programa
                        programa = Programa.query.filter_by(
                            componente_id=componente.id,
                            cod_programa=str(fila_data.get('cod_programa', ''))
                        ).first()

                        if not programa and fila_data.get('cod_programa'):
                            programa = Programa(
                                componente_id=componente.id,
                                cod_programa=str(fila_data.get('cod_programa', '')),
                                nombre=str(fila_data.get('programa_pdm', '')),
                                dependencia_responsable=str(fila_data.get('dependencia_responsable', '')),
                                bpim=str(fila_data.get('bpim', ''))
                            )
                            db.session.add(programa)
                            db.session.flush()

                        if programa:
                            # Buscar o crear proyecto
                            proyecto = Proyecto.query.filter_by(
                                programa_id=programa.id,
                                nombre=str(fila_data.get('nombre_proyecto', ''))
                            ).first()

                            if not proyecto and fila_data.get('nombre_proyecto'):
                                proyecto = Proyecto(
                                    programa_id=programa.id,
                                    nombre=str(fila_data.get('nombre_proyecto', '')),
                                    presupuesto_total=0.0
                                )
                                db.session.add(proyecto)
                                db.session.flush()

                            if proyecto:
                                # Buscar o crear indicador
                                indicador = IndicadorProducto.query.filter_by(
                                    proyecto_id=proyecto.id,
                                    cod_indicador=str(fila_data.get('cod_indicador_de_producto', ''))
                                ).first()

                                if not indicador and fila_data.get('cod_indicador_de_producto'):
                                    indicador = IndicadorProducto(
                                        proyecto_id=proyecto.id,
                                        cod_indicador=str(fila_data.get('cod_indicador_de_producto', '')),
                                        nombre=str(fila_data.get('indicador_de_producto', '')),
                                        tipo_indicador=str(fila_data.get('tipo_de_indicador', '')),
                                        linea_base=float(fila_data.get('linea_base', 0.0)),
                                        sentido=str(fila_data.get('sentido', 'positivo')),
                                        tipologia=str(fila_data.get('tipologia', '')),
                                        unidad=str(fila_data.get('unidad', '')),
                                        meta_cuatrienio=float(fila_data.get('meta_cuatrienio', 0.0)),
                                        meta_2024=float(fila_data.get('meta_2024', 0.0))
                                    )
                                    db.session.add(indicador)
                                    db.session.flush()

                                if indicador:
                                    # Actualizar ejecuciones trimestrales
                                    for trimestre in range(1, 5):
                                        ejecucion_existente = EjecucionTrimestral.query.filter_by(
                                            indicador_id=indicador.id,
                                            anio=2024,
                                            trimestre=trimestre
                                        ).first()

                                        ejecucion_data = {
                                            'ejecucion_trimestral': float(fila_data.get(f'ejecucion_{trimestre}_trimestre', 0.0)),
                                            'cumplimiento_trimestral': float(fila_data.get(f'cumplimiento_{trimestre}_trimestre', 0.0)),
                                            'poblacion_impactada_trimestral': int(fila_data.get(f'poblacion_impactada_{trimestre}_trimestre', 0)),
                                            'observacion_trimestral': str(fila_data.get(f'observacion_{trimestre}_trimestre', ''))
                                        }

                                        if ejecucion_existente:
                                            for key, value in ejecucion_data.items():
                                                setattr(ejecucion_existente, key, value)
                                        else:
                                            nueva_ejecucion = EjecucionTrimestral(
                                                indicador_id=indicador.id,
                                                proyecto_id=proyecto.id,
                                                usuario_id=current_user.id,
                                                anio=2024,
                                                trimestre=trimestre,
                                                **ejecucion_data
                                            )
                                            db.session.add(nueva_ejecucion)

            except Exception as e:
                print(f"Error procesando fila: {e}")
                continue

        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

# ==================== EDICIÓN AVANZADA DE CELDAS ====================

@planes_bp.route('/<int:plan_id>/editar-celda-excel', methods=['POST'])
@login_required
def editar_celda_excel(plan_id):
    """Guarda el nuevo valor de una celda, con justificación y acta de auditoría."""
    plan = get_plan_or_404(plan_id, current_user)

    column_name = request.form.get('column_name')
    new_value = request.form.get('new_value')
    justification = request.form.get('justification')
    indicator_id = request.form.get('indicator_id')

    if not column_name or not new_value or not justification:
        return jsonify({
            'success': False,
            'error': 'Faltan datos requeridos: columna, valor y justificación son obligatorios',
        }), 400

    indicador = _indicador_del_plan(indicator_id, plan.id)
    if indicator_id and indicador is None:
        return jsonify({
            'success': False,
            'error': 'El indicador no existe o no pertenece a este plan de desarrollo',
        }), 404

    if indicador is not None and not puede_editar(current_user, column_name):
        return jsonify({
            'success': False,
            'error': f"Su rol no tiene permiso para editar la columna '{column_name}'",
        }), 403

    try:
        old_value = valor_actual(indicador, column_name)

        justificacion = EditJustification(
            plan_id=plan.id,
            indicador_id=indicador.id if indicador else None,
            column_name=column_name,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value),
            justification=justification,
            support_file_path=_guardar_archivo_de_soporte(request.files.get('support_file')),
            user_id=current_user.id,
        )
        db.session.add(justificacion)
        db.session.flush()  # necesitamos el id para el acta de auditoría

        aplicar_valor(indicador, column_name, new_value, current_user.id)
        if indicador is not None:
            indicador.updated_at = ahora_utc()

        _registrar_acta_de_auditoria(justificacion)

        db.session.commit()
    except ValorInvalido as exc:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(exc)}), 400
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception('Error guardando la celda %s del plan %s',
                                     column_name, plan_id)
        return jsonify({
            'success': False,
            'error': 'No se pudo guardar el cambio. Intente de nuevo.',
        }), 500

    return jsonify({
        'success': True,
        'message': 'Celda editada exitosamente',
        'edit_id': justificacion.id,
    })


def _indicador_del_plan(indicator_id, plan_id):
    """Busca el indicador exigiendo que cuelgue de este plan."""
    if not indicator_id:
        return None

    try:
        identificador = int(indicator_id)
    except (TypeError, ValueError):
        return None

    return (IndicadorProducto.query
            .join(Proyecto, IndicadorProducto.proyecto_id == Proyecto.id)
            .join(Programa, Proyecto.programa_id == Programa.id)
            .join(Componente, Programa.componente_id == Componente.id)
            .join(LineaEstrategica, Componente.linea_estrategica_id == LineaEstrategica.id)
            .filter(IndicadorProducto.id == identificador,
                    LineaEstrategica.plan_id == plan_id)
            .first())


def _guardar_archivo_de_soporte(archivo):
    """Guarda el anexo que respalda la edición y devuelve su ruta, o None."""
    if not archivo or not archivo.filename:
        return None

    nombre = secure_filename(archivo.filename)
    marca = datetime.now().strftime('%Y%m%d_%H%M%S')
    destino = os.path.join(
        current_app.config['UPLOAD_FOLDER'], 'justifications',
        f'{marca}_{current_user.id}_{nombre}',
    )
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    archivo.save(destino)
    return destino


def _registrar_acta_de_auditoria(justificacion):
    """Genera el acta PDF del cambio. Un fallo aquí no debe perder la edición."""
    try:
        from audit_file_system import create_audit_file

        ruta = create_audit_file(justificacion)
        if ruta:
            current_app.logger.info('Acta de auditoría creada: %s', ruta)
        else:
            current_app.logger.warning('No se pudo crear el acta de auditoría del cambio %s',
                                       justificacion.id)
    except Exception:
        current_app.logger.exception('Error creando el acta de auditoría del cambio %s',
                                     justificacion.id)

# ==================== FIN EDICIÓN AVANZADA ====================

# ==================== DOCUMENTOS ====================

@planes_bp.route('/<int:plan_id>/documentos')
@login_required
def documentos(plan_id):
    """Ver documentos de un plan"""
    plan = get_plan_or_404(plan_id, current_user)
    # Solo mostrar documentos activos (no eliminados)
    documentos = Documento.query.filter_by(plan_id=plan_id, estado='activo').order_by(Documento.fecha_subida.desc()).all()

    return render_template('planes/documentos.html', title='Documentos', plan=plan, documentos=documentos)

@planes_bp.route('/<int:plan_id>/documentos/subir', methods=['GET', 'POST'])
@login_required
def subir_documento(plan_id):
    """Subir documento a un plan"""
    plan = get_plan_or_404(plan_id, current_user)

    form = DocumentoForm()

    # Debug: Log del método de request
    current_app.logger.info(f"Método de request: {request.method}")
    current_app.logger.info(f"Formulario validado: {form.validate_on_submit()}")
    current_app.logger.info(f"Datos del formulario: {request.form}")

    if request.method == 'POST':
        current_app.logger.info(f"Campos del formulario: {list(form._fields.keys())}")
        for field_name, field in form._fields.items():
            current_app.logger.info('Campo %s: %s (errores: %s)',
                                    field_name, field.data, field.errors)

    if form.validate_on_submit():
        current_app.logger.info("Formulario validado correctamente")
        file = form.archivo.data
        current_app.logger.info(f"Archivo recibido: {file}")
        if file:
            current_app.logger.info(f"Nombre del archivo: {file.filename}")
            current_app.logger.info(f"Tamaño del archivo: {getattr(file, 'content_length', 'N/A')}")
            filename = secure_filename(file.filename)

            # Crear directorio si no existe
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'planes', str(plan_id))
            os.makedirs(upload_dir, exist_ok=True)

            # Guardar archivo
            file_path = os.path.join(upload_dir, filename)
            current_app.logger.info(f"Guardando archivo en: {file_path}")
            file.save(file_path)
            current_app.logger.info("Archivo guardado exitosamente")

            # Verificar que el archivo existe
            if os.path.exists(file_path):
                current_app.logger.info(f"Archivo verificado en disco: {os.path.getsize(file_path)} bytes")
            else:
                current_app.logger.error(f"Archivo NO encontrado en disco: {file_path}")

            # Crear registro en base de datos
            current_app.logger.info("Creando registro en base de datos...")
            documento = Documento(
                titulo=form.titulo.data,
                descripcion=form.descripcion.data,
                nombre_original=file.filename,
                nombre_archivo=filename,
                ruta_archivo=file_path,
                tamano=os.path.getsize(file_path),
                tipo_mime=file.mimetype,
                extension=os.path.splitext(filename)[1][1:],
                tipo_documento=form.tipo_documento.data,
                categoria=None,  # Campo eliminado del formulario
                confidencialidad=form.confidencialidad.data,
                plan_id=plan.id,
                linea_estrategica_id=request.form.get('linea_estrategica_id'),
                componente_id=request.form.get('componente_id'),
                programa_id=request.form.get('programa_id'),
                proyecto_id=request.form.get('proyecto_id'),
                indicador_id=request.form.get('indicador_id'),
                usuario_id=current_user.id
            )

            current_app.logger.info(f"Datos del documento: título={documento.titulo}, tipo={documento.tipo_documento}")

            db.session.add(documento)
            current_app.logger.info("Documento agregado a la sesión")
            db.session.commit()
            current_app.logger.info(f"Documento guardado exitosamente con ID: {documento.id}")

            flash('Documento subido exitosamente.', 'success')
            return redirect(url_for('planes.documentos', plan_id=plan_id))
        else:
            current_app.logger.warning("No se recibió ningún archivo")
    else:
        current_app.logger.warning("Formulario NO validado")
        current_app.logger.warning(f"Errores del formulario: {form.errors}")

    # Debug: Mostrar errores del formulario en el template
    if request.method == 'POST':
        current_app.logger.info(f"Mostrando errores del formulario al usuario: {form.errors}")

    return render_template('planes/subir_documento.html', title='Subir Documento', form=form, plan=plan)

@planes_bp.route('/<int:plan_id>/documentos/<int:documento_id>/descargar')
@login_required
def descargar_documento(plan_id, documento_id):
    """Descargar un documento específico"""
    # Comprueba que el plan existe y pertenece al municipio del usuario.
    get_plan_or_404(plan_id, current_user)
    documento = Documento.query.filter_by(id=documento_id, plan_id=plan_id).first_or_404()

    # Verificar permisos de descarga
    if not documento.puede_descargar(current_user):
        flash('No tienes permisos para descargar este documento.', 'error')
        return redirect(url_for('planes.documentos', plan_id=plan_id))

    # Verificar que el archivo existe
    if not os.path.exists(documento.ruta_archivo):
        flash('El archivo no se encuentra disponible.', 'error')
        return redirect(url_for('planes.documentos', plan_id=plan_id))

    try:
        # Log de la descarga
        current_app.logger.info(f"Descargando documento: {documento.nombre_original} por usuario: {current_user.username}")

        # Enviar el archivo
        return send_file(
            documento.ruta_archivo,
            as_attachment=True,
            download_name=documento.nombre_original,
            mimetype=documento.tipo_mime
        )
    except Exception as e:
        current_app.logger.error(f"Error al descargar documento {documento_id}: {e}")
        flash('Error al descargar el documento.', 'error')
        return redirect(url_for('planes.documentos', plan_id=plan_id))

@planes_bp.route('/<int:plan_id>/documentos/<int:documento_id>/eliminar', methods=['POST'])
@login_required
def eliminar_documento(plan_id, documento_id):
    """Eliminar un documento"""
    # Comprueba que el plan existe y pertenece al municipio del usuario.
    get_plan_or_404(plan_id, current_user)
    documento = Documento.query.filter_by(id=documento_id, plan_id=plan_id).first_or_404()

    # Verificar permisos (solo el propietario o admin pueden eliminar)
    if current_user.id != documento.usuario_id and not current_user.has_role('admin'):
        flash('No tienes permisos para eliminar este documento.', 'error')
        return redirect(url_for('planes.documentos', plan_id=plan_id))

    try:
        # Eliminar el archivo físico si existe
        if os.path.exists(documento.ruta_archivo):
            os.remove(documento.ruta_archivo)
            current_app.logger.info(f"Archivo físico eliminado: {documento.ruta_archivo}")

        # Marcar como eliminado en la base de datos (no eliminar físicamente)
        documento.estado = 'eliminado'
        db.session.commit()

        current_app.logger.info(f"Documento marcado como eliminado: {documento.nombre_original}")
        flash('Documento eliminado exitosamente.', 'success')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al eliminar documento {documento_id}: {e}")
        flash('Error al eliminar el documento.', 'error')

    return redirect(url_for('planes.documentos', plan_id=plan_id))

# ==================== DEBUG: PRUEBA DE PERMISOS ====================

@planes_bp.route('/<int:plan_id>/documentos/probar_permisos', methods=['GET'])
@login_required
def probar_permisos(plan_id):
    """Prueba el sistema de permisos de confidencialidad"""
    plan = get_plan_or_404(plan_id, current_user)

    from app.models import Documento, User

    # Crear documentos de prueba con diferentes niveles de confidencialidad
    documentos_prueba = [
        {'titulo': 'Documento Público', 'confidencialidad': 'publico'},
        {'titulo': 'Documento Confidencial', 'confidencialidad': 'confidencial'}
    ]

    # Obtener algunos usuarios para probar permisos
    usuarios_prueba = User.query.limit(3).all()

    resultados = []
    for doc_data in documentos_prueba:
        # Buscar o crear documento de prueba
        doc = Documento.query.filter_by(
            titulo=doc_data['titulo'],
            plan_id=plan.id
        ).first()

        if not doc:
            # Crear documento si no existe
            doc = Documento(
                titulo=doc_data['titulo'],
                descripcion=f'Documento de prueba - {doc_data["confidencialidad"]}',
                nombre_original='test.txt',
                nombre_archivo='test.txt',
                ruta_archivo='/tmp/test.txt',
                tamano=100,
                tipo_mime='text/plain',
                extension='txt',
                tipo_documento='informe',
                confidencialidad=doc_data['confidencialidad'],
                plan_id=plan.id,
                usuario_id=current_user.id
            )
            db.session.add(doc)
            db.session.commit()

        # Probar permisos para diferentes usuarios
        permisos = []
        for usuario in usuarios_prueba:
            puede_acceder = doc.puede_descargar(usuario)
            permisos.append({
                'usuario': f'{usuario.username} ({usuario.municipality})',
                'puede_acceder': puede_acceder,
                'roles': [ur.role.name for ur in usuario.active_roles] if usuario.active_roles else [usuario.legacy_role]
            })

        resultados.append({
            'documento': doc_data['titulo'],
            'confidencialidad': doc_data['confidencialidad'],
            'permisos': permisos
        })

    return render_template('planes/probar_permisos.html',
                          title='Prueba de Permisos',
                          plan=plan,
                          resultados=resultados)

# ==================== DEBUG: PRUEBA DE FORMULARIO ====================

@planes_bp.route('/<int:plan_id>/documentos/verificar_formulario', methods=['GET'])
@login_required
def verificar_formulario(plan_id):
    """Verificar que el formulario funciona correctamente"""
    plan = get_plan_or_404(plan_id, current_user)
    form = DocumentoForm()

    # Verificar campos del formulario
    campos_info = []
    for field_name in form._fields:
        field = form._fields[field_name]
        info = {
            'nombre': field_name,
            'tipo': field.__class__.__name__,
            'requerido': any('DataRequired' in str(v) for v in getattr(field, 'validators', [])),
            'opciones': getattr(field, 'choices', None)
        }
        campos_info.append(info)

    return render_template('planes/verificar_formulario.html',
                          title='Verificación de Formulario',
                          plan=plan,
                          campos=campos_info,
                          form=form)

# ==================== DEBUG: PRUEBA DE SUBIDA ====================

@planes_bp.route('/<int:plan_id>/documentos/test', methods=['GET'])
@login_required
def test_documento(plan_id):
    """Función de prueba para verificar la subida de documentos"""
    plan = get_plan_or_404(plan_id, current_user)

    # Crear un documento de prueba sin archivo
    import datetime

    from app.models import Documento

    documento_test = Documento(
        titulo="Documento de Prueba - " + str(datetime.datetime.now().strftime("%Y%m%d_%H%M%S")),
        descripcion="Documento creado para pruebas del sistema",
        nombre_original="test_document.txt",
        nombre_archivo="test_document.txt",
        ruta_archivo="/tmp/test_document.txt",
        tamano=100,
        tipo_mime="text/plain",
        extension="txt",
        tipo_documento="informe",
        confidencialidad="publico",
        plan_id=plan.id,
        usuario_id=current_user.id
    )

    try:
        db.session.add(documento_test)
        db.session.commit()
        current_app.logger.info(f"Documento de prueba creado exitosamente: {documento_test.id}")
        flash(f'Documento de prueba creado exitosamente (ID: {documento_test.id}).', 'success')
    except Exception as e:
        current_app.logger.error(f"Error creando documento de prueba: {e}")
        db.session.rollback()
        flash(f'Error creando documento de prueba: {e}', 'error')

    return redirect(url_for('planes.documentos', plan_id=plan_id))

@planes_bp.route('/<int:plan_id>/debug')
@login_required
def debug_plan(plan_id):
    """Endpoint de diagnóstico para verificar el estado del plan y sus relaciones"""
    plan = get_plan_or_redirect(plan_id, current_user)
    if hasattr(plan, 'status_code'):
        return plan


    debug_info = {
        'plan': {
            'id': plan.id,
            'titulo': plan.titulo,
            'estado': plan.estado,
            'lineas_count': len(plan.lineas_estrategicas)
        },
        'relaciones': {},
        'datos': {}
    }

    try:
        # Verificar líneas estratégicas
        lineas = []
        for linea in plan.lineas_estrategicas:
            linea_info = {
                'id': linea.id,
                'nombre': linea.nombre,
                'estado': linea.estado,
                'componentes_count': len(getattr(linea, 'componentes', []))
            }

            componentes = []
            for componente in getattr(linea, 'componentes', []):
                componente_info = {
                    'id': componente.id,
                    'nombre': componente.nombre,
                    'estado': componente.estado,
                    'programas_count': len(getattr(componente, 'programas', []))
                }

                programas = []
                for programa in getattr(componente, 'programas', []):
                    programa_info = {
                        'id': programa.id,
                        'nombre': programa.nombre,
                        'estado': programa.estado,
                        'proyectos_count': len(getattr(programa, 'proyectos', []))
                    }

                    proyectos = []
                    for proyecto in getattr(programa, 'proyectos', []):
                        proyecto_info = {
                            'id': proyecto.id,
                            'nombre': proyecto.nombre,
                            'estado': proyecto.estado,
                            'indicadores_count': len(getattr(proyecto, 'indicadores', []))
                        }

                        indicadores = []
                        for indicador in getattr(proyecto, 'indicadores', []):
                            indicador_info = {
                                'id': indicador.id,
                                'nombre': indicador.nombre,
                                'estado': indicador.estado,
                                'ejecuciones_count': len(getattr(indicador, 'ejecuciones_trimestrales', []))
                            }
                            indicadores.append(indicador_info)

                        proyecto_info['indicadores'] = indicadores
                        proyectos.append(proyecto_info)

                    programa_info['proyectos'] = proyectos
                    programas.append(programa_info)

                componente_info['programas'] = programas
                componentes.append(componente_info)

            linea_info['componentes'] = componentes
            lineas.append(linea_info)

        debug_info['relaciones'] = lineas

        # La generación de reportes se retiró del sistema, así que aquí solo
        # se reportan los totales que sí se pueden calcular.
        debug_info['datos'] = {
            'total_lineas': len(lineas),
            'total_componentes': sum(len(linea['componentes']) for linea in lineas),
        }

    except Exception as e:
        debug_info['error'] = str(e)
        debug_info['error_type'] = type(e).__name__

    return debug_info


