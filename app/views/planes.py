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
    """API para obtener datos JSON para los reportes con datos reales del plan activo"""
    plan = get_plan_or_redirect(plan_id, current_user)
    if hasattr(plan, 'status_code'):
        return plan

    from app.models import IndicadorProducto, Proyecto, Programa, Componente, LineaEstrategica, EjecucionTrimestral

    # Obtener parámetros de consulta
    tipo_analisis = request.args.get('tipo_analisis', 'general')
    periodo = request.args.get('periodo', '2024')
    tipo_grafico = request.args.get('tipo_grafico', 'lineas')
    columnas_seleccionadas = request.args.get('columnas', '').split(',') if request.args.get('columnas') else None

    try:
        # Obtener datos reales del plan
        datos_plan = obtener_datos_plan_completo(plan, periodo, columnas_seleccionadas)

        # Si no hay datos reales, usar datos de ejemplo
        if not datos_plan['datos'] or len(datos_plan['datos']) == 0:
            current_app.logger.warning("⚠️ No hay datos reales, usando datos de ejemplo")
            return generar_datos_ejemplo(tipo_analisis, periodo, tipo_grafico, plan, datos_plan)

        # Generar datos para gráficos basados en el tipo de análisis
        if tipo_analisis == 'general':
            data = generar_analisis_general_real(datos_plan, periodo, tipo_grafico)
        elif tipo_analisis == 'ejecucion':
            data = generar_analisis_ejecucion_real(datos_plan, periodo, tipo_grafico)
        elif tipo_analisis == 'presupuesto':
            data = generar_analisis_presupuesto_real(datos_plan, periodo, tipo_grafico)
        elif tipo_analisis == 'indicadores':
            data = generar_analisis_indicadores_real(datos_plan, periodo, tipo_grafico)
        elif tipo_analisis == 'comparativo':
            data = generar_analisis_comparativo_real(datos_plan, periodo, tipo_grafico)
        elif tipo_analisis == 'tendencias':
            data = generar_analisis_tendencias_real(datos_plan, periodo, tipo_grafico)
        else:
            data = generar_analisis_general_real(datos_plan, periodo, tipo_grafico)

        return data

    except Exception as e:
        current_app.logger.error(f'Error en reportes_datos: {str(e)}')
        # En caso de error, devolver datos de ejemplo
        return generar_datos_ejemplo(tipo_analisis, periodo, tipo_grafico, plan, {'columnas': []})

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
            'fill': True
        }, {
            'label': 'Tendencia Óptima',
            'data': [50, 60, 70, 80, 88, 94],
            'borderColor': 'rgba(75, 192, 192, 1)',
            'backgroundColor': 'rgba(75, 192, 192, 0.1)',
            'tension': 0.4,
            'borderDash': [5, 5],
            'fill': False
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


def obtener_datos_plan_completo(plan, periodo, columnas_seleccionadas=None):
    """
    Obtiene todos los datos del plan de desarrollo activo para crear una tabla unificada
    que sirva como fuente para Business Intelligence
    """
    from app.models import IndicadorProducto, Proyecto, Programa, Componente, LineaEstrategica, EjecucionTrimestral

    current_app.logger.info(f"🔍 Iniciando obtención de datos para plan: {plan.id} - {plan.titulo}")

    datos_completos = []

    # Columnas disponibles por defecto para BI
    columnas_default = [
        'id_indicador', 'cod_indicador', 'nombre_indicador', 'tipo_indicador',
        'linea_base', 'meta_cuatrienio', 'meta_2024', 'unidad',
        'cod_linea', 'nombre_linea', 'cod_componente', 'nombre_componente',
        'cod_programa', 'nombre_programa', 'cod_proyecto', 'nombre_proyecto',
        'ejecucion_q1', 'ejecucion_q2', 'ejecucion_q3', 'ejecucion_q4',
        'cumplimiento_q1', 'cumplimiento_q2', 'cumplimiento_q3', 'cumplimiento_q4',
        'ejecucion_acumulada', 'cumplimiento_acumulado',
        'presupuesto_ejecutado_q1', 'presupuesto_ejecutado_q2',
        'presupuesto_ejecutado_q3', 'presupuesto_ejecutado_q4',
        'presupuesto_ejecutado_acumulado', 'poblacion_impactada_q1',
        'poblacion_impactada_q2', 'poblacion_impactada_q3', 'poblacion_impactada_q4',
        'poblacion_impactada_acumulada', 'avance_porcentual', 'estado'
    ]

    # Si se especifican columnas, usar solo esas
    if columnas_seleccionadas and len(columnas_seleccionadas) > 0:
        columnas_a_usar = [col for col in columnas_seleccionadas if col in columnas_default]
        if not columnas_a_usar:
            columnas_a_usar = columnas_default[:10]  # Usar primeras 10 si ninguna coincide
    else:
        columnas_a_usar = columnas_default

    current_app.logger.info(f"📊 Columnas a usar: {columnas_a_usar}")

    try:
        # Obtener todos los indicadores del plan de una vez para evitar problemas de lazy loading
        from app.models import IndicadorProducto
        # Cambiar filtro para incluir indicadores en ejecución también
        indicadores_plan = IndicadorProducto.query.filter(IndicadorProducto.estado.in_(['activo', 'en_ejecucion'])).all()
        indicadores_por_proyecto = {}

        # Organizar indicadores por proyecto
        for indicador in indicadores_plan:
            proyecto_id = indicador.proyecto_id
            if proyecto_id not in indicadores_por_proyecto:
                indicadores_por_proyecto[proyecto_id] = []
            indicadores_por_proyecto[proyecto_id].append(indicador)

        current_app.logger.info(f"📊 Total indicadores en plan: {len(indicadores_plan)}")
        current_app.logger.info(f"📊 Proyectos con indicadores: {len(indicadores_por_proyecto)}")

        # Usar el plan original (ya que no necesitamos joinedload)
        plan_cargado = plan

        # Verificar si el plan tiene líneas estratégicas
        lineas_count = len(plan_cargado.lineas_estrategicas)
        current_app.logger.info(f"🏗️ Plan tiene {lineas_count} líneas estratégicas")

        if lineas_count == 0:
            current_app.logger.warning("⚠️ El plan no tiene líneas estratégicas")
            return {
                'datos': [],
                'columnas': columnas_a_usar,
                'total_registros': 0,
                'periodo': periodo,
                'plan_titulo': plan.titulo,
                'error': 'El plan no tiene líneas estratégicas configuradas'
            }

        # Recorrer todas las líneas estratégicas del plan
        linea_count = 0
        componente_count = 0
        programa_count = 0
        proyecto_count = 0
        indicador_count = 0

        for linea in plan_cargado.lineas_estrategicas:
            linea_count += 1
            current_app.logger.debug(f"Procesando línea {linea_count}/{lineas_count}: {linea.nombre}")

            # Cambiar filtro para incluir líneas en ejecución también
            if linea.estado not in ['activo', 'en_ejecucion']:
                current_app.logger.debug(f"Línea {linea.nombre} no está operativa (estado: {linea.estado})")
                continue

            # Verificar que la línea tenga componentes
            if not hasattr(linea, 'componentes'):
                current_app.logger.error(f"❌ Línea {linea.nombre} no tiene atributo 'componentes'")
                continue

            componentes_linea = linea.componentes
            current_app.logger.debug(f"Línea {linea.nombre} tiene {len(componentes_linea)} componentes")

            for componente in componentes_linea:
                componente_count += 1
                current_app.logger.debug(f"Procesando componente: {componente.nombre}")

                if componente.estado not in ['activo', 'en_ejecucion']:
                    continue

                # Verificar que el componente tenga programas
                if not hasattr(componente, 'programas'):
                    current_app.logger.error(f"❌ Componente {componente.nombre} no tiene atributo 'programas'")
                    continue

                programas_componente = componente.programas
                current_app.logger.debug(f"Componente {componente.nombre} tiene {len(programas_componente)} programas")

                for programa in programas_componente:
                    programa_count += 1
                    current_app.logger.debug(f"Procesando programa: {programa.nombre}")

                    if programa.estado not in ['activo', 'en_ejecucion']:
                        continue

                    # Verificar que el programa tenga proyectos
                    if not hasattr(programa, 'proyectos'):
                        current_app.logger.error(f"❌ Programa {programa.nombre} no tiene atributo 'proyectos'")
                        continue

                    proyectos_programa = programa.proyectos
                    current_app.logger.debug(f"Programa {programa.nombre} tiene {len(proyectos_programa)} proyectos")

                    for proyecto in proyectos_programa:
                        proyecto_count += 1
                        current_app.logger.debug(f"Procesando proyecto: {proyecto.nombre}")

                        if proyecto.estado not in ['activo', 'en_ejecucion']:
                            current_app.logger.debug(f"⚠️ Proyecto {proyecto.nombre} no está operativo (estado: {proyecto.estado})")
                            continue

                        current_app.logger.debug(f"✅ Proyecto {proyecto.nombre} está operativo (estado: {proyecto.estado}), continuando verificación...")

                        # Verificar que el proyecto tenga indicadores
                        current_app.logger.debug(f"🔍 Verificando proyecto: {proyecto.nombre} (ID: {proyecto.id})")

                        # Obtener indicadores del proyecto usando el diccionario pre-cargado
                        indicadores_proyecto = indicadores_por_proyecto.get(proyecto.id, [])
                        current_app.logger.debug(f"📊 Proyecto {proyecto.nombre} tiene {len(indicadores_proyecto)} indicadores activos")

                        if len(indicadores_proyecto) == 0:
                            current_app.logger.debug(f"⚠️ Proyecto {proyecto.nombre} no tiene indicadores activos, saltando...")
                            continue

                        # Para cada indicador del proyecto
                        current_app.logger.debug(f"Procesando {len(indicadores_proyecto)} indicadores del proyecto {proyecto.nombre}")
                        for indicador in indicadores_proyecto:
                            indicador_count += 1
                            current_app.logger.debug(f"Procesando indicador {indicador_count}: {indicador.nombre} (ID: {indicador.id}, Estado: {indicador.estado})")

                            # Verificar que el indicador tenga todos los campos necesarios
                            if not hasattr(indicador, 'estado') or indicador.estado not in ['activo', 'en_ejecucion']:
                                current_app.logger.debug(f"Indicador {indicador.nombre} no está activo (estado: {getattr(indicador, 'estado', 'N/A')})")
                                continue

                            try:
                                # Obtener todas las ejecuciones del indicador para el período
                                ejecuciones = indicador.get_ejecuciones_por_anio(int(periodo))
                                current_app.logger.debug(f"Indicador {indicador.nombre} tiene {len(ejecuciones)} ejecuciones en {periodo}")

                                # Crear fila de datos con todas las columnas disponibles
                                fila_datos = {
                                    'id_indicador': indicador.id,
                                    'cod_indicador': getattr(indicador, 'cod_indicador', ''),
                                    'nombre_indicador': indicador.nombre,
                                    'tipo_indicador': getattr(indicador, 'tipo_indicador', ''),
                                    'linea_base': indicador.linea_base,
                                    'meta_cuatrienio': indicador.meta_cuatrienio,
                                    'meta_2024': indicador.meta_2024,
                                    'unidad': getattr(indicador, 'unidad', ''),
                                    'cod_linea': linea.cod_linea,
                                    'nombre_linea': linea.nombre,
                                    'cod_componente': getattr(componente, 'cod_componente', ''),
                                    'nombre_componente': componente.nombre,
                                    'cod_programa': getattr(programa, 'cod_programa', ''),
                                    'nombre_programa': programa.nombre,
                                    'cod_proyecto': getattr(proyecto, 'cod_proyecto', ''),
                                    'nombre_proyecto': proyecto.nombre,
                                    'estado': indicador.estado
                                }

                                # Inicializar columnas de ejecución
                                for trimestre in range(1, 5):
                                    fila_datos[f'ejecucion_q{trimestre}'] = 0.0
                                    fila_datos[f'cumplimiento_q{trimestre}'] = 0.0
                                    fila_datos[f'presupuesto_ejecutado_q{trimestre}'] = 0.0
                                    fila_datos[f'poblacion_impactada_q{trimestre}'] = 0

                                fila_datos['ejecucion_acumulada'] = 0.0
                                fila_datos['cumplimiento_acumulado'] = 0.0
                                fila_datos['presupuesto_ejecutado_acumulado'] = 0.0
                                fila_datos['poblacion_impactada_acumulada'] = 0

                                # Llenar con datos reales de ejecuciones
                                for ejecucion in ejecuciones:
                                    trimestre = ejecucion.trimestre
                                    fila_datos[f'ejecucion_q{trimestre}'] = ejecucion.ejecucion_trimestral
                                    fila_datos[f'cumplimiento_q{trimestre}'] = ejecucion.cumplimiento_trimestral
                                    fila_datos[f'presupuesto_ejecutado_q{trimestre}'] = ejecucion.presupuesto_ejecutado_trimestral
                                    fila_datos[f'poblacion_impactada_q{trimestre}'] = ejecucion.poblacion_impactada_trimestral

                                # Calcular valores acumulados (última ejecución disponible)
                                ultima_ejecucion = indicador.get_ultima_ejecucion()
                                if ultima_ejecucion:
                                    fila_datos['ejecucion_acumulada'] = ultima_ejecucion.ejecucion_acumulada
                                    fila_datos['cumplimiento_acumulado'] = ultima_ejecucion.cumplimiento_acumulado
                                    fila_datos['presupuesto_ejecutado_acumulado'] = ultima_ejecucion.presupuesto_ejecutado_acumulado
                                    fila_datos['poblacion_impactada_acumulada'] = ultima_ejecucion.poblacion_impactada_acumulada

                                # Calcular avance porcentual
                                fila_datos['avance_porcentual'] = indicador.get_progreso_porcentual()

                                # Filtrar solo las columnas solicitadas
                                fila_filtrada = {col: fila_datos[col] for col in columnas_a_usar if col in fila_datos}
                                datos_completos.append(fila_filtrada)
                                current_app.logger.debug(f"✅ Indicador {indicador.nombre} procesado correctamente")

                            except Exception as e:
                                current_app.logger.error(f"❌ Error procesando indicador {indicador.nombre}: {str(e)}")
                                import traceback
                                current_app.logger.error(f"Traceback: {traceback.format_exc()}")
                                continue

        current_app.logger.info(f"✅ Procesamiento completado: {linea_count} líneas, {componente_count} componentes, {programa_count} programas, {proyecto_count} proyectos, {indicador_count} indicadores")
        current_app.logger.info(f"📊 Total registros generados: {len(datos_completos)}")

    except Exception as e:
        current_app.logger.error(f"❌ Error general en obtener_datos_plan_completo: {str(e)}")
        return {
            'datos': [],
            'columnas': columnas_a_usar,
            'total_registros': 0,
            'periodo': periodo,
            'plan_titulo': plan.titulo,  # Usar plan original en caso de error
            'error': str(e)
        }

    return {
        'datos': datos_completos,
        'columnas': columnas_a_usar,
        'total_registros': len(datos_completos),
        'periodo': periodo,
        'plan_titulo': plan_cargado.titulo
    }


def generar_datos_ejemplo(tipo_analisis, periodo, tipo_grafico, plan, datos_plan):
    """Genera datos de ejemplo cuando no hay datos reales disponibles"""
    current_app.logger.info("📊 Generando datos de ejemplo para análisis BI")

    # Datos de ejemplo para indicadores
    indicadores_ejemplo = [
        {
            'id': 1,
            'nombre': 'Cobertura de agua potable',
            'meta_2024': 85,
            'ejecucion_q1': 75,
            'avance': 88,
            'linea_estrategica': 'Infraestructura Básica',
            'componente': 'Servicios Públicos',
            'programa': 'Agua y Saneamiento',
            'proyecto': 'Sistema de Acueducto'
        },
        {
            'id': 2,
            'nombre': 'Tasa de alfabetización',
            'meta_2024': 95,
            'ejecucion_q1': 92,
            'avance': 97,
            'linea_estrategica': 'Desarrollo Humano',
            'componente': 'Educación',
            'programa': 'Educación Básica',
            'proyecto': 'Campaña de Alfabetización'
        },
        {
            'id': 3,
            'nombre': 'Empleo juvenil',
            'meta_2024': 60,
            'ejecucion_q1': 55,
            'avance': 92,
            'linea_estrategica': 'Desarrollo Económico',
            'componente': 'Empleo',
            'programa': 'Inserción Laboral',
            'proyecto': 'Programa Jóvenes al Trabajo'
        }
    ]

    # Datos para gráficos según el tipo de análisis
    if tipo_analisis == 'general':
        return {
            'success': True,
            'tipo_analisis': 'general',
            'titulo': f'Análisis General - {periodo} (Datos de Ejemplo)',
            'descripcion': f'Análisis basado en datos de ejemplo. Plan: {plan.titulo}',
            'tendencias': {
                'labels': ['Q1', 'Q2', 'Q3', 'Q4'],
                'datasets': [{
                    'label': f'Ejecución Promedio {periodo}',
                    'data': [15, 25, 35, 45],
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'backgroundColor': 'rgba(54, 162, 235, 0.1)',
                    'tension': 0.4
                }]
            },
            'presupuesto': {
                'labels': ['Infraestructura', 'Educación', 'Salud'],
                'datasets': [{
                    'data': [35, 25, 20],
                    'backgroundColor': [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 205, 86, 0.8)'
                    ]
                }]
            },
            'indicadores': indicadores_ejemplo,
            'metricas': {
                'total_indicadores': len(indicadores_ejemplo),
                'avance_promedio': 92.3,
                'indicadores_completados': 1,
                'anio_inicio': 2024,
                'anio_fin': 2027
            }
        }
    elif tipo_analisis == 'indicadores':
        return {
            'success': True,
            'tipo_analisis': 'indicadores',
            'titulo': f'Análisis de Indicadores - {periodo} (Datos de Ejemplo)',
            'descripcion': f'Análisis detallado de indicadores. Plan: {plan.titulo}',
            'tendencias': {
                'labels': ['Indicador 1', 'Indicador 2', 'Indicador 3'],
                'datasets': [{
                    'label': 'Avance (%)',
                    'data': [88, 97, 92],
                    'backgroundColor': 'rgba(54, 162, 235, 0.8)'
                }]
            },
            'presupuesto': None,
            'indicadores': indicadores_ejemplo,
            'metricas': {
                'total_indicadores': len(indicadores_ejemplo),
                'avance_promedio': 92.3,
                'indicadores_completados': 1
            }
        }
    else:
        # Análisis por defecto
        return {
            'success': True,
            'tipo_analisis': tipo_analisis,
            'titulo': f'{tipo_analisis.title()} - {periodo} (Datos de Ejemplo)',
            'descripcion': f'Análisis {tipo_analisis} basado en datos de ejemplo. Plan: {plan.titulo}',
            'tendencias': {
                'labels': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
                'datasets': [{
                    'label': 'Tendencia de Ejemplo',
                    'data': [10, 20, 30, 40, 50, 60],
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'backgroundColor': 'rgba(54, 162, 235, 0.1)',
                    'tension': 0.4
                }]
            },
            'presupuesto': None,
            'indicadores': indicadores_ejemplo,
            'metricas': {
                'total_indicadores': len(indicadores_ejemplo),
                'avance_promedio': 92.3,
                'indicadores_completados': 1
            }
        }


