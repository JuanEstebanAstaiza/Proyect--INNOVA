from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import io
from datetime import datetime

from app import db
from app.models import (
    PlanDesarrollo, LineaEstrategica, Componente, Programa,
    Proyecto, Actividad, IndicadorProducto, EjecucionTrimestral, Documento
)
from app.forms.planes import (
    PlanForm, LineaEstrategicaForm, ComponenteForm,
    ProgramaForm, ProyectoForm, ActividadForm, IndicadorForm, DocumentoForm,
    EditarLineaEstrategicaForm, EditarComponenteForm, EditarProgramaForm,
    EditarProyectoForm, EditarActividadForm
)

planes_bp = Blueprint('planes', __name__, url_prefix='/planes')

def get_plan_or_redirect(plan_id, current_user, redirect_endpoint='planes.index'):
    """Helper function to get a plan or redirect to an available one"""
    plan = PlanDesarrollo.query.filter_by(id=plan_id, municipio=current_user).first()

    if not plan:
        # Buscar el plan activo del usuario
        plan_activo = PlanDesarrollo.query.filter_by(
            municipio=current_user,
            estado='activo'
        ).first()

        if plan_activo:
            flash(f'El plan solicitado no fue encontrado. Redirigiendo al plan activo.', 'info')
            return redirect(url_for('planes.ver', plan_id=plan_activo.id))
        else:
            # Si no hay plan activo, buscar el más reciente
            plan_reciente = PlanDesarrollo.query.filter_by(municipio=current_user).order_by(
                PlanDesarrollo.created_at.desc()
            ).first()

            if plan_reciente:
                flash(f'El plan solicitado no fue encontrado. Redirigiendo al plan más reciente.', 'info')
                return redirect(url_for('planes.ver', plan_id=plan_reciente.id))
            else:
                # Si no hay ningún plan, mostrar error
                flash('No se encontraron planes disponibles. Por favor cree un plan primero.', 'warning')
                return redirect(url_for(redirect_endpoint))

    return plan

# Lista de planes
@planes_bp.route('/')
@login_required
def index():
    """Lista todos los planes del usuario actual"""
    # Para usuarios normales, mostrar solo el plan activo o el más reciente
    if not current_user.is_admin():
        plan_activo = PlanDesarrollo.get_plan_activo_o_primero(current_user)
        planes = [plan_activo] if plan_activo else []
        mostrar_todos = False
    else:
        # Para administradores, mostrar todos los planes
        planes = PlanDesarrollo.query.filter_by(municipio=current_user).order_by(
            PlanDesarrollo.estado.desc(),  # Activos primero
            PlanDesarrollo.created_at.desc()  # Luego por fecha de creación
        ).all()
        mostrar_todos = True

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
        plan.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Plan actualizado exitosamente.', 'success')
        return redirect(url_for('planes.ver', plan_id=plan.id))

    return render_template('planes/editar.html', title='Editar Plan', form=form, plan=plan)

# Eliminar plan
@planes_bp.route('/<int:plan_id>/eliminar', methods=['POST'])
@login_required
def eliminar(plan_id):
    """Eliminar un plan"""
    plan = PlanDesarrollo.query.filter_by(id=plan_id, municipio=current_user).first_or_404()

    # No permitir eliminar planes activos
    if plan.estado == 'activo':
        flash('No se puede eliminar un plan activo. Primero desactívelo.', 'danger')
        return redirect(url_for('planes.index'))

    try:
        # Eliminar dependencias en orden correcto para evitar errores de integridad

        # 1. Eliminar permisos de fila asociados a indicadores de este plan
        from app.models import RowPermission, IndicadorProducto, Proyecto, Programa, Componente, LineaEstrategica

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
        from app.models import ColumnPermission
        # Nota: ColumnPermission no tiene relación directa con planes, así que no necesitamos eliminarlos

        # 3. Eliminar sesiones activas relacionadas (si existen)
        from app.models import ActiveSession
        # Las sesiones activas no están directamente relacionadas con planes

        # 4. Eliminar logs de actividad relacionados (opcional)
        from app.models import ActivityLog
        # Los logs pueden ser útiles para auditoría, así que los mantenemos

        # 5. Ahora sí podemos eliminar el plan de forma segura
        db.session.delete(plan)
        db.session.commit()

        flash('Plan eliminado exitosamente.', 'success')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error eliminando plan {plan_id}: {str(e)}')
        flash('Error al eliminar el plan. Inténtalo de nuevo.', 'danger')

    return redirect(url_for('planes.index'))

# Activar plan
@planes_bp.route('/<int:plan_id>/activar', methods=['POST'])
@login_required
def activar_plan(plan_id):
    """Activar un plan (desactiva automáticamente los demás)"""
    plan = PlanDesarrollo.query.filter_by(id=plan_id, municipio=current_user).first_or_404()

    plan.activar()

    flash(f'Plan "{plan.titulo}" activado exitosamente. Los demás planes han sido desactivados.', 'success')
    return redirect(url_for('planes.index'))

