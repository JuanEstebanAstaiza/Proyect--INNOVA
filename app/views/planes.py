from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import io
from datetime import datetime

from app import db
from app.models import (
    PlanDesarrollo, LineaEstrategica, Componente, Programa,
    Proyecto, Actividad, IndicadorProducto, EjecucionTrimestral, Documento,
    EditJustification
)
from app.forms.planes import (
    PlanForm, LineaEstrategicaForm, ComponenteForm,
    ProgramaForm, ProyectoForm, ActividadForm, IndicadorForm, DocumentoForm,
    EditarLineaEstrategicaForm, EditarComponenteForm, EditarProgramaForm,
    EditarProyectoForm, EditarActividadForm
)

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
    """Helper function to get a plan with 404 if not found, allowing editors to see global plans"""
    # Determinar si el usuario puede ver planes de otros municipios
    puede_ver_global = current_user.is_admin() or current_user.is_editor()

    if puede_ver_global:
        # Para administradores y editores, buscar el plan directamente sin filtro de municipio 
        plan = PlanDesarrollo.query.filter_by(id=plan_id).first_or_404()
    else:
        # Para usuarios normales (viewers), filtrar por municipio
        plan = PlanDesarrollo.query.filter_by(id=plan_id, municipio=current_user).first_or_404()

    return plan

def build_plan_filter(current_user):
    """Helper function to build plan filter based on user permissions"""
    puede_ver_global = current_user.is_admin() or current_user.is_editor()

    if puede_ver_global:
        # Para administradores y editores, no filtrar por municipio
        return PlanDesarrollo.municipio_id != None  # Siempre verdadero
    else:
        # Para usuarios normales (viewers), filtrar por municipio
        return PlanDesarrollo.municipio_id == current_user.id

def get_plan_or_redirect(plan_id, current_user, redirect_endpoint='planes.index'):
    """Helper function to get a plan or redirect to an available one"""
    # Determinar si el usuario puede ver planes de otros municipios
    puede_ver_global = current_user.is_admin() or current_user.is_editor()

    if puede_ver_global:
        # Para administradores y editores, buscar el plan directamente sin filtro de municipio
        plan = PlanDesarrollo.query.filter_by(id=plan_id).first()
    else:
        # Para usuarios normales (viewers), filtrar por municipio
        plan = PlanDesarrollo.query.filter_by(id=plan_id, municipio=current_user).first()

    if not plan:
        if puede_ver_global:
            # Buscar el plan activo global
            plan_activo = PlanDesarrollo.query.filter_by(estado='activo').first()

            if plan_activo:
                flash(f'El plan solicitado no fue encontrado. Redirigiendo al plan activo.', 'info')
                return redirect(url_for('planes.ver', plan_id=plan_activo.id))
            else:
                # Si no hay plan activo global, buscar el más reciente sin filtro de municipio
                plan_reciente = PlanDesarrollo.query.order_by(
                    PlanDesarrollo.created_at.desc()
                ).first()

                if plan_reciente:
                    flash(f'El plan solicitado no fue encontrado. Redirigiendo al plan más reciente.', 'info')
                    return redirect(url_for('planes.ver', plan_id=plan_reciente.id))
                else:
                    flash('No se encontraron planes disponibles. Por favor cree un plan primero.', 'warning')
                    return redirect(url_for(redirect_endpoint))
        else:
            # Lógica original para usuarios normales (viewers)
            plan_activo = PlanDesarrollo.query.filter_by(
                municipio=current_user,
                estado='activo'
            ).first()

            if plan_activo:
                flash(f'El plan solicitado no fue encontrado. Redirigiendo al plan activo.', 'info')
                return redirect(url_for('planes.ver', plan_id=plan_activo.id))
            else:
                plan_reciente = PlanDesarrollo.query.filter_by(municipio=current_user).order_by(
                    PlanDesarrollo.created_at.desc()
                ).first()

                if plan_reciente:
                    flash(f'El plan solicitado no fue encontrado. Redirigiendo al plan más reciente.', 'info')
                    return redirect(url_for('planes.ver', plan_id=plan_reciente.id))
                else:
                    flash('No se encontraron planes disponibles. Por favor cree un plan primero.', 'warning')
                    return redirect(url_for(redirect_endpoint))

    return plan

