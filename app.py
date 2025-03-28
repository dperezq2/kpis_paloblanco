from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash
import plotly.express as px
import pandas as pd
import random
from database import init_db, db
from models import Proyecto, Actividad, Usuario, Departamento
from utils import crear_proyecto, agregar_actividad, actualizar_actividad, obtener_proyectos_usuario, obtener_actividades_proyecto, calcular_porcentaje_avance, crear_kpi, obtener_kpis_usuario, obtener_detalle_kpi, agregar_avance_kpi, agregar_categoria_inicial
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
import calendar
import os

app = Flask(__name__)

# Cargar variables de entorno
load_dotenv()
init_db(app)

app.secret_key = os.getenv('FLASK_SECRET_KEY')  # Cambia esto por una clave segura en producción

# Datos predefinidos de departamentos y usuarios
departments = ["Sistemas", "RR. HH.", "Costos"]
users = {
    "Sistemas": ["Usuario_V1", "Usuario_V2", "Usuario_V3"],
    "RR. HH.": ["Usuario_M1", "Usuario_M2", "Usuario_M3"],
    "Costos": ["Usuario_D1", "Usuario_D2", "Usuario_D3"]
}

# Lista de posibles KPIs (cada usuario podrá crear KPIs a su gusto; aquí simulamos algunos)
kpi_names = ["Eficiencia", "Productividad", "Calidad", "Satisfacción"]

# Generar datos aleatorios para KPIs
kpi_data = []
for dept in departments:
    for user in users[dept]:
        # Cada usuario tiene entre 1 y 4 KPIs definidos
        cantidad_kpis = random.randint(1, len(kpi_names))
        kpis_seleccionados = random.sample(kpi_names, cantidad_kpis)
        for kpi in kpis_seleccionados:
            kpi_data.append({
                "department": dept,
                "user": user,
                "kpi_name": kpi,
                "kpi_value": random.randint(50, 150)
            })

# Generar datos de actividades con fechas de inicio y fin
activity_data = []
for dept in departments:
    for user in users[dept]:
        num_activities = random.randint(1, 5)  # Cada usuario tiene entre 1 y 5 actividades
        for i in range(num_activities):
            start_date = pd.Timestamp.today() + pd.Timedelta(days=random.randint(0, 30))
            end_date = start_date + pd.Timedelta(days=random.randint(1, 10))
            activity_data.append({
                "department": dept,
                "user": user,
                "activity": f"Actividad {i + 1}",
                "start_date": start_date,
                "end_date": end_date
            })

# Convertir los datos de KPIs y actividades a DataFrame
kpi_df = pd.DataFrame(kpi_data)
activity_df = pd.DataFrame(activity_data)

# Credenciales de prueba para login
USER_CREDENTIALS = {
    "username": "admin",
    "password": "admin123",
    "name": "Administrador",
    "email": "admin@ejemplo.com",
    "id": 1
}

# Ruta de inicio
@app.route('/')
def home():
    return redirect(url_for('login'))