def generar_analisis_general_real(datos_plan, periodo, tipo_grafico):
    """Genera datos para análisis general usando datos reales"""
    datos = datos_plan['datos']

    if not datos:
        return generar_analisis_general_fallback(periodo, tipo_grafico)

    # Calcular métricas generales
    total_indicadores = len(datos)
    indicadores_completados = sum(1 for d in datos if d.get('avance_porcentual', 0) >= 100)
    avance_promedio = sum(d.get('avance_porcentual', 0) for d in datos) / total_indicadores if total_indicadores > 0 else 0

    # Datos para gráfico de tendencias (ejecución por trimestre)
    labels_trimestres = ['Q1', 'Q2', 'Q3', 'Q4']
    ejecucion_promedio = []

    for trimestre in range(1, 5):
        valores_trimestre = [d.get(f'ejecucion_q{trimestre}', 0) for d in datos if d.get(f'ejecucion_q{trimestre}', 0) > 0]
        promedio_trimestre = sum(valores_trimestre) / len(valores_trimestre) if valores_trimestre else 0
        ejecucion_promedio.append(promedio_trimestre)

    tendencias_data = {
        'labels': labels_trimestres,
        'datasets': [{
            'label': f'Ejecución Promedio {periodo}',
            'data': ejecucion_promedio,
            'borderColor': 'rgba(54, 162, 235, 1)',
            'backgroundColor': 'rgba(54, 162, 235, 0.1)',
            'tension': 0.4
        }]
    }

    # Datos para distribución presupuestaria por línea estratégica
    lineas_presupuesto = {}
    for dato in datos:
        linea = dato.get('nombre_linea', 'Sin línea')
        presupuesto = dato.get('presupuesto_ejecutado_acumulado', 0)
        if linea not in lineas_presupuesto:
            lineas_presupuesto[linea] = 0
        lineas_presupuesto[linea] += presupuesto

    presupuesto_data = {
        'labels': list(lineas_presupuesto.keys()),
        'datasets': [{
            'data': list(lineas_presupuesto.values()),
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

    # Preparar indicadores para la tabla (primeros 10 para no sobrecargar)
    indicadores_data = []
    for i, dato in enumerate(datos[:10]):
        indicadores_data.append({
            'id': dato.get('id_indicador', i+1),
            'nombre': dato.get('nombre_indicador', 'Sin nombre'),
            'meta_2024': dato.get('meta_2024', 0),
            'ejecucion_q1': dato.get('ejecucion_q1', 0),
            'avance': dato.get('avance_porcentual', 0)
        })

    return {
        'success': True,
        'plan_id': datos_plan.get('plan_id', 0),
        'plan_titulo': datos_plan.get('plan_titulo', ''),
        'tipo_analisis': 'general',
        'titulo': f'Análisis General - {periodo}',
        'descripcion': f'Análisis basado en {total_indicadores} indicadores del plan de desarrollo',
        'tendencias': tendencias_data,
        'presupuesto': presupuesto_data,
        'indicadores': indicadores_data,
        'metricas': {
            'total_indicadores': total_indicadores,
            'indicadores_completados': indicadores_completados,
            'avance_promedio': round(avance_promedio, 2),
            'anio_inicio': 2024,
            'anio_fin': 2027
        }
    }


def generar_analisis_general_fallback(periodo, tipo_grafico):
    """Genera datos de ejemplo cuando no hay datos reales"""
    return {
        'success': True,
        'tipo_analisis': 'general',
        'titulo': f'Análisis General - {periodo} (Datos de Ejemplo)',
        'descripcion': 'No hay datos reales disponibles, mostrando datos de ejemplo',
        'tendencias': {
            'labels': ['Q1', 'Q2', 'Q3', 'Q4'],
            'datasets': [{
                'label': f'Ejecución Promedio {periodo}',
                'data': [15, 25, 35, 45],
                'borderColor': 'rgba(54, 162, 235, 1)',
                'backgroundColor': 'rgba(54, 162, 235, 0.1)',
                'tension': 0.4
            }]
        },
        'presupuesto': {
            'labels': ['Infraestructura', 'Educación', 'Salud'],
            'datasets': [{
                'data': [35, 25, 20],
                'backgroundColor': [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 205, 86, 0.8)'
                ]
            }]
        },
        'indicadores': [
            {'id': 1, 'nombre': 'Indicador de ejemplo', 'meta_2024': 100, 'ejecucion_q1': 75, 'avance': 75}
        ],
        'metricas': {
            'total_indicadores': 1,
            'indicadores_completados': 0,
            'avance_promedio': 75,
            'anio_inicio': 2024,
            'anio_fin': 2027
        }
    }


def generar_analisis_ejecucion_real(datos_plan, periodo, tipo_grafico):
    """Genera datos para análisis de ejecución por trimestre usando datos reales"""
    datos = datos_plan['datos']

    if not datos:
        return generar_analisis_ejecucion_fallback(datos_plan, periodo, tipo_grafico)

    # Calcular promedios por trimestre
    promedios_fisicos = []
    promedios_financieros = []

    for trimestre in range(1, 5):
        ejecucion_fisica = [d.get(f'ejecucion_q{trimestre}', 0) for d in datos]
        cumplimiento_trimestre = [d.get(f'cumplimiento_q{trimestre}', 0) for d in datos]

        promedio_fisico = sum(ejecucion_fisica) / len(ejecucion_fisica) if ejecucion_fisica else 0
        promedio_financiero = sum(cumplimiento_trimestre) / len(cumplimiento_trimestre) if cumplimiento_trimestre else 0

        promedios_fisicos.append(promedio_fisico)
        promedios_financieros.append(promedio_financiero)

    ejecucion_data = {
        'labels': ['Q1', 'Q2', 'Q3', 'Q4'],
        'datasets': [{
            'label': f'Ejecución Física {periodo} (%)',
            'data': promedios_fisicos,
            'borderColor': 'rgba(75, 192, 192, 1)',
            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            'tension': 0.4
        }, {
            'label': f'Cumplimiento {periodo} (%)',
            'data': promedios_financieros,
            'borderColor': 'rgba(255, 159, 64, 1)',
            'backgroundColor': 'rgba(255, 159, 64, 0.2)',
            'tension': 0.4
        }]
    }

    return {
        'success': True,
        'tipo_analisis': 'ejecucion',
        'titulo': f'Análisis de Ejecución por Trimestre - {periodo}',
        'descripcion': f'Seguimiento detallado basado en {len(datos)} indicadores',
        'tendencias': ejecucion_data,
        'presupuesto': None,
        'indicadores': [],
        'metricas': {
            'ejecucion_fisica_promedio': round(sum(promedios_fisicos) / len(promedios_fisicos), 2) if promedios_fisicos else 0,
            'cumplimiento_promedio': round(sum(promedios_financieros) / len(promedios_financieros), 2) if promedios_financieros else 0,
            'variacion_trimestral': 2.5,  # Podría calcularse dinámicamente
            'proyectos_activos': len(set(d.get('cod_proyecto') for d in datos if d.get('cod_proyecto')))
        }
    }


def generar_analisis_presupuesto_real(datos_plan, periodo, tipo_grafico):
    """Genera datos para análisis presupuestario usando datos reales"""
    datos = datos_plan['datos']

    if not datos:
        return generar_analisis_presupuesto_fallback(datos_plan, periodo, tipo_grafico)

    # Agrupar presupuesto por línea estratégica
    presupuesto_por_linea = {}
    for dato in datos:
        linea = dato.get('nombre_linea', 'Sin clasificación')
        presupuesto = dato.get('presupuesto_ejecutado_acumulado', 0)
        if linea not in presupuesto_por_linea:
            presupuesto_por_linea[linea] = 0
        presupuesto_por_linea[linea] += presupuesto

    presupuesto_data = {
        'labels': list(presupuesto_por_linea.keys()),
        'datasets': [{
            'label': f'Presupuesto Ejecutado {periodo} (Millones)',
            'data': list(presupuesto_por_linea.values()),
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
        'tipo_analisis': 'presupuesto',
        'titulo': f'Análisis Presupuestario - {periodo}',
        'descripcion': f'Distribución presupuestaria por línea estratégica',
        'tendencias': None,
        'presupuesto': presupuesto_data,
        'indicadores': [],
        'metricas': {
            'presupuesto_total_ejecutado': sum(presupuesto_por_linea.values()),
            'lineas_con_presupuesto': len([v for v in presupuesto_por_linea.values() if v > 0]),
            'linea_mayor_ejecucion': max(presupuesto_por_linea.keys(), key=lambda k: presupuesto_por_linea[k]) if presupuesto_por_linea else 'N/A'
        }
    }


def generar_analisis_indicadores_real(datos_plan, periodo, tipo_grafico):
    """Genera datos para análisis de indicadores usando datos reales"""
    datos = datos_plan['datos']

    if not datos:
        return generar_analisis_indicadores_fallback(datos_plan, periodo, tipo_grafico)

    # Crear datos para diferentes tipos de gráficos según el tipo_grafico
    if tipo_grafico == 'scatter':
        # Gráfico de dispersión: avance vs presupuesto
        scatter_data = {
            'datasets': [{
                'label': 'Indicadores',
                'data': [{
                    'x': d.get('avance_porcentual', 0),
                    'y': d.get('presupuesto_ejecutado_acumulado', 0),
                    'nombre': d.get('nombre_indicador', ''),
                    'linea': d.get('nombre_linea', '')
                } for d in datos],
                'backgroundColor': 'rgba(54, 162, 235, 0.6)',
                'borderColor': 'rgba(54, 162, 235, 1)'
            }]
        }
    elif tipo_grafico == 'pastel':
        # Distribución por estado de avance
        estados = {'excelente': 0, 'bueno': 0, 'regular': 0, 'critico': 0}
        for d in datos:
            avance = d.get('avance_porcentual', 0)
            if avance >= 90:
                estados['excelente'] += 1
            elif avance >= 75:
                estados['bueno'] += 1
            elif avance >= 50:
                estados['regular'] += 1
            else:
                estados['critico'] += 1

        scatter_data = {
            'labels': list(estados.keys()),
            'datasets': [{
                'data': list(estados.values()),
                'backgroundColor': [
                    'rgba(40, 167, 69, 0.8)',   # verde - excelente
                    'rgba(23, 162, 184, 0.8)',  # azul - bueno
                    'rgba(255, 193, 7, 0.8)',   # amarillo - regular
                    'rgba(220, 53, 69, 0.8)'    # rojo - critico
                ]
            }]
        }
    else:
        # Gráfico de barras por defecto
        scatter_data = {
            'labels': [d.get('nombre_indicador', f'Indicador {i+1}') for i, d in enumerate(datos[:10])],
            'datasets': [{
                'label': 'Avance (%)',
                'data': [d.get('avance_porcentual', 0) for d in datos[:10]],
                'backgroundColor': 'rgba(54, 162, 235, 0.8)'
            }]
        }

    return {
        'success': True,
        'tipo_analisis': 'indicadores',
        'titulo': f'Análisis de Indicadores - {periodo}',
        'descripcion': f'Análisis detallado de {len(datos)} indicadores',
        'tendencias': scatter_data,
        'presupuesto': None,
        'indicadores': [],
        'metricas': {
            'total_indicadores': len(datos),
            'avance_promedio': sum(d.get('avance_porcentual', 0) for d in datos) / len(datos) if datos else 0,
            'indicadores_completados': sum(1 for d in datos if d.get('avance_porcentual', 0) >= 100)
        }
    }


def generar_analisis_comparativo_real(datos_plan, periodo, tipo_grafico):
    """Genera datos para análisis comparativo usando datos reales"""
    datos = datos_plan['datos']

    if not datos:
        return generar_analisis_comparativo_fallback(datos_plan, periodo, tipo_grafico)

    # Comparar diferentes líneas estratégicas
    comparativo_data = {}
    for dato in datos:
        linea = dato.get('nombre_linea', 'Sin línea')
        if linea not in comparativo_data:
            comparativo_data[linea] = {
                'avance_promedio': [],
                'presupuesto_total': 0,
                'indicadores_count': 0
            }

        comparativo_data[linea]['avance_promedio'].append(dato.get('avance_porcentual', 0))
        comparativo_data[linea]['presupuesto_total'] += dato.get('presupuesto_ejecutado_acumulado', 0)
        comparativo_data[linea]['indicadores_count'] += 1

    # Calcular promedios
    labels = []
    avances = []
    presupuestos = []

    for linea, data in comparativo_data.items():
        labels.append(linea)
        avances.append(sum(data['avance_promedio']) / len(data['avance_promedio']) if data['avance_promedio'] else 0)
        presupuestos.append(data['presupuesto_total'])

    comparativo_chart = {
        'labels': labels,
        'datasets': [{
            'label': 'Avance Promedio (%)',
            'data': avances,
            'borderColor': 'rgba(54, 162, 235, 1)',
            'backgroundColor': 'rgba(54, 162, 235, 0.1)',
            'tension': 0.4
        }]
    }

    return {
        'success': True,
        'tipo_analisis': 'comparativo',
        'titulo': f'Análisis Comparativo - {periodo}',
        'descripcion': f'Comparación entre líneas estratégicas',
        'tendencias': comparativo_chart,
        'presupuesto': None,
        'indicadores': [],
        'metricas': {
            'lineas_analizadas': len(labels),
            'mejor_linea': labels[avances.index(max(avances))] if avances else 'N/A',
            'diferencia_maxima': max(avances) - min(avances) if avances else 0
        }
    }


def generar_analisis_tendencias_real(datos_plan, periodo, tipo_grafico):
    """Genera datos para análisis de tendencias usando datos reales"""
    datos = datos_plan['datos']

    if not datos:
        return generar_analisis_tendencias_fallback(datos_plan, periodo, tipo_grafico)

    # Analizar tendencias de avance por trimestre
    tendencias_trimestrales = []
    for trimestre in range(1, 5):
        avances_trimestre = [d.get(f'cumplimiento_q{trimestre}', 0) for d in datos]
        promedio_trimestre = sum(avances_trimestre) / len(avances_trimestre) if avances_trimestre else 0
        tendencias_trimestrales.append(promedio_trimestre)

    # Proyectar tendencia futura
    if len(tendencias_trimestrales) >= 2:
        # Calcular pendiente de la tendencia
        pendiente = (tendencias_trimestrales[-1] - tendencias_trimestrales[0]) / (len(tendencias_trimestrales) - 1)
        proyeccion_q5 = tendencias_trimestrales[-1] + pendiente
        proyeccion_q6 = proyeccion_q5 + pendiente
    else:
        proyeccion_q5 = tendencias_trimestrales[-1] if tendencias_trimestrales else 0
        proyeccion_q6 = proyeccion_q5

    tendencias_completas = {
        'labels': ['Q1', 'Q2', 'Q3', 'Q4', 'Proy Q5', 'Proy Q6'],
        'datasets': [{
            'label': 'Tendencia Real',
            'data': tendencias_trimestrales + [proyeccion_q5, proyeccion_q6],
            'borderColor': 'rgba(54, 162, 235, 1)',
            'backgroundColor': 'rgba(54, 162, 235, 0.1)',
            'tension': 0.4
        }, {
            'label': 'Meta Ideal',
            'data': [25, 50, 75, 100, 100, 100],
            'borderColor': 'rgba(75, 192, 192, 1)',
            'backgroundColor': 'rgba(75, 192, 192, 0.1)',
            'borderDash': [5, 5],
            'tension': 0.4,
            'fill': False
        }]
    }

    return {
        'success': True,
        'tipo_analisis': 'tendencias',
        'titulo': f'Análisis de Tendencias - {periodo}',
        'descripcion': f'Proyección de tendencias basada en datos reales',
        'tendencias': tendencias_completas,
        'presupuesto': None,
        'indicadores': [],
        'metricas': {
            'tendencia_actual': 'creciente' if tendencias_trimestrales[-1] > tendencias_trimestrales[0] else 'decreciente',
            'proyeccion_q6': round(proyeccion_q6, 2),
            'velocidad_mejora': round((tendencias_trimestrales[-1] - tendencias_trimestrales[0]) / len(tendencias_trimestrales), 2) if tendencias_trimestrales else 0
        }
    }


# Funciones de respaldo (fallback) para cuando no hay datos reales
def generar_analisis_ejecucion_fallback(datos_plan, periodo, tipo_grafico):
    return generar_analisis_ejecucion(None, periodo, tipo_grafico)

def generar_analisis_presupuesto_fallback(datos_plan, periodo, tipo_grafico):
    return generar_analisis_presupuesto(None, periodo, tipo_grafico)

def generar_analisis_indicadores_fallback(datos_plan, periodo, tipo_grafico):
    return generar_analisis_indicadores(None, periodo, tipo_grafico)

def generar_analisis_comparativo_fallback(datos_plan, periodo, tipo_grafico):
    return generar_analisis_comparativo(None, periodo, tipo_grafico)

def generar_analisis_tendencias_fallback(datos_plan, periodo, tipo_grafico):
    return generar_analisis_tendencias(None, periodo, tipo_grafico)


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


@planes_bp.route('/<int:plan_id>/reportes/columnas')
@login_required
def reportes_columnas(plan_id):
    """API para obtener información sobre columnas disponibles para BI"""
    plan = get_plan_or_redirect(plan_id, current_user)
    if hasattr(plan, 'status_code'):
        return plan

    # Columnas disponibles con metadatos para BI
    columnas_disponibles = [
        {
            'id': 'id_indicador',
            'nombre': 'ID Indicador',
            'tipo': 'entero',
            'descripcion': 'Identificador único del indicador',
            'categoria': 'identificador',
            'graficos_apropiados': ['barras', 'lineas']
        },
        {
            'id': 'cod_indicador',
            'nombre': 'Código Indicador',
            'tipo': 'texto',
            'descripcion': 'Código del indicador de producto',
            'categoria': 'identificador',
            'graficos_apropiados': ['barras', 'pastel']
        },
        {
            'id': 'nombre_indicador',
            'nombre': 'Nombre Indicador',
            'tipo': 'texto',
            'descripcion': 'Nombre completo del indicador',
            'categoria': 'descriptivo',
            'graficos_apropiados': ['barras', 'pastel']
        },
        {
            'id': 'tipo_indicador',
            'nombre': 'Tipo Indicador',
            'tipo': 'texto',
            'descripcion': 'Tipo de indicador (proceso, resultado, impacto)',
            'categoria': 'clasificacion',
            'graficos_apropiados': ['pastel', 'barras']
        },
        {
            'id': 'linea_base',
            'nombre': 'Línea Base',
            'tipo': 'numerico',
            'descripcion': 'Valor inicial o línea base del indicador',
            'categoria': 'metrica',
            'graficos_apropiados': ['lineas', 'barras', 'scatter']
        },
        {
            'id': 'meta_cuatrienio',
            'nombre': 'Meta Cuatrienio',
            'tipo': 'numerico',
            'descripcion': 'Meta total para el período 2024-2027',
            'categoria': 'metrica',
            'graficos_apropiados': ['barras', 'lineas', 'area']
        },
        {
            'id': 'meta_2024',
            'nombre': 'Meta 2024',
            'tipo': 'numerico',
            'descripcion': 'Meta específica para el año 2024',
            'categoria': 'metrica',
            'graficos_apropiados': ['barras', 'lineas', 'area']
        },
        {
            'id': 'unidad',
            'nombre': 'Unidad',
            'tipo': 'texto',
            'descripcion': 'Unidad de medida del indicador',
            'categoria': 'metrica',
            'graficos_apropiados': ['barras', 'pastel']
        },
        {
            'id': 'cod_linea',
            'nombre': 'Código Línea',
            'tipo': 'entero',
            'descripcion': 'Código de la línea estratégica',
            'categoria': 'jerarquia',
            'graficos_apropiados': ['barras', 'pastel']
        },
        {
            'id': 'nombre_linea',
            'nombre': 'Nombre Línea Estratégica',
            'tipo': 'texto',
            'descripcion': 'Nombre de la línea estratégica',
            'categoria': 'jerarquia',
            'graficos_apropiados': ['barras', 'pastel', 'treemap']
        },
        {
            'id': 'cod_componente',
            'nombre': 'Código Componente',
            'tipo': 'texto',
            'descripcion': 'Código del componente',
            'categoria': 'jerarquia',
            'graficos_apropiados': ['barras', 'pastel']
        },
        {
            'id': 'nombre_componente',
            'nombre': 'Nombre Componente',
            'tipo': 'texto',
            'descripcion': 'Nombre del componente',
            'categoria': 'jerarquia',
            'graficos_apropiados': ['barras', 'pastel', 'treemap']
        },
        {
            'id': 'cod_programa',
            'nombre': 'Código Programa',
            'tipo': 'texto',
            'descripcion': 'Código del programa',
            'categoria': 'jerarquia',
            'graficos_apropiados': ['barras', 'pastel']
        },
        {
            'id': 'nombre_programa',
            'nombre': 'Nombre Programa',
            'tipo': 'texto',
            'descripcion': 'Nombre del programa',
            'categoria': 'jerarquia',
            'graficos_apropiados': ['barras', 'pastel', 'treemap']
        },
        {
            'id': 'cod_proyecto',
            'nombre': 'Código Proyecto',
            'tipo': 'texto',
            'descripcion': 'Código del proyecto',
            'categoria': 'jerarquia',
            'graficos_apropiados': ['barras', 'pastel']
        },
        {
            'id': 'nombre_proyecto',
            'nombre': 'Nombre Proyecto',
            'tipo': 'texto',
            'descripcion': 'Nombre del proyecto',
            'categoria': 'jerarquia',
            'graficos_apropiados': ['barras', 'pastel', 'treemap']
        }
    ]

    # Agregar columnas de ejecución trimestral
    for trimestre in range(1, 5):
        columnas_disponibles.extend([
            {
                'id': f'ejecucion_q{trimestre}',
                'nombre': f'Ejecución Q{trimestre}',
                'tipo': 'numerico',
                'descripcion': f'Ejecución física del {trimestre} trimestre',
                'categoria': 'ejecucion',
                'graficos_apropiados': ['lineas', 'barras', 'area', 'scatter']
            },
            {
                'id': f'cumplimiento_q{trimestre}',
                'nombre': f'Cumplimiento Q{trimestre} (%)',
                'tipo': 'porcentaje',
                'descripcion': f'Porcentaje de cumplimiento del {trimestre} trimestre',
                'categoria': 'ejecucion',
                'graficos_apropiados': ['lineas', 'barras', 'area', 'heatmap']
            },
            {
                'id': f'presupuesto_ejecutado_q{trimestre}',
                'nombre': f'Presupuesto Q{trimestre}',
                'tipo': 'monetario',
                'descripcion': f'Presupuesto ejecutado en el {trimestre} trimestre',
                'categoria': 'presupuesto',
                'graficos_apropiados': ['barras', 'lineas', 'area', 'pastel']
            },
            {
                'id': f'poblacion_impactada_q{trimestre}',
                'nombre': f'Población Q{trimestre}',
                'tipo': 'entero',
                'descripcion': f'Población impactada en el {trimestre} trimestre',
                'categoria': 'impacto',
                'graficos_apropiados': ['barras', 'lineas', 'area', 'mapa']
            }
        ])

    # Agregar columnas acumuladas
    columnas_disponibles.extend([
        {
            'id': 'ejecucion_acumulada',
            'nombre': 'Ejecución Acumulada',
            'tipo': 'numerico',
            'descripcion': 'Ejecución física acumulada hasta la fecha',
            'categoria': 'ejecucion',
            'graficos_apropiados': ['lineas', 'barras', 'area', 'scatter']
        },
        {
            'id': 'cumplimiento_acumulado',
            'nombre': 'Cumplimiento Acumulado (%)',
            'tipo': 'porcentaje',
            'descripcion': 'Porcentaje de cumplimiento acumulado',
            'categoria': 'ejecucion',
            'graficos_apropiados': ['lineas', 'barras', 'area', 'heatmap']
        },
        {
            'id': 'presupuesto_ejecutado_acumulado',
            'nombre': 'Presupuesto Acumulado',
            'tipo': 'monetario',
            'descripcion': 'Presupuesto ejecutado acumulado',
            'categoria': 'presupuesto',
            'graficos_apropiados': ['barras', 'lineas', 'area', 'pastel']
        },
        {
            'id': 'poblacion_impactada_acumulada',
            'nombre': 'Población Acumulada',
            'tipo': 'entero',
            'descripcion': 'Población impactada acumulada',
            'categoria': 'impacto',
            'graficos_apropiados': ['barras', 'lineas', 'area', 'mapa']
        },
        {
            'id': 'avance_porcentual',
            'nombre': 'Avance (%)',
            'tipo': 'porcentaje',
            'descripcion': 'Porcentaje de avance general del indicador',
            'categoria': 'metrica',
            'graficos_apropiados': ['barras', 'lineas', 'scatter', 'heatmap', 'boxplot']
        },
        {
            'id': 'estado',
            'nombre': 'Estado',
            'tipo': 'texto',
            'descripcion': 'Estado actual del indicador',
            'categoria': 'clasificacion',
            'graficos_apropiados': ['pastel', 'barras', 'treemap']
        }
    ])

    # Agrupar por categorías para facilitar la selección
    categorias = {}
    for col in columnas_disponibles:
        categoria = col['categoria']
        if categoria not in categorias:
            categorias[categoria] = []
        categorias[categoria].append(col)

    return {
        'success': True,
        'plan_id': plan_id,
        'plan_titulo': plan.titulo,
        'columnas_disponibles': columnas_disponibles,
        'categorias': categorias,
        'total_columnas': len(columnas_disponibles),
        'tipos_graficos_disponibles': [
            'barras', 'lineas', 'area', 'pastel', 'scatter',
            'heatmap', 'boxplot', 'treemap', 'radar', 'correlacion'
        ]
    }


@planes_bp.route('/<int:plan_id>/reportes/bi-data')
@login_required
def reportes_bi_data(plan_id):
    """API específica para Business Intelligence - devuelve datos crudos para análisis avanzado"""
    plan = get_plan_or_redirect(plan_id, current_user)
    if hasattr(plan, 'status_code'):
        return plan

    # Obtener parámetros de BI
    columnas_solicitadas = request.args.get('columnas', '').split(',') if request.args.get('columnas') else None
    formato = request.args.get('formato', 'json')  # json, csv, excel
    filtros = request.args.get('filtros', '')  # filtros en formato JSON

    try:
        # Obtener datos del plan
        datos_plan = obtener_datos_plan_completo(plan, '2024', columnas_solicitadas)

        # Aplicar filtros si existen
        if filtros:
            import json
            filtros_dict = json.loads(filtros)
            datos_plan['datos'] = aplicar_filtros_bi(datos_plan['datos'], filtros_dict)

        # Preparar respuesta según formato solicitado
        if formato == 'csv':
            return generar_respuesta_csv(datos_plan)
        elif formato == 'excel':
            return generar_respuesta_excel(datos_plan)
        else:
            # Formato JSON por defecto
            return {
                'success': True,
                'tipo': 'bi_data',
                'plan_id': plan_id,
                'plan_titulo': plan.titulo,
                'datos': datos_plan['datos'],
                'columnas': datos_plan['columnas'],
                'total_registros': len(datos_plan['datos']),
                'metadata': {
                    'fecha_generacion': datetime.utcnow().isoformat(),
                    'usuario': current_user.username,
                    'columnas_solicitadas': columnas_solicitadas,
                    'filtros_aplicados': filtros
                }
            }

    except Exception as e:
        current_app.logger.error(f'Error en reportes_bi_data: {str(e)}')
        return {
            'success': False,
            'error': str(e),
            'tipo': 'bi_data_error'
        }


def aplicar_filtros_bi(datos, filtros):
    """Aplica filtros avanzados a los datos de BI"""
    datos_filtrados = datos

    for filtro in filtros.get('filtros', []):
        campo = filtro.get('campo')
        operador = filtro.get('operador', 'equals')
        valor = filtro.get('valor')

        if not campo or campo not in datos[0] if datos else False:
            continue

        if operador == 'equals':
            datos_filtrados = [d for d in datos_filtrados if str(d.get(campo, '')).lower() == str(valor).lower()]
        elif operador == 'contains':
            datos_filtrados = [d for d in datos_filtrados if valor.lower() in str(d.get(campo, '')).lower()]
        elif operador == 'greater_than':
            datos_filtrados = [d for d in datos_filtrados if float(d.get(campo, 0)) > float(valor)]
        elif operador == 'less_than':
            datos_filtrados = [d for d in datos_filtrados if float(d.get(campo, 0)) < float(valor)]
        elif operador == 'between':
            min_val, max_val = valor
            datos_filtrados = [d for d in datos_filtrados if float(min_val) <= float(d.get(campo, 0)) <= float(max_val)]

    return datos_filtrados


def generar_respuesta_csv(datos_plan):
    """Genera respuesta en formato CSV"""
    import io
    from flask import Response

    output = io.StringIO()
    if datos_plan['datos']:
        import csv

        # Escribir encabezados
        fieldnames = datos_plan['columnas']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        # Escribir datos
        for fila in datos_plan['datos']:
            writer.writerow(fila)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=bi_data_{datos_plan["plan_titulo"].replace(" ", "_")}.csv'}
    )


def generar_respuesta_excel(datos_plan):
    """Genera respuesta en formato Excel"""
    try:
        from openpyxl import Workbook
        from flask import Response
        import io

        wb = Workbook()
        ws = wb.active
        ws.title = "BI Data"

        # Escribir encabezados
        if datos_plan['datos']:
            headers = datos_plan['columnas']
            for col_num, header in enumerate(headers, 1):
                ws.cell(row=1, column=col_num, value=header)

            # Escribir datos
            for row_num, fila in enumerate(datos_plan['datos'], 2):
                for col_num, header in enumerate(headers, 1):
                    ws.cell(row=row_num, column=col_num, value=fila.get(header, ''))

        # Preparar respuesta
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename=bi_data_{datos_plan["plan_titulo"].replace(" ", "_")}.xlsx'}
        )
    except ImportError:
        return {
            'success': False,
            'error': 'Biblioteca openpyxl no disponible para exportación Excel'
        }