# Lista de planes
@planes_bp.route('/')
@login_required
def index():
    """Lista todos los planes del usuario actual"""
    # Determinar si el usuario puede ver planes de otros municipios
    puede_ver_global = current_user.is_admin() or current_user.is_editor()

    if not puede_ver_global:
        # Para usuarios normales (viewers), mostrar solo el plan activo de su municipio
        plan_activo = PlanDesarrollo.get_plan_activo_o_primero(current_user)
        planes = [plan_activo] if plan_activo else []
        mostrar_todos = False
    else:
        # Para administradores y editores, mostrar el plan activo global primero
        plan_activo_global = PlanDesarrollo.query.filter_by(estado='activo').first()
        if plan_activo_global:
            # Si hay plan activo global, mostrarlo junto con los planes del municipio del usuario
            planes_municipio = PlanDesarrollo.query.filter_by(municipio=current_user).all()
            # Evitar duplicados
            planes = [plan_activo_global] if plan_activo_global not in planes_municipio else []
            planes.extend(planes_municipio)
            mostrar_todos = True
        else:
            # Si no hay plan activo global, mostrar los del municipio del usuario
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
    plan = get_plan_or_404(plan_id, current_user)

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
    plan = PlanDesarrollo.query.filter_by(id=plan_id).first_or_404()
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
            flash(f'Error al actualizar la línea estratégica: {str(e)}', 'danger')

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
                    can_edit_row = current_user.can_edit_row(indicador.id if indicador else 0, plan.id) if indicador else False

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

                    # Agregar información de documentos asociados
                    documentos_linea = get_documentos_asociados(linea_id=linea.id)
                    documentos_componente = get_documentos_asociados(componente_id=componente.id)
                    documentos_programa = get_documentos_asociados(programa_id=programa.id)
                    documentos_proyecto = get_documentos_asociados(proyecto_id=proyecto.id)
                    documentos_indicador = get_documentos_asociados(indicador_id=indicador.id) if indicador else []

                    row['documentos_linea'] = len(documentos_linea)
                    row['documentos_componente'] = len(documentos_componente)
                    row['documentos_programa'] = len(documentos_programa)
                    row['documentos_proyecto'] = len(documentos_proyecto)
                    row['documentos_indicador'] = len(documentos_indicador)
                    row['total_documentos'] = (len(documentos_linea) + len(documentos_componente) +
                                             len(documentos_programa) + len(documentos_proyecto) +
                                             len(documentos_indicador))

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

        # Agregar campos de documentos a la fila de ejemplo
        row_ejemplo['documentos_linea'] = 0
        row_ejemplo['documentos_componente'] = 0
        row_ejemplo['documentos_programa'] = 0
        row_ejemplo['documentos_proyecto'] = 0
        row_ejemplo['documentos_indicador'] = 0
        row_ejemplo['total_documentos'] = 0

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

    plan = get_plan_or_404(plan_id, current_user)

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
        return redirect(url_for('planes.ver_excel', plan_id=plan_id))

    plan = PlanDesarrollo.query.filter_by(id=plan_id).first_or_404()

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
        flash(f'Error al procesar el archivo Excel: {str(e)}', 'error')

    return redirect(url_for('planes.ver_excel', plan_id=plan_id))