# Ruta para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Maneja el proceso de inicio de sesión verificando las credenciales contra la base de datos.
    """
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Buscar el usuario en la base de datos y unir con departamento
        usuario = Usuario.query.filter_by(username=username).first()
        
        if usuario and check_password_hash(usuario.password, password):
            session['logged_in'] = True
            session['user_id'] = usuario.id
            session['user_name'] = usuario.username
            session['user_email'] = usuario.email
            session['id_departamento'] = usuario.id_departamento
            session['user_departamento'] = usuario.departamento.descripcion if usuario.departamento else "Sin departamento"
            flash("Inicio de sesión exitoso.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Credenciales incorrectas. Intenta de nuevo.", "danger")
    
    return render_template('login.html')

# Ruta para logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# PROYECTOS

# Ruta para mostrar los proyectos
@app.route('/mis_proyectos')
def mis_proyectos():
    """
    Muestra los proyectos asociados al usuario en sesión.
    """
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    proyectos = obtener_proyectos_usuario()
    return render_template('mis_proyectos.html', proyectos=proyectos)


# Ruta para ver detalles de un proyecto
@app.route('/proyecto/<int:id>')
def detalle_proyecto(id):
    """
    Muestra las actividades del proyecto seleccionado con sus detalles.
    """
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    proyecto = Proyecto.query.get_or_404(id)
    actividades = obtener_actividades_proyecto(id)

    # Obtener el nombre del encargado
    encargado = Usuario.query.get(proyecto.encargado)
    proyecto.encargado = encargado.username if encargado else "Sin encargado"

    return render_template('detalle_proyecto.html', proyecto=proyecto, actividades=actividades)


@app.route('/actualizar_fecha_actividad', methods=['POST'])
def actualizar_fecha_actividad():
    if not session.get('logged_in'):
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()

    if not data or 'actividad_id' not in data:
        return jsonify({"error": "ID de actividad requerido"}), 400

    actividad = Actividad.query.get_or_404(data['actividad_id'])

    # Validación: No se puede asignar fecha de finalización sin fecha de inicio real
    if 'fecha_fin_real' in data and data['fecha_fin_real']:
        if not actividad.fecha_inicio_real:
            return jsonify({"error": "No puedes asignar una fecha de finalización sin una fecha de inicio real."}), 400
        actividad.fecha_fin_real = datetime.strptime(data['fecha_fin_real'], '%Y-%m-%d').date()

    # Actualizar fecha de inicio real
    if 'fecha_inicio_real' in data and data['fecha_inicio_real']:
        actividad.fecha_inicio_real = datetime.strptime(data['fecha_inicio_real'], '%Y-%m-%d').date()

    try:
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


    

# Ruta para finalizar una actividad
@app.route('/finalizar_actividades', methods=['POST'])
def finalizar_actividades():
    if not session.get('logged_in'):
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    actividades = data.get('actividades', [])

    if not actividades:
        return jsonify({"error": "No se recibieron actividades para finalizar."}), 400

    try:
        for actividad_data in actividades:
            actividad = Actividad.query.get(actividad_data['actividad_id'])

            # Validación: No se puede finalizar sin fechas reales
            if not actividad.fecha_inicio_real or not actividad.fecha_fin_real:
                return jsonify({"error": f"No puedes finalizar la actividad {actividad.id} sin ambas fechas reales."}), 400

            actividad.estado = "finalizada"

        db.session.commit()
        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Ruta para agregar proyecto
@app.route('/agregar_proyecto', methods=['GET', 'POST'])
def agregar_proyecto():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        descripcion = request.form.get('descripcion')
        encargado = session.get('user_id')  # El usuario en sesión es el encargado
        id_departamento = session.get('id_departamento')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')

        # Crear proyecto usando la función de utils
        resultado = crear_proyecto(descripcion, encargado, id_departamento, fecha_inicio, fecha_fin)
        
        if 'error' in resultado:
            flash(resultado['error'], "danger")
            return redirect(url_for('agregar_proyecto'))
        
        # Obtener el ID del proyecto recién creado
        nuevo_proyecto = Proyecto.query.filter_by(descripcion=descripcion, encargado=encargado).order_by(Proyecto.id.desc()).first()
        
        if nuevo_proyecto:
            # Guardar actividades
            index = 0
            while f"actividad_{index}_descripcion" in request.form:
                descripcion_actividad = request.form.get(f"actividad_{index}_descripcion")
                fecha_inicio_planificada = request.form.get(f"actividad_{index}_fecha_inicio_planificada")
                fecha_fin_planificada = request.form.get(f"actividad_{index}_fecha_fin_planificada")
                fecha_inicio_real = request.form.get(f"actividad_{index}_fecha_inicio_real")
                fecha_fin_real = request.form.get(f"actividad_{index}_fecha_fin_real")

                # Agregar actividad usando la función de utils
                resultado_actividad = agregar_actividad(
                    id_proyecto=nuevo_proyecto.id,
                    descripcion=descripcion_actividad,
                    id_usuario=session.get('user_id'),
                    fecha_inicio_planificada=fecha_inicio_planificada,
                    fecha_fin_planificada=fecha_fin_planificada,
                    fecha_inicio_real=fecha_inicio_real,
                    fecha_fin_real=fecha_fin_real
                )
                
                if 'error' in resultado_actividad:
                    flash(resultado_actividad['error'], "warning")
                    index += 1
                    continue
                
                index += 1

            flash("Proyecto y actividades guardados correctamente.", "success")
            return redirect(url_for('mis_proyectos'))
        else:
            flash("Error al crear el proyecto.", "danger")
            
    return render_template("agregar_proyecto.html", 
                        user_name=session.get('user_name'), 
                        user_email=session.get('user_email'),
                        user_departamento=session.get('user_departamento'),
                        current_year=datetime.now().year)

# Ruta para agregar actividades a un proyecto
@app.route('/agregar_actividades/<int:id_proyecto>', methods=['GET', 'POST'])
def agregar_actividades(id_proyecto):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Verificar si es una solicitud JSON (desde fetch) o un formulario tradicional
        if request.is_json:
            # Obtener datos del JSON enviado por fetch
            datos = request.get_json()
            descripcion = datos.get('descripcion')
            id_usuario = session.get('user_id')
            fecha_inicio_planificada = datos.get('fecha_inicio_planificada')
            fecha_fin_planificada = datos.get('fecha_fin_planificada')
        else:
            # Mantener compatibilidad con formularios HTML tradicionales
            descripcion = request.form.get('descripcion')
            id_usuario = session.get('user_id')
            fecha_inicio_planificada = request.form.get('fecha_inicio_planificada')
            fecha_fin_planificada = request.form.get('fecha_fin_planificada')

        # Agregar actividad usando la función de utils
        resultado = agregar_actividad(
            id_proyecto=id_proyecto,
            descripcion=descripcion,
            id_usuario=id_usuario,
            fecha_inicio_planificada=fecha_inicio_planificada,
            fecha_fin_planificada=fecha_fin_planificada
        )
        
        if 'error' in resultado:
            if request.is_json:
                return jsonify({'success': False, 'error': resultado['error']})
            flash(resultado['error'], "danger")
            return redirect(url_for('agregar_actividades', id_proyecto=id_proyecto))
        
        if request.is_json:
            return jsonify({'success': True})
        
        flash("Actividad agregada correctamente.", "success")
        return redirect(url_for('detalle_proyecto', id=id_proyecto))

    return render_template('agregar_actividad.html', proyecto_id=id_proyecto)


# ------------------------------> KPIS <------------------------------
# Ruta para agregar KPI
@app.route('/agregar_kpi', methods=['GET', 'POST'])
def agregar_kpi():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        meta_porcentaje = request.form.get('meta_porcentaje')
        total_unidades = request.form.get('total_unidades')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        id_usuario = session.get('user_id')

        # Procesar fincas (opcional)
        fincas = []
        index = 0
        while f"ubicacion_{index}" in request.form:
            ubicacion = request.form.get(f"ubicacion_{index}")
            cantidad = request.form.get(f"cantidad_{index}")
            if ubicacion and cantidad:
                fincas.append({"ubicacion": ubicacion, "cantidad": int(cantidad)})
            index += 1

        resultado = crear_kpi(titulo, descripcion, meta_porcentaje, total_unidades, fecha_inicio, fecha_fin, id_usuario, fincas)
        
        if 'error' in resultado:
            flash(resultado['error'], "danger")
            return redirect(url_for('agregar_kpi'))
        
        flash("KPI creado exitosamente.", "success")
        return redirect(url_for('mis_kpis'))

    return render_template("agregar_kpi.html", 
                        user_name=session.get('user_name'), 
                        user_email=session.get('user_email'),
                        user_departamento=session.get('user_departamento'),
                        current_year=datetime.now().year)

# Ruta para mostrar los KPIs
@app.route('/mis_kpis')
def mis_kpis():
    """
    Muestra los KPIs asociados al usuario en sesión.
    """
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    kpis = obtener_kpis_usuario()
    if isinstance(kpis, dict) and 'error' in kpis:
        flash(kpis['error'], "danger")
        return redirect(url_for('login'))
    
    return render_template('mis_kpis.html', kpis=kpis)

# Ruta para mostrar y actualizar detalles del KPI
@app.route('/detalle_kpi/<int:id>', methods=['GET', 'POST'])
def detalle_kpi(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    kpi = obtener_detalle_kpi(id)
    if isinstance(kpi, dict) and 'error' in kpi:
        flash(kpi['error'], "danger")
        return redirect(url_for('mis_kpis'))
    
    if request.method == 'POST' and 'fecha_avance' in request.form:  # Para avances
        fecha_avance = request.form.get('fecha_avance')
        ubicacion = request.form.get('ubicacion')
        cantidad_avance = request.form.get('cantidad_avance')
        comentario = request.form.get('comentario') or None
        
        resultado = agregar_avance_kpi(id, fecha_avance, ubicacion, cantidad_avance, comentario)
        if 'error' in resultado:
            flash(resultado['error'], "danger")
        else:
            flash(resultado['success'], "success")
        return redirect(url_for('detalle_kpi', id=id))
    
    return render_template('detalle_kpi.html', kpi=kpi)

# Agregar categorías en el detalle kpi
@app.route('/agregar_categoria_kpi/<int:id>', methods=['POST'])
def agregar_categoria_kpi(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    kpi = obtener_detalle_kpi(id)
    if isinstance(kpi, dict) and 'error' in kpi:
        flash(kpi['error'], "danger")
        return redirect(url_for('mis_kpis'))
    
    nueva_categoria = request.form.get('nueva_categoria')
    cantidad_categoria = request.form.get('cantidad_categoria')
    
    resultado = agregar_categoria_inicial(id, nueva_categoria, cantidad_categoria)
    if 'error' in resultado:
        flash(resultado['error'], "danger")
    else:
        flash(resultado['success'], "success")
    
    return redirect(url_for('detalle_kpi', id=id))

# Ruta para dashboard
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Obtener parámetros de la URL
    selected_dept = request.args.get('department')
    selected_user = request.args.get('user')
    selected_proyecto = request.args.get('proyecto')
    selected_estado = request.args.get('estado')
    selected_month = request.args.get('month')  # Filtro de mes (1-12)
    selected_year = request.args.get('year')    # Nuevo: filtro de año
    active_tab = request.args.get('active_tab', 'kpis')

    # Obtener todos los proyectos para el filtro
    proyectos = Proyecto.query.filter_by(encargado=session['user_id']).all()

    # Filtrar los datos de KPIs y actividades
    filtered_kpi_df = kpi_df.copy()
    filtered_activity_df = activity_df.copy()
    
    if selected_dept:
        filtered_kpi_df = filtered_kpi_df[filtered_kpi_df['department'] == selected_dept]
        filtered_activity_df = filtered_activity_df[filtered_activity_df['department'] == selected_dept]
    
    if selected_user:
        filtered_kpi_df = filtered_kpi_df[filtered_kpi_df['user'] == selected_user]
        filtered_activity_df = filtered_activity_df[filtered_activity_df['user'] == selected_user]

    # Gráfico de KPIs
    if not filtered_kpi_df.empty:
        if selected_user:
            kpi_fig = px.bar(
                filtered_kpi_df,
                x="kpi_name",
                y="kpi_value",
                title=f'KPIs de {selected_user}',
                labels={"kpi_value": "Valor KPI", "kpi_name": "KPI"}
            )
        else:
            agg_kpi_df = filtered_kpi_df.groupby(["user", "kpi_name"])["kpi_value"].mean().reset_index()
            kpi_fig = px.bar(
                agg_kpi_df,
                x="user",
                y="kpi_value",
                color="kpi_name",
                barmode="group",
                title=f'KPIs por Usuario {f"en {selected_dept}" if selected_dept else ""}',
                labels={"kpi_value": "Valor KPI", "user": "Usuario"}
            )
        # Mejorar responsividad del gráfico KPI
        kpi_fig.update_layout(
            autosize=True,
            margin=dict(l=20, r=20, b=40, t=40, pad=4),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
        )
        kpi_graph_html = kpi_fig.to_html(full_html=False, config={'responsive': True})
    else:
        kpi_graph_html = "<p>No hay datos de KPIs para mostrar.</p>"

    # Gráfico de Gantt para proyectos
    # Obtener los proyectos donde el usuario de la sesión es encargado
    proyectos_usuario = Proyecto.query.filter_by(encargado=session['user_id']).all()
    proyectos_ids = [proyecto.id for proyecto in proyectos_usuario]

    # Iniciar la consulta base para el Gantt
    if selected_proyecto and int(selected_proyecto) in proyectos_ids:
        # Si hay un proyecto seleccionado y pertenece al usuario
        query = Actividad.query.filter_by(id_proyecto=selected_proyecto)
        proyecto_descripcion = Proyecto.query.get(selected_proyecto).descripcion
    else:
        # Mostrar actividades de todos los proyectos del usuario
        query = Actividad.query.filter(Actividad.id_proyecto.in_(proyectos_ids))
        proyecto_descripcion = "mis proyectos"

    # Continuar con el resto del filtrado (estado, etc.)
    if selected_estado:
        if selected_estado == "COMPLETADA":
            query = query.filter_by(estado="finalizada")
        elif selected_estado == "PENDIENTE":
            query = query.filter(Actividad.estado != "finalizada")

    # Ordenar actividades
    actividades = query.order_by(Actividad.id.desc()).all()

    # Generar datos para el gráfico de Gantt
    gantt_data = []
    
    for actividad in actividades:
        # Convertir objetos datetime directamente a cadenas de texto formateadas
        inicio_planificado = actividad.fecha_inicio_planificada.strftime("%Y-%m-%d") if actividad.fecha_inicio_planificada else ""
        fin_planificado = actividad.fecha_fin_planificada.strftime("%Y-%m-%d") if actividad.fecha_fin_planificada else ""
        inicio_real = actividad.fecha_inicio_real.strftime("%Y-%m-%d") if actividad.fecha_inicio_real else ""
        fin_real = actividad.fecha_fin_real.strftime("%Y-%m-%d") if actividad.fecha_fin_real else ""
        
        porcentaje, estado = calcular_porcentaje_avance(actividad)
        
        gantt_data.append({
            "Actividad": actividad.descripcion,
            "Inicio": inicio_planificado,
            "Fin": fin_planificado, 
            "InicioTexto": inicio_planificado,  # Duplicado para tooltip
            "FinTexto": fin_planificado,        # Duplicado para tooltip
            "InicioReal": inicio_real,
            "FinReal": fin_real,
            "Responsable": actividad.usuario.username,
            "Porcentaje": porcentaje,
            "Estado": estado
        })

    if gantt_data:
        # Definir colores personalizados
        color_discrete_map = {
            "Completada a tiempo": "green",
            "Completada con retraso": "red",
            "En progreso": "blue",
            "No iniciada": "gray",
            "Error en fechas": "black"
        }
        
        # Convertir a DataFrame
        df_gantt = pd.DataFrame(gantt_data)
        
        # Convertir las columnas de fecha a objetos datetime para el gráfico
        for col in ["Inicio", "Fin"]:
            df_gantt[col] = pd.to_datetime(df_gantt[col], errors='coerce')
        
        # Crear el gráfico de Gantt
        gantt_fig = px.timeline(
            df_gantt,
            x_start="Inicio",
            x_end="Fin",
            y="Actividad",
            color="Estado",
            color_discrete_map=color_discrete_map,
            title=f'Diagrama de Gantt para {proyecto_descripcion}',
            labels={"Actividad": "Actividad", "Responsable": "Responsable"},
            custom_data=["InicioTexto", "FinTexto", "InicioReal", "FinReal", "Responsable", "Estado", "Porcentaje"]
        )

        # Personalizar el tooltip
        gantt_fig.update_traces(
            hovertemplate=(
                "<b>Actividad:</b> %{y}<br>" +
                "<b>Inicio Planificado:</b> %{customdata[0]}<br>" +
                "<b>Fin Planificado:</b> %{customdata[1]}<br>" +
                "<b>Inicio Real:</b> %{customdata[2]}<br>" +
                "<b>Fin Real:</b> %{customdata[3]}<br>" +
                "<b>Responsable:</b> %{customdata[4]}<br>" +
                "<b>Estado:</b> %{customdata[5]}<br>" +
                "<b>Porcentaje:</b> %{customdata[6]}%"
            )
        )

        # Ajustar el diseño del gráfico para mejor responsividad
        gantt_fig.update_yaxes(categoryorder="total ascending")
        gantt_fig.update_xaxes(
            type='date',
            tickformat="%Y-%m-%d",
            dtick="M1",
            tickangle=45,
            tickfont=dict(size=10)
        )
        gantt_fig.update_traces(
            marker=dict(line=dict(width=0.5)),
            selector=dict(type='bar')
        )
        gantt_fig.update_layout(
            autosize=True,
            height=625,
            margin=dict(l=20, r=20, b=80, t=60, pad=4),
            title={
                'text': f'Diagrama de Gantt para {proyecto_descripcion}',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=16)
            },
            legend=dict(
                title="Estado",
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            )
        )
        gantt_html = gantt_fig.to_html(full_html=False, config={'responsive': True})
    else:
        gantt_html = "<p>No hay actividades para mostrar.</p>"

    # NUEVA SECCIÓN: Preparar datos para la Curva S
    # Obtener los proyectos donde el usuario de la sesión es encargado
    proyectos_usuario = Proyecto.query.filter_by(encargado=session['user_id']).all()
    proyectos_ids = [proyecto.id for proyecto in proyectos_usuario]

    # Iniciar la consulta base para la Curva S
    all_activities = Actividad.query

    # Si hay proyecto seleccionado para la curva S, verificar que pertenezca al usuario
    if selected_proyecto and int(selected_proyecto) in proyectos_ids:
        all_activities = all_activities.filter_by(id_proyecto=selected_proyecto)
        proyecto_descripcion = Proyecto.query.get(selected_proyecto).descripcion
    else:
        # Mostrar la curva S de todos los proyectos del usuario
        all_activities = all_activities.filter(Actividad.id_proyecto.in_(proyectos_ids))
        proyecto_descripcion = "Mis Proyectos"

    all_activities = all_activities.all()
    
    # Obtener la fecha más temprana y más tardía para establecer el rango de la curva S
    start_dates = [act.fecha_inicio_planificada for act in all_activities if act.fecha_inicio_planificada]
    end_dates = [act.fecha_fin_planificada for act in all_activities if act.fecha_fin_planificada]
    real_end_dates = [act.fecha_fin_real for act in all_activities if act.fecha_fin_real]
    
    all_dates = start_dates + end_dates + real_end_dates
    
    if all_dates:
        min_date = min(all_dates)
        max_date = max(all_dates)
        
        # Crear un rango de fechas mensuales desde el inicio al fin
        current_date = datetime(min_date.year, min_date.month, 1)
        end_date = datetime(max_date.year, max_date.month, 1) + timedelta(days=32)
        end_date = datetime(end_date.year, end_date.month, 1)  # Primer día del mes siguiente
        
        # Lista de fechas mensuales para el filtro
        fecha_meses = []
        current = current_date
        while current <= end_date:
            fecha_meses.append(current)
            # Avanzar al próximo mes
            if current.month == 12:
                current = datetime(current.year + 1, 1, 1)
            else:
                current = datetime(current.year, current.month + 1, 1)
        
        # Crear DataFrame para la Curva S
        curve_s_data = []
        
        # Para cada mes, calcular acumulados
        for i, fecha in enumerate(fecha_meses):
            # Obtener el último día del mes
            if fecha.month == 12:
                ultimo_dia = datetime(fecha.year, fecha.month, 31)
            else:
                ultimo_dia = datetime(fecha.year, fecha.month + 1, 1) - timedelta(days=1)
            
            # Convertir ultimo_dia a datetime.date para comparar con las fechas de las actividades
            ultimo_dia = ultimo_dia.date()

            # Contar actividades planificadas hasta este mes
            actividades_planificadas = sum(
                1 for act in all_activities
                if act.fecha_fin_planificada and act.fecha_fin_planificada <= ultimo_dia
            )
            
            # Contar actividades completadas hasta este mes
            actividades_completadas = sum(
                1 for act in all_activities
                if act.fecha_fin_real and act.fecha_fin_real <= ultimo_dia and act.estado == "finalizada"
            )
            
            # Nombrar el mes para la visualización
            nombre_mes = f"{calendar.month_name[fecha.month]} {fecha.year}"
            
            curve_s_data.append({
                "fecha": fecha,
                "fecha_str": fecha.strftime("%Y-%m"),
                "mes": nombre_mes,
                "actividades_planificadas": actividades_planificadas,
                "actividades_completadas": actividades_completadas
            })
        
        df_curve_s = pd.DataFrame(curve_s_data)
        
        # Crear gráfico de Curva S
        if not df_curve_s.empty:
            curves_fig = px.line(
                df_curve_s, 
                x="mes", 
                y=["actividades_planificadas", "actividades_completadas"],
                title=f"Curva S de Proyecto: {proyecto_descripcion}",
                labels={
                    "mes": "Mes",
                    "value": "Actividades acumuladas",
                    "variable": "Tipo"
                },
                color_discrete_map={
                    "actividades_planificadas": "blue",
                    "actividades_completadas": "green"
                }
            )
            
            # Mejorar legibilidad y responsividad
            curves_fig.update_layout(
                autosize=True,
                xaxis_title="Mes",
                yaxis_title="Actividades acumuladas",
                legend_title="Tipo",
                hovermode="x unified",
                margin=dict(l=20, r=20, b=80, t=60, pad=4),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.3,
                    xanchor="center",
                    x=0.5
                )
            )
            
            # Actualizar nombres de la leyenda
            curves_fig.for_each_trace(lambda t: t.update(
                name="Planificadas" if t.name == "actividades_planificadas" else "Completadas"
            ))
            
            # Actualizar diseño para mejor legibilidad
            curves_fig.update_xaxes(tickangle=45, tickfont=dict(size=10))
            
            curve_s_html = curves_fig.to_html(full_html=False, config={'responsive': True})
        else:
            curve_s_html = "<p>No hay datos suficientes para generar la Curva S.</p>"

        # Gráfico circular (pie chart) para tareas acumuladas y completadas
        total_planificadas = len([act for act in all_activities if act.fecha_fin_planificada])
        total_completadas = len([act for act in all_activities if act.estado == "finalizada"])
        
        pie_data = {
            "Tipo": ["Planificadas", "Completadas"],
            "Cantidad": [total_planificadas, total_completadas]
        }
        df_pie = pd.DataFrame(pie_data)
        
        pie_fig = px.pie(
            df_pie,
            names="Tipo",
            values="Cantidad",
            title=f"Progreso de Tareas - {proyecto_descripcion}",
            color_discrete_sequence=["blue", "green"]
        )
        
        pie_fig.update_layout(
            autosize=True,
            margin=dict(l=20, r=20, b=80, t=60, pad=4),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            )
        )
        
        pie_html = pie_fig.to_html(full_html=False, config={'responsive': True})
    else:
        fecha_meses = []
        curve_s_html = "<p>No hay actividades con fechas definidas para generar la Curva S.</p>"
        pie_html = "<p>No hay datos para generar el gráfico circular.</p>"

    return render_template(
        'dashboard.html',
        kpi_graph_html=kpi_graph_html,
        gantt_graph_html=gantt_html,
        curve_s_html=curve_s_html,
        pie_html=pie_html,
        departments=departments,
        selected_dept=selected_dept,
        users=users,
        selected_user=selected_user,
        proyectos=proyectos,
        selected_proyecto=selected_proyecto,
        active_tab=active_tab,
        estado=selected_estado,
        proyecto_descripcion=proyecto_descripcion
    )


@app.context_processor
def inject_user_data():
    return {
        'user_name': session.get('user_name'),
        'user_email': session.get('user_email'),
        'user_departamento': session.get('user_departamento')
    }
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)