# Desactivar plan
@planes_bp.route('/<int:plan_id>/desactivar', methods=['POST'])
@login_required
def desactivar_plan(plan_id):
    """Desactivar un plan"""
    plan = PlanDesarrollo.query.filter_by(id=plan_id, municipio=current_user).first_or_404()

    plan.desactivar()

    flash(f'Plan "{plan.titulo}" desactivado exitosamente.', 'success')
    return redirect(url_for('planes.index'))

# ==================== LÍNEAS ESTRATÉGICAS ====================

@planes_bp.route('/<int:plan_id>/lineas')
@login_required
def lineas(plan_id):
    """Ver líneas estratégicas de un plan"""
    plan = PlanDesarrollo.query.filter_by(id=plan_id, municipio=current_user).first_or_404()
    return render_template('planes/lineas.html', title='Líneas Estratégicas', plan=plan)

@planes_bp.route('/<int:plan_id>/lineas/crear', methods=['GET', 'POST'])
@login_required
def crear_linea(plan_id):
    """Crear nueva línea estratégica"""
    plan = PlanDesarrollo.query.filter_by(id=plan_id, municipio=current_user).first_or_404()

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
        PlanDesarrollo.municipio_id == current_user.id
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
            flash(f'Error al actualizar la línea estratégica: {str(e)}', 'danger')

    return render_template('planes/editar_linea.html', title='Editar Línea Estratégica',
                          form=form, linea=linea, plan=linea.plan)

@planes_bp.route('/lineas/<int:linea_id>/detalles')
@login_required
def detalles_linea(linea_id):
    """Ver detalles completos de una línea estratégica"""
    linea = LineaEstrategica.query.join(PlanDesarrollo).filter(
        LineaEstrategica.id == linea_id,
        PlanDesarrollo.municipio_id == current_user.id
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
        PlanDesarrollo.municipio_id == current_user.id
    ).first_or_404()

    return render_template('planes/componentes.html', title='Componentes', linea=linea)