@planes_bp.route('/<int:plan_id>/guardar-excel', methods=['POST'])
@login_required
def guardar_excel(plan_id):
    """Guardar cambios desde la vista Excel"""
    from flask import jsonify

    plan = get_plan_or_404(plan_id, current_user)

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
    """Editar una celda individual de Excel con justificación y soporte de archivos"""
    from flask import jsonify, request
    from werkzeug.utils import secure_filename
    import os

    plan = get_plan_or_404(plan_id, current_user)

    try:
        # Obtener datos del formulario
        column_name = request.form.get('column_name')
        new_value = request.form.get('new_value')
        justification = request.form.get('justification')
        indicator_id = request.form.get('indicator_id')

        # Validaciones básicas
        if not column_name or not new_value or not justification:
            return jsonify({
                'success': False,
                'error': 'Faltan datos requeridos'
            }), 400

        # Buscar el indicador si existe
        indicador = None
        if indicator_id:
            try:
                indicador = IndicadorProducto.query.filter_by(
                    id=int(indicator_id),
                    proyecto_id=Proyecto.query.join(Programa).join(Componente).join(LineaEstrategica).filter(LineaEstrategica.plan_id == plan_id).subquery().c.id
                ).first()
            except:
                indicador = None

        # Obtener el valor anterior
        old_value = None
        if indicador:
            # Para indicadores, obtener el valor actual del campo correspondiente
            if hasattr(indicador, column_name):
                old_value = getattr(indicador, column_name)
            elif column_name.startswith('ejecucion_') or column_name.startswith('cumplimiento_') or column_name.startswith('poblacion_impactada_') or column_name.startswith('observacion_'):
                # Para datos trimestrales, buscar en EjecucionTrimestral
                trimestre = None
                if '_trimestre' in column_name:
                    parts = column_name.split('_')
                    if len(parts) >= 2:
                        try:
                            trimestre = int(parts[1])
                        except:
                            trimestre = None

                if trimestre:
                    ejecucion = EjecucionTrimestral.query.filter_by(
                        indicador_id=indicador.id,
                        anio=2024,
                        trimestre=trimestre
                    ).first()

                    if ejecucion:
                        if column_name.startswith('ejecucion_'):
                            old_value = ejecucion.ejecucion_trimestral
                        elif column_name.startswith('cumplimiento_'):
                            old_value = ejecucion.cumplimiento_trimestral
                        elif column_name.startswith('poblacion_impactada_'):
                            old_value = ejecucion.poblacion_impactada_trimestral
                        elif column_name.startswith('observacion_'):
                            old_value = ejecucion.observacion_trimestral

        # Manejar archivo de soporte
        support_file_path = None
        if 'support_file' in request.files:
            file = request.files['support_file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                # Crear nombre único para el archivo
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{timestamp}_{current_user.id}_{filename}"
                file_path = os.path.join('uploads', 'justifications', unique_filename)

                # Asegurar que el directorio existe
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                # Guardar el archivo
                file.save(file_path)
                support_file_path = file_path

        # Crear registro de justificación
        edit_justification = EditJustification(
            plan_id=plan_id,
            indicador_id=indicador.id if indicador else None,
            column_name=column_name,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value),
            justification=justification,
            support_file_path=support_file_path,
            user_id=current_user.id
        )

        db.session.add(edit_justification)
        db.session.flush()  # Para obtener el ID de la justificación

        # Crear archivo de auditoría
        try:
            from audit_file_system import create_audit_file
            audit_file_path = create_audit_file(edit_justification)
            if audit_file_path:
                print(f"Archivo de auditoría creado: {audit_file_path}")
        except Exception as e:
            print(f"Error creando archivo de auditoría: {e}")

        # Actualizar el valor en la base de datos
        if indicador:
            if hasattr(indicador, column_name):
                # Actualizar campo directo del indicador
                if column_name in ['linea_base', 'meta_cuatrienio', 'meta_2024']:
                    try:
                        setattr(indicador, column_name, float(new_value) if new_value else 0.0)
                    except:
                        setattr(indicador, column_name, 0.0)
                else:
                    setattr(indicador, column_name, new_value)
                indicador.updated_at = datetime.utcnow()
            elif column_name.startswith(('ejecucion_', 'cumplimiento_', 'poblacion_impactada_', 'observacion_')) and '_trimestre' in column_name:
                # Actualizar datos trimestrales
                parts = column_name.split('_')
                if len(parts) >= 2:
                    try:
                        trimestre = int(parts[1])
                    except:
                        trimestre = None

                    if trimestre:
                        # Buscar o crear registro de ejecución trimestral
                        ejecucion = EjecucionTrimestral.query.filter_by(
                            indicador_id=indicador.id,
                            anio=2024,
                            trimestre=trimestre
                        ).first()

                        if not ejecucion:
                            ejecucion = EjecucionTrimestral(
                                indicador_id=indicador.id,
                                proyecto_id=indicador.proyecto_id,
                                usuario_id=current_user.id,
                                anio=2024,
                                trimestre=trimestre
                            )
                            db.session.add(ejecucion)

                        # Actualizar el campo correspondiente
                        if column_name.startswith('ejecucion_'):
                            try:
                                ejecucion.ejecucion_trimestral = float(new_value) if new_value else 0.0
                                # Recalcular cumplimiento
                                if indicador.meta_2024 and indicador.meta_2024 > 0:
                                    ejecucion.cumplimiento_trimestral = (ejecucion.ejecucion_trimestral / indicador.meta_2024) * 100
                            except:
                                ejecucion.ejecucion_trimestral = 0.0
                        elif column_name.startswith('cumplimiento_'):
                            try:
                                ejecucion.cumplimiento_trimestral = float(new_value) if new_value else 0.0
                            except:
                                ejecucion.cumplimiento_trimestral = 0.0
                        elif column_name.startswith('poblacion_impactada_'):
                            try:
                                ejecucion.poblacion_impactada_trimestral = int(float(new_value)) if new_value else 0
                            except:
                                ejecucion.poblacion_impactada_trimestral = 0
                        elif column_name.startswith('observacion_'):
                            ejecucion.observacion_trimestral = new_value

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Celda editada exitosamente',
            'edit_id': edit_justification.id
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error al editar celda: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

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
        for field_name in form._fields:
            field = form._fields[field_name]
            current_app.logger.info(f"Campo {field_name}: {getattr(form, field_name).data} (errores: {getattr(form, field_name).errors})")

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
            current_app.logger.info(f"Archivo guardado exitosamente")

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
    plan = get_plan_or_404(plan_id, current_user)
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
    plan = get_plan_or_404(plan_id, current_user)
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
    from app.models import Documento
    import datetime

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

    from app.models import IndicadorProducto, Proyecto, Programa, Componente, LineaEstrategica, EjecucionTrimestral

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

        # Intentar obtener datos usando la función principal
        datos_plan = obtener_datos_plan_completo(plan, '2024', None)
        debug_info['datos'] = {
            'total_registros': len(datos_plan['datos']),
            'columnas': datos_plan['columnas'],
            'error': datos_plan.get('error', None)
        }

    except Exception as e:
        debug_info['error'] = str(e)
        debug_info['error_type'] = type(e).__name__

    return debug_info