@planes_bp.route('/lineas/<int:linea_id>/componentes/crear', methods=['GET', 'POST'])
@login_required
def crear_componente(linea_id):
    """Crear nuevo componente"""
    linea = LineaEstrategica.query.join(PlanDesarrollo).filter(
        LineaEstrategica.id == linea_id,
        PlanDesarrollo.municipio_id == current_user.id
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
        PlanDesarrollo.municipio_id == current_user.id
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
            flash(f'Error al actualizar el componente: {str(e)}', 'danger')

    return render_template('planes/editar_componente.html', title='Editar Componente',
                          form=form, componente=componente, linea=componente.linea_estrategica)

@planes_bp.route('/componentes/<int:componente_id>/detalles')
@login_required
def detalles_componente(componente_id):
    """Ver detalles completos de un componente"""
    componente = Componente.query.join(LineaEstrategica).join(PlanDesarrollo).filter(
        Componente.id == componente_id,
        PlanDesarrollo.municipio_id == current_user.id
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
            flash(f'Error al crear el programa: {str(e)}', 'danger')

    return render_template('planes/crear_programa.html', title='Crear Programa', form=form, componente=componente)

@planes_bp.route('/programas/<int:programa_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_programa(programa_id):
    """Editar programa existente"""
    programa = Programa.query.join(Componente).join(LineaEstrategica).join(PlanDesarrollo).filter(
        Programa.id == programa_id,
        PlanDesarrollo.municipio_id == current_user.id
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
            flash(f'Error al actualizar el programa: {str(e)}', 'danger')

    return render_template('planes/editar_programa.html', title='Editar Programa',
                          form=form, programa=programa, componente=programa.componente)

@planes_bp.route('/programas/<int:programa_id>/detalles')
@login_required
def detalles_programa(programa_id):
    """Ver detalles completos de un programa"""
    programa = Programa.query.join(Componente).join(LineaEstrategica).join(PlanDesarrollo).filter(
        Programa.id == programa_id,
        PlanDesarrollo.municipio_id == current_user.id
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
            flash(f'Error al crear el proyecto: {str(e)}', 'danger')

    return render_template('planes/crear_proyecto.html', title='Crear Proyecto', form=form, programa=programa)

@planes_bp.route('/proyectos/<int:proyecto_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_proyecto(proyecto_id):
    """Editar proyecto existente"""
    proyecto = Proyecto.query.join(Programa).join(Componente).join(LineaEstrategica).join(PlanDesarrollo).filter(
        Proyecto.id == proyecto_id,
        PlanDesarrollo.municipio_id == current_user.id
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
            flash(f'Error al actualizar el proyecto: {str(e)}', 'danger')

    return render_template('planes/editar_proyecto.html', title='Editar Proyecto',
                          form=form, proyecto=proyecto, programa=proyecto.programa)

@planes_bp.route('/proyectos/<int:proyecto_id>/detalles')
@login_required
def detalles_proyecto(proyecto_id):
    """Ver detalles completos de un proyecto"""
    proyecto = Proyecto.query.join(Programa).join(Componente).join(LineaEstrategica).join(PlanDesarrollo).filter(
        Proyecto.id == proyecto_id,
        PlanDesarrollo.municipio_id == current_user.id
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
            flash(f'Error al crear la actividad: {str(e)}', 'danger')

    return render_template('planes/crear_actividad.html', title='Crear Actividad', form=form, proyecto=proyecto)

@planes_bp.route('/actividades/<int:actividad_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_actividad(actividad_id):
    """Editar actividad existente"""
    actividad = Actividad.query.join(Proyecto).join(Programa).join(Componente).join(LineaEstrategica).join(PlanDesarrollo).filter(
        Actividad.id == actividad_id,
        PlanDesarrollo.municipio_id == current_user.id
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
            flash(f'Error al actualizar la actividad: {str(e)}', 'danger')

    return render_template('planes/editar_actividad.html', title='Editar Actividad',
                          form=form, actividad=actividad, proyecto=actividad.proyecto)

@planes_bp.route('/actividades/<int:actividad_id>/detalles')
@login_required
def detalles_actividad(actividad_id):
    """Ver detalles completos de una actividad"""
    actividad = Actividad.query.join(Proyecto).join(Programa).join(Componente).join(LineaEstrategica).join(PlanDesarrollo).filter(
        Actividad.id == actividad_id,
        PlanDesarrollo.municipio_id == current_user.id
    ).first_or_404()

    return render_template('planes/detalles_actividad.html', title='Detalles de la Actividad',
                          actividad=actividad, proyecto=actividad.proyecto)

# ==================== VISTA EXCEL ====================

@planes_bp.route('/<int:plan_id>/excel')
@login_required
def ver_excel(plan_id):
    """Ver plan en formato tabla Excel editable con permisos aplicados"""
    plan = get_plan_or_redirect(plan_id, current_user)
    if hasattr(plan, 'status_code'):
        return plan

    # Obtener permisos del usuario
    user_editable_columns = current_user.get_editable_columns()
    user_viewable_columns = current_user.get_viewable_columns()

    # Preparar datos para la tabla Excel según el diccionario de datos
    excel_data = []

    for linea in plan.lineas_estrategicas:
        for componente in linea.componentes:
            for programa in componente.programas:
                for proyecto in programa.proyectos:
                    # Buscar indicador para este proyecto
                    indicador = proyecto.indicadores[0] if proyecto.indicadores else None

                    # Verificar si el usuario puede editar esta fila específica
                    can_edit_row = current_user.can_edit_row(indicador.id if indicador else 0) if indicador else False

                    # Obtener ejecuciones trimestrales del 2024
                    ejecuciones_2024 = []
                    if indicador:
                        ejecuciones_2024 = indicador.get_ejecuciones_por_anio(2024)

                    # Crear diccionario con todos los campos del diccionario de datos
                    row = {
                        # Información básica de la estructura
                        'cod_linea': linea.cod_linea,
                        'lineas_estrategicas': linea.nombre,
                        'cod_componente': componente.cod_componente,
                        'componentes': componente.nombre,
                        'cod_programa': programa.cod_programa,
                        'programa_pdm': programa.nombre,
                        'dependencia_responsable': programa.dependencia_responsable or '',
                        'bpim': programa.bpim or '',
                        'nombre_proyecto': proyecto.nombre,
                        'indicadores': indicador.nombre if indicador else '',
                        'cod_indicador_de_producto': indicador.cod_indicador if indicador else '',
                        'indicador_de_producto': indicador.nombre if indicador else '',
                        'tipo_de_indicador': indicador.tipo_indicador if indicador else '',
                        'linea_base': indicador.linea_base if indicador else 0.0,
                        'sentido': indicador.sentido if indicador else '',
                        'tipologia': indicador.tipologia if indicador else '',
                        'unidad': indicador.unidad if indicador else '',
                        'meta_cuatrienio': indicador.meta_cuatrienio if indicador else 0.0,
                        'meta_2024': indicador.meta_2024 if indicador else 0.0,
                    }

                    # Agregar columnas de ejecución trimestral
                    for trimestre in range(1, 5):
                        ejecucion = next((e for e in ejecuciones_2024 if e.trimestre == trimestre), None)

                        row[f'ejecucion_{trimestre}_trimestre'] = ejecucion.ejecucion_trimestral if ejecucion else 0.0
                        row[f'cumplimiento_{trimestre}_trimestre'] = ejecucion.cumplimiento_trimestral if ejecucion else 0.0
                        row[f'poblacion_impactada_{trimestre}_trimestre'] = ejecucion.poblacion_impactada_trimestral if ejecucion else 0
                        row[f'observacion_{trimestre}_trimestre'] = ejecucion.observacion_trimestral if ejecucion else ''

                    # Agregar columnas acumuladas
                    ejecucion_acumulada = sum(row[f'ejecucion_{i}_trimestre'] for i in range(1, 5))
                    cumplimiento_acumulado = (ejecucion_acumulada / row['meta_2024'] * 100) if row['meta_2024'] > 0 else 0.0
                    poblacion_acumulada = sum(row[f'poblacion_impactada_{i}_trimestre'] for i in range(1, 5))

                    row['ejecucion_acumulada'] = ejecucion_acumulada
                    row['cumplimiento_acumulado'] = cumplimiento_acumulado
                    row['poblacion_impactada_acumulada'] = poblacion_acumulada
                    row['observacion_acumulada'] = 'Consolidado anual'

                    # Agregar información de permisos a la fila
                    row['_can_edit_row'] = can_edit_row
                    row['_indicador_id'] = indicador.id if indicador else None

                    excel_data.append(row)

    # Si no hay datos, crear una fila de ejemplo
    if not excel_data:
        row_ejemplo = {
            'cod_linea': 1,
            'lineas_estrategicas': 'Desarrollo Económico Sostenible',
            'cod_componente': 1.1,
            'componentes': 'Fortalecimiento del Sector Productivo',
            'cod_programa': 'PDM-001',
            'programa_pdm': 'Programa de Apoyo a Emprendimientos',
            'dependencia_responsable': 'Dirección de Desarrollo Económico',
            'bpim': 'BPIM-2024-001',
            'nombre_proyecto': 'Centro de Emprendimiento Municipal',
            'indicadores': 'Número de emprendedores capacitados',
            'cod_indicador_de_producto': 'IP-001',
            'indicador_de_producto': 'Número de emprendedores capacitados',
            'tipo_de_indicador': 'Resultado',
            'linea_base': 50.0,
            'sentido': 'positivo',
            'tipologia': 'Cuantitativo',
            'unidad': 'personas',
            'meta_cuatrienio': 500.0,
            'meta_2024': 150.0,
        }

        # Agregar columnas trimestrales vacías
        for trimestre in range(1, 5):
            row_ejemplo[f'ejecucion_{trimestre}_trimestre'] = 0.0
            row_ejemplo[f'cumplimiento_{trimestre}_trimestre'] = 0.0
            row_ejemplo[f'poblacion_impactada_{trimestre}_trimestre'] = 0
            row_ejemplo[f'observacion_{trimestre}_trimestre'] = ''

        row_ejemplo['ejecucion_acumulada'] = 0.0
        row_ejemplo['cumplimiento_acumulado'] = 0.0
        row_ejemplo['poblacion_impactada_acumulada'] = 0
        row_ejemplo['observacion_acumulada'] = ''

        excel_data.append(row_ejemplo)

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
    """Exportar plan a archivo Excel"""
    try:
        import pandas as pd
    except ImportError:
        flash('La funcionalidad de Excel requiere instalar pandas. Contacte al administrador.', 'error')
        return redirect(url_for('planes.ver', plan_id=plan_id))

    plan = PlanDesarrollo.query.filter_by(id=plan_id, municipio=current_user).first_or_404()

    # Preparar datos como en la vista Excel
    excel_data = []

    for linea in plan.lineas_estrategicas:
        for componente in linea.componentes:
            for programa in componente.programas:
                for proyecto in programa.proyectos:
                    indicador = proyecto.indicadores[0] if proyecto.indicadores else None
                    ejecuciones_2024 = []
                    if indicador:
                        ejecuciones_2024 = indicador.get_ejecuciones_por_anio(2024)

                    row = {
                        'CÓD LINEA': linea.cod_linea,
                        'LINEAS ESTRATEGICAS': linea.nombre,
                        'CÓD COMPONENTE': componente.cod_componente,
                        'COMPONENTES': componente.nombre,
                        'CÓD PROGRAMA': programa.cod_programa,
                        'PROGRAMA PDM': programa.nombre,
                        'DEPENDENCIA RESPOSABLE': programa.dependencia_responsable or '',
                        'BPIM': programa.bpim or '',
                        'NOMBRE PROYECTO': proyecto.nombre,
                        'INDICADORES': indicador.nombre if indicador else '',
                        'CÓD INDICADOR DE PRODUCTO': indicador.cod_indicador if indicador else '',
                        'INDICADOR DE PRODUCTO': indicador.nombre if indicador else '',
                        'TIPO DE INDICADOR': indicador.tipo_indicador if indicador else '',
                        'LINEA BASE': indicador.linea_base if indicador else 0.0,
                        'SENTIDO': indicador.sentido if indicador else '',
                        'TIPOLOGÍA': indicador.tipologia if indicador else '',
                        'UNIDAD': indicador.unidad if indicador else '',
                        'META CUATRIENIO (2024-2027)': indicador.meta_cuatrienio if indicador else 0.0,
                        'META 2024': indicador.meta_2024 if indicador else 0.0,
                    }

                    # Agregar columnas de ejecución trimestral
                    for trimestre in range(1, 5):
                        ejecucion = next((e for e in ejecuciones_2024 if e.trimestre == trimestre), None)
                        row[f'EJECUCIÓN {trimestre} TRIMESTRE'] = ejecucion.ejecucion_trimestral if ejecucion else 0.0
                        row[f'% CUMPLIMIENTO {trimestre} TRIMESTRE'] = ejecucion.cumplimiento_trimestral if ejecucion else 0.0
                        row[f'POBLACIÓN IMPACTADA POR SECTOR {trimestre} TRIMESTRE'] = ejecucion.poblacion_impactada_trimestral if ejecucion else 0
                        row[f'OBSERVACIÓN AL CUMPLIMIENTO {trimestre}TRIMESTRE'] = ejecucion.observacion_trimestral if ejecucion else ''

                    # Agregar columnas acumuladas
                    ejecucion_acumulada = sum(row[f'EJECUCIÓN {i} TRIMESTRE'] for i in range(1, 5))
                    cumplimiento_acumulado = (ejecucion_acumulada / row['META 2024'] * 100) if row['META 2024'] > 0 else 0.0
                    poblacion_acumulada = sum(row[f'POBLACIÓN IMPACTADA POR SECTOR {i} TRIMESTRE'] for i in range(1, 5))

                    row['EJECUCIÓN ACUMULADA'] = ejecucion_acumulada
                    row['% CUMPLIMIENTO ACUMULADO'] = cumplimiento_acumulado
                    row['POBLACIÓN IMPACTADA ACUMULADA'] = poblacion_acumulada
                    row['OBSERVACIÓN ACUMULADA'] = 'Consolidado anual'

                    excel_data.append(row)

    # Crear DataFrame de pandas
    df = pd.DataFrame(excel_data)

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
        return redirect(url_for('planes.excel', plan_id=plan_id))

    plan = PlanDesarrollo.query.filter_by(id=plan_id, municipio=current_user).first_or_404()

    if 'excel_file' not in request.files:
        flash('No se encontró el archivo.', 'error')
        return redirect(url_for('planes.excel', plan_id=plan_id))

    file = request.files['excel_file']
    if file.filename == '':
        flash('No se seleccionó ningún archivo.', 'error')
        return redirect(url_for('planes.excel', plan_id=plan_id))

    if not file.filename.endswith(('.xlsx', '.xls')):
        flash('El archivo debe ser un Excel (.xlsx o .xls).', 'error')
        return redirect(url_for('planes.excel', plan_id=plan_id))

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
        flash(f'Error al procesar el archivo Excel: {str(e)}', 'error')

    return redirect(url_for('planes.excel', plan_id=plan_id))

@planes_bp.route('/<int:plan_id>/guardar-excel', methods=['POST'])
@login_required
def guardar_excel(plan_id):
    """Guardar cambios desde la vista Excel"""
    from flask import jsonify

    plan = PlanDesarrollo.query.filter_by(id=plan_id, municipio=current_user).first_or_404()

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

# ==================== DOCUMENTOS ====================

@planes_bp.route('/<int:plan_id>/documentos')
@login_required
def documentos(plan_id):
    """Ver documentos de un plan"""
    plan = PlanDesarrollo.query.filter_by(id=plan_id, municipio=current_user).first_or_404()
    documentos = Documento.query.filter_by(plan_id=plan_id).all()

    return render_template('planes/documentos.html', title='Documentos', plan=plan, documentos=documentos)

@planes_bp.route('/<int:plan_id>/documentos/subir', methods=['GET', 'POST'])
@login_required
def subir_documento(plan_id):
    """Subir documento a un plan"""
    plan = PlanDesarrollo.query.filter_by(id=plan_id, municipio=current_user).first_or_404()

    form = DocumentoForm()
    if form.validate_on_submit():
        file = form.archivo.data
        if file:
            filename = secure_filename(file.filename)

            # Crear directorio si no existe
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'planes', str(plan_id))
            os.makedirs(upload_dir, exist_ok=True)

            # Guardar archivo
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)

            # Crear registro en base de datos
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
                categoria=form.categoria.data,
                confidencialidad=form.confidencialidad.data,
                plan=plan,
                usuario=current_user
            )

            db.session.add(documento)
            db.session.commit()

            flash('Documento subido exitosamente.', 'success')
            return redirect(url_for('planes.documentos', plan_id=plan_id))

    return render_template('planes/subir_documento.html', title='Subir Documento', form=form, plan=plan)

# ==================== REPORTES ====================

@planes_bp.route('/<int:plan_id>/reportes')
@login_required
def reportes(plan_id):
    """Ver reportes de un plan"""
    plan = get_plan_or_redirect(plan_id, current_user)
    if hasattr(plan, 'status_code'):
        return plan

    # Obtener el plan activo para mostrar información actual
    from app.models import IndicadorProducto, Proyecto
    plan_activo = PlanDesarrollo.query.filter_by(
        municipio=current_user,
        estado='activo'
    ).first()

    # Calcular estadísticas para el reporte
    total_lineas = len(plan.lineas_estrategicas)
    total_componentes = sum(len(linea.componentes) for linea in plan.lineas_estrategicas)
    total_programas = sum(len(componente.programas) for componente in
                         [comp for linea in plan.lineas_estrategicas for comp in linea.componentes])
    total_proyectos = sum(len(programa.proyectos) for programa in
                         [prog for componente in
                          [comp for linea in plan.lineas_estrategicas for comp in linea.componentes]
                          for prog in componente.programas])

    # Estadísticas para métricas (usando el plan actual)
    # Para simplificar, usaremos conteos básicos por ahora
    # En una implementación completa, estas consultas serían más complejas
    try:
        # Contar indicadores asociados al plan actual (simplificado)
        indicadores_count = IndicadorProducto.query.count()

        # Contar proyectos asociados al plan actual (simplificado)
        proyectos_count = Proyecto.query.count()
    except:
        indicadores_count = 0
        proyectos_count = 0

    return render_template('planes/reportes.html',
                          title='Reportes y Análisis',
                          plan=plan,
                          plan_activo=plan_activo,
                          indicadores_count=indicadores_count,
                          proyectos_count=proyectos_count,
                          total_lineas=total_lineas,
                          total_componentes=total_componentes,
                          total_programas=total_programas,
                          total_proyectos=total_proyectos)

# API para datos de reportes
@planes_bp.route('/<int:plan_id>/reportes/datos')
@login_required
def reportes_datos(plan_id):
    """API para obtener datos JSON para los reportes"""
    plan = get_plan_or_redirect(plan_id, current_user)
    if hasattr(plan, 'status_code'):
        return plan

    from app.models import IndicadorProducto, Proyecto, Programa, Componente, LineaEstrategica, EjecucionTrimestral

    # Obtener tipo de análisis de los parámetros de consulta
    tipo_analisis = request.args.get('tipo_analisis', 'general')
    periodo = request.args.get('periodo', '2024')
    tipo_grafico = request.args.get('tipo_grafico', 'lineas')

    # Generar datos basados en el tipo de análisis
    if tipo_analisis == 'general':
        data = generar_analisis_general(plan, periodo, tipo_grafico)
    elif tipo_analisis == 'ejecucion':
        data = generar_analisis_ejecucion(plan, periodo, tipo_grafico)
    elif tipo_analisis == 'presupuesto':
        data = generar_analisis_presupuesto(plan, periodo, tipo_grafico)
    elif tipo_analisis == 'indicadores':
        data = generar_analisis_indicadores(plan, periodo, tipo_grafico)
    elif tipo_analisis == 'comparativo':
        data = generar_analisis_comparativo(plan, periodo, tipo_grafico)
    elif tipo_analisis == 'tendencias':
        data = generar_analisis_tendencias(plan, periodo, tipo_grafico)
    else:
        data = generar_analisis_general(plan, periodo, tipo_grafico)

    return data

def generar_analisis_general(plan, periodo, tipo_grafico):
    """Genera datos para análisis general"""
    # Datos para gráfico de tendencias (ejemplo con datos realistas)
    tendencias_data = {
        'labels': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
        'datasets': [{
            'label': f'Ejecución Global {periodo} (%)',
            'data': [15, 25, 35, 45, 55, 65, 70, 75, 80, 82, 85, 88],
            'borderColor': 'rgba(54, 162, 235, 1)',
            'backgroundColor': 'rgba(54, 162, 235, 0.1)',
            'tension': 0.4
        }, {
            'label': f'Planificado {periodo} (%)',
            'data': [20, 30, 40, 50, 60, 70, 75, 80, 85, 87, 90, 92],
            'borderColor': 'rgba(255, 99, 132, 1)',
            'backgroundColor': 'rgba(255, 99, 132, 0.1)',
            'tension': 0.4
        }]
    }

    # Datos para distribución presupuestaria
    presupuesto_data = {
        'labels': ['Infraestructura', 'Educación', 'Salud', 'Medio Ambiente', 'Desarrollo Social'],
        'datasets': [{
            'data': [35, 25, 20, 12, 8],
            'backgroundColor': [
                'rgba(255, 99, 132, 0.8)',
                'rgba(54, 162, 235, 0.8)',
                'rgba(255, 205, 86, 0.8)',
                'rgba(75, 192, 192, 0.8)',
                'rgba(153, 102, 255, 0.8)'
            ]
        }]
    }

    # Indicadores de ejemplo
    indicadores_data = [
        {'id': 1, 'nombre': 'Cobertura de agua potable', 'meta_2024': 85, 'ejecucion_q1': 75, 'avance': 88},
        {'id': 2, 'nombre': 'Tasa de alfabetización', 'meta_2024': 95, 'ejecucion_q1': 92, 'avance': 97},
        {'id': 3, 'nombre': 'Acceso a vivienda digna', 'meta_2024': 70, 'ejecucion_q1': 65, 'avance': 93},
        {'id': 4, 'nombre': 'Empleo juvenil', 'meta_2024': 60, 'ejecucion_q1': 55, 'avance': 92},
        {'id': 5, 'nombre': 'Reducción de pobreza', 'meta_2024': 45, 'ejecucion_q1': 40, 'avance': 89}
    ]

    return {
        'success': True,
        'plan_id': plan.id,
        'plan_titulo': plan.titulo,
        'tipo_analisis': 'general',
        'titulo': f'Análisis General - {periodo}',
        'descripcion': 'Vista general del progreso del plan de desarrollo',
        'tendencias': tendencias_data,
        'presupuesto': presupuesto_data,
        'indicadores': indicadores_data,
        'metricas': {
            'total_indicadores': len(indicadores_data),
            'total_proyectos': 12,
            'presupuesto_total': plan.presupuesto_total or 100000000,
            'presupuesto_ejecutado': 75000000,
            'avance_global': 75,
            'anio_inicio': plan.anio_inicio,
            'anio_fin': plan.anio_fin
        }
    }

def generar_analisis_ejecucion(plan, periodo, tipo_grafico):
    """Genera datos para análisis de ejecución por trimestre"""
    ejecucion_data = {
        'labels': ['Q1', 'Q2', 'Q3', 'Q4'],
        'datasets': [{
            'label': f'Ejecución Física {periodo} (%)',
            'data': [78, 82, 85, 88],
            'borderColor': 'rgba(75, 192, 192, 1)',
            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            'tension': 0.4
        }, {
            'label': f'Ejecución Financiera {periodo} (%)',
            'data': [72, 78, 83, 87],
            'borderColor': 'rgba(255, 159, 64, 1)',
            'backgroundColor': 'rgba(255, 159, 64, 0.2)',
            'tension': 0.4
        }]
    }

    return {
        'success': True,
        'plan_id': plan.id,
        'plan_titulo': plan.titulo,
        'tipo_analisis': 'ejecucion',
        'titulo': f'Análisis de Ejecución por Trimestre - {periodo}',
        'descripcion': 'Seguimiento detallado de la ejecución física y financiera',
        'tendencias': ejecucion_data,
        'presupuesto': None,
        'indicadores': [],
        'metricas': {
            'ejecucion_fisica_promedio': 83.25,
            'ejecucion_financiera_promedio': 80,
            'variacion_trimestral': 2.5,
            'proyectos_completados': 8,
            'proyectos_en_progreso': 4
        }
    }

def generar_analisis_presupuesto(plan, periodo, tipo_grafico):
    """Genera datos para análisis presupuestario"""
    presupuesto_detallado = {
        'labels': ['Infraestructura Vial', 'Infraestructura Educativa', 'Infraestructura Salud',
                  'Programas Sociales', 'Desarrollo Rural', 'Medio Ambiente', 'Administración'],
        'datasets': [{
            'label': f'Presupuesto Asignado {periodo} (Millones)',
            'data': [25, 18, 15, 12, 10, 8, 12],
            'backgroundColor': [
                'rgba(255, 99, 132, 0.8)',
                'rgba(54, 162, 235, 0.8)',
                'rgba(255, 205, 86, 0.8)',
                'rgba(75, 192, 192, 0.8)',
                'rgba(153, 102, 255, 0.8)',
                'rgba(255, 159, 64, 0.8)',
                'rgba(201, 203, 207, 0.8)'
            ]
        }]
    }

    return {
        'success': True,
        'plan_id': plan.id,
        'plan_titulo': plan.titulo,
        'tipo_analisis': 'presupuesto',
        'titulo': f'Análisis Presupuestario - {periodo}',
        'descripcion': 'Distribución y ejecución del presupuesto por componentes',
        'tendencias': None,
        'presupuesto': presupuesto_detallado,
        'indicadores': [],
        'metricas': {
            'presupuesto_total': plan.presupuesto_total or 100000000,
            'presupuesto_ejecutado': 75000000,
            'presupuesto_restante': 25000000,
            'eficiencia_ejecucion': 85,
            'componente_mayor_inversion': 'Infraestructura Vial'
        }
    }

def generar_analisis_indicadores(plan, periodo, tipo_grafico):
    """Genera datos para análisis de indicadores"""
    indicadores_completos = [
        {'id': 1, 'nombre': 'Cobertura de agua potable', 'meta': 85, 'actual': 82, 'avance': 96.5},
        {'id': 2, 'nombre': 'Tasa de alfabetización', 'meta': 95, 'actual': 93, 'avance': 97.9},
        {'id': 3, 'nombre': 'Acceso a vivienda digna', 'meta': 70, 'actual': 68, 'avance': 97.1},
        {'id': 4, 'nombre': 'Empleo juvenil', 'meta': 60, 'actual': 57, 'avance': 95.0},
        {'id': 5, 'nombre': 'Reducción de pobreza', 'meta': 45, 'actual': 43, 'avance': 95.6},
        {'id': 6, 'nombre': 'Cobertura eléctrica', 'meta': 90, 'actual': 87, 'avance': 96.7},
        {'id': 7, 'nombre': 'Acceso a internet', 'meta': 75, 'actual': 72, 'avance': 96.0},
        {'id': 8, 'nombre': 'Cobertura sanitaria', 'meta': 80, 'actual': 78, 'avance': 97.5}
    ]

    indicadores_chart = {
        'labels': [ind['nombre'][:20] + '...' for ind in indicadores_completos],
        'datasets': [{
            'label': 'Avance Actual (%)',
            'data': [ind['avance'] for ind in indicadores_completos],
            'backgroundColor': 'rgba(54, 162, 235, 0.8)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        }]
    }

    return {
        'success': True,
        'plan_id': plan.id,
        'plan_titulo': plan.titulo,
        'tipo_analisis': 'indicadores',
        'titulo': f'Análisis de Indicadores - {periodo}',
        'descripcion': 'Evaluación detallada del cumplimiento de indicadores',
        'tendencias': indicadores_chart,
        'presupuesto': None,
        'indicadores': indicadores_completos,
        'metricas': {
            'total_indicadores': len(indicadores_completos),
            'indicadores_cumplidos': len([i for i in indicadores_completos if i['avance'] >= 95]),
            'avance_promedio': sum(i['avance'] for i in indicadores_completos) / len(indicadores_completos),
            'indicador_mejor_desempeno': max(indicadores_completos, key=lambda x: x['avance'])['nombre']
        }
    }

def generar_analisis_comparativo(plan, periodo, tipo_grafico):
    """Genera datos para análisis comparativo"""
    comparativo_data = {
        'labels': ['2022', '2023', periodo],
        'datasets': [{
            'label': 'Ejecución Física (%)',
            'data': [65, 72, 83],
            'borderColor': 'rgba(75, 192, 192, 1)',
            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            'tension': 0.4
        }, {
            'label': 'Ejecución Financiera (%)',
            'data': [68, 75, 80],
            'borderColor': 'rgba(255, 159, 64, 1)',
            'backgroundColor': 'rgba(255, 159, 64, 0.2)',
            'tension': 0.4
        }, {
            'label': 'Satisfacción Ciudadana (%)',
            'data': [70, 76, 84],
            'borderColor': 'rgba(153, 102, 255, 1)',
            'backgroundColor': 'rgba(153, 102, 255, 0.2)',
            'tension': 0.4
        }]
    }

    return {
        'success': True,
        'plan_id': plan.id,
        'plan_titulo': plan.titulo,
        'tipo_analisis': 'comparativo',
        'titulo': f'Análisis Comparativo - {periodo}',
        'descripcion': 'Comparación histórica del desempeño del plan',
        'tendencias': comparativo_data,
        'presupuesto': None,
        'indicadores': [],
        'metricas': {
            'mejora_vs_anio_anterior': 11.5,
            'tendencia_general': 'positiva',
            'mejor_metrica': 'Satisfacción Ciudadana',
            'proyeccion_siguiente_anio': 88
        }
    }

def generar_analisis_tendencias(plan, periodo, tipo_grafico):
    """Genera datos para análisis de tendencias"""
    tendencias_completas = {
        'labels': ['2020', '2021', '2022', '2023', periodo, str(int(periodo) + 1)],
        'datasets': [{
            'label': 'Tendencia General',
            'data': [45, 52, 65, 72, 83, 89],
            'borderColor': 'rgba(54, 162, 235, 1)',
            'backgroundColor': 'rgba(54, 162, 235, 0.1)',
            'tension': 0.4,
            'fill': true
        }, {
            'label': 'Tendencia Óptima',
            'data': [50, 60, 70, 80, 88, 94],
            'borderColor': 'rgba(75, 192, 192, 1)',
            'backgroundColor': 'rgba(75, 192, 192, 0.1)',
            'tension': 0.4,
            'borderDash': [5, 5],
            'fill': false
        }]
    }

    return {
        'success': True,
        'plan_id': plan.id,
        'plan_titulo': plan.titulo,
        'tipo_analisis': 'tendencias',
        'titulo': f'Análisis de Tendencias - {periodo}',
        'descripcion': 'Proyección y análisis de tendencias futuras',
        'tendencias': tendencias_completas,
        'presupuesto': None,
        'indicadores': [],
        'metricas': {
            'tendencia_actual': 'creciente',
            'proyeccion_2027': 94,
            'velocidad_mejora': 3.2,
            'probabilidad_cumplimiento': 87
        }
    }
