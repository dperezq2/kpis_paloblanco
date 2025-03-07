from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash
import plotly.express as px
import pandas as pd
import random
from database import init_db, db
from models import Proyecto, Actividad, Usuario, ActividadInicioReal, ActividadDuracionReal, ActividadInicio, ActividadDuracion, ActividadInicioReal, ActividadDuracionReal, Dia
from utils import registrar_inicio_actividad, registrar_duracion_actividad, registrar_inicio_real, registrar_duracion_real, crear_proyecto, agregar_actividad
from datetime import datetime

app = Flask(__name__)
init_db(app)
app.secret_key = 'mysecretkey'  # Cambia esto por una clave segura en producción

# Datos predefinidos de departamentos y usuarios
departments = ["Ventas", "Marketing", "Desarrollo"]
users = {
    "Ventas": ["Usuario_V1", "Usuario_V2", "Usuario_V3"],
    "Marketing": ["Usuario_M1", "Usuario_M2", "Usuario_M3"],
    "Desarrollo": ["Usuario_D1", "Usuario_D2", "Usuario_D3"]
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



#Ruta para logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# PROYECTOS

#Ruta para mostrar los proyectos
@app.route('/mis_proyectos')
def mis_proyectos():
    """
    Muestra los proyectos asociados al usuario en sesión.
    """
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    proyectos = Proyecto.query.filter(
        (Proyecto.encargado == session['user_name']) | 
        (Proyecto.id_departamento == session['id_departamento'])
    ).all()

    return render_template('mis_proyectos.html', proyectos=proyectos)

# Ruta para ver detalles de un proyecto
from sqlalchemy.orm import aliased

@app.route('/proyecto/<int:id>')
def detalle_proyecto(id):
    """
    Muestra las actividades del proyecto seleccionado con sus detalles.
    """
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    proyecto = Proyecto.query.get_or_404(id)

    # Crear alias para la tabla 'dia' para evitar conflictos
    dia_inicio = aliased(Dia)
    dia_real = aliased(Dia)

    actividades = db.session.query(
        Actividad.id,
        Actividad.descripcion,
        dia_inicio.dia.label("inicio_planificado"),
        dia_inicio.id_mes.label("mes_inicio_planificado"),
        ActividadDuracion.valor.label("duracion_planificada"),
        ActividadInicioReal.valor.label("inicio_real"),
        dia_real.dia.label("inicio_real_dia"),
        dia_real.id_mes.label("mes_inicio_real"),
        ActividadDuracionReal.valor.label("duracion_real")
    ).join(ActividadInicio, ActividadInicio.id_actividad == Actividad.id, isouter=True) \
     .join(dia_inicio, dia_inicio.id == ActividadInicio.valor, isouter=True) \
     .join(ActividadDuracion, ActividadDuracion.id_actividad == Actividad.id, isouter=True) \
     .join(ActividadInicioReal, ActividadInicioReal.id_actividad == Actividad.id, isouter=True) \
     .join(dia_real, dia_real.id == ActividadInicioReal.valor, isouter=True) \
     .join(ActividadDuracionReal, ActividadDuracionReal.id_actividad == Actividad.id, isouter=True) \
     .filter(Actividad.id_proyecto == id).all()

    return render_template('detalle_proyecto.html', proyecto=proyecto, actividades=actividades)





# Ruta para guardar la duración real de una actividad
@app.route('/finalizar_actividad/<int:id>', methods=['POST'])
def finalizar_actividad(id):
    """
    Marca una actividad como finalizada y guarda la duración real.
    """
    if not session.get('logged_in'):
        return jsonify({"error": "No autorizado"}), 403

    actividad = Actividad.query.get_or_404(id)
    data = request.get_json()
    
    if not data or 'fecha_fin_real' not in data:
        return jsonify({"error": "Fecha de finalización requerida"}), 400

    fecha_fin_real = datetime.strptime(data['fecha_fin_real'], '%Y-%m-%d')
    fecha_inicio_real = actividad.inicio_real if actividad.inicio_real else datetime.utcnow()

    duracion_real = (fecha_fin_real - fecha_inicio_real).days

    nueva_duracion = ActividadDuracionReal(
        id_actividad=id,
        anio=fecha_fin_real.year,
        valor=duracion_real,
        id_usuario=session['user_id']
    )
    
    db.session.add(nueva_duracion)
    db.session.commit()

    return jsonify({"success": "Actividad finalizada correctamente."})



@app.route('/finalizar_actividades', methods=['POST'])
def finalizar_actividades():
    """
    Marca actividades como finalizadas y guarda la fecha de finalización en actividad_duracion_real.
    """
    if not session.get('logged_in'):
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    actividades = data.get("actividades", [])

    if not actividades:
        return jsonify({"error": "No se seleccionaron actividades."}), 400

    for actividad in actividades:
        actividad_id = actividad["id"]
        fecha_fin = actividad["fecha_fin"]

        if not fecha_fin:
            continue  # No guardar si no hay fecha seleccionada

        # Buscar la actividad
        actividad_obj = Actividad.query.get(actividad_id)
        if actividad_obj:
            # Guardar en actividad_duracion_real
            nueva_duracion = ActividadDuracionReal(
                id_actividad=actividad_id,
                anio=int(fecha_fin[:4]),  # Extraer el año de la fecha
                valor=int(fecha_fin[-2:]),  # Extraer el día
                id_usuario=session['user_id']
            )

            db.session.add(nueva_duracion)

    db.session.commit()
    return jsonify({"success": "Actividades finalizadas correctamente."})


# Ruta para agregar proyecto
@app.route('/agregar_proyecto', methods=['GET', 'POST'])
def agregar_proyecto():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        descripcion = request.form.get('descripcion')
        encargado = request.form.get('encargado', session.get('user_name'))
        id_departamento = session.get('id_departamento')
        frecuencia = request.form.get('frecuencia')
        mes_inicio = request.form.get('mes_inicio')
        anio = request.form.get('anio', datetime.now().year)

        # Crear proyecto usando la función de utils
        resultado = crear_proyecto(descripcion, encargado, id_departamento)
        
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
                
                # Agregar actividad usando la función de utils
                resultado_actividad = agregar_actividad(
                    id_proyecto=nuevo_proyecto.id,
                    descripcion=descripcion_actividad,
                    id_usuario=session.get('user_id')
                )
                
                if 'error' in resultado_actividad:
                    flash(resultado_actividad['error'], "warning")
                    index += 1
                    continue
                
                # Obtener la actividad recién creada
                nueva_actividad = Actividad.query.filter_by(
                    descripcion=descripcion_actividad,
                    id_proyecto=nuevo_proyecto.id
                ).order_by(Actividad.id.desc()).first()
                
                # Registrar planificación
                inicio_planificado = request.form.get(f"actividad_{index}_inicio_planificado")
                if inicio_planificado:
                    # Convertir la fecha a día y mes
                    fecha_inicio = datetime.strptime(inicio_planificado, '%Y-%m-%d')
                    registrar_inicio_actividad(
                        id_actividad=nueva_actividad.id,
                        anio=fecha_inicio.year,
                        mes=fecha_inicio.month,
                        dia=fecha_inicio.day,
                        id_usuario=session.get('user_id')
                    )
                
                duracion_planificada = request.form.get(f"actividad_{index}_duracion_planificada")
                if duracion_planificada:
                    registrar_duracion_actividad(
                        id_actividad=nueva_actividad.id,
                        anio=anio,
                        valor=int(duracion_planificada),
                        id_usuario=session.get('user_id')
                    )
                
                # Si se proporcionan datos reales
                inicio_real = request.form.get(f"actividad_{index}_inicio_real")
                if inicio_real:
                    # Convertir la fecha a día y mes
                    fecha_real = datetime.strptime(inicio_real, '%Y-%m-%d')
                    registrar_inicio_real(
                        id_actividad=nueva_actividad.id,
                        anio=fecha_real.year,
                        mes=fecha_real.month,
                        dia=fecha_real.day,
                        id_usuario=session.get('user_id')
                    )
                
                duracion_real = request.form.get(f"actividad_{index}_duracion_real")
                if duracion_real:
                    registrar_duracion_real(
                        id_actividad=nueva_actividad.id,
                        anio=anio,
                        valor=int(duracion_real),
                        id_usuario=session.get('user_id')
                    )
                
                index += 1

            flash("Proyecto y actividades guardados correctamente.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Error al crear el proyecto.", "danger")
            
    return render_template("agregar_proyecto.html", 
                          user_name=session.get('user_name'), 
                          user_email=session.get('user_email'),
                          user_departamento=session.get('user_departamento'),
                          current_year=datetime.now().year)

# Ruta para dashboard
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    selected_dept = request.args.get('department')
    selected_user = request.args.get('user')
    
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
    if selected_user:
        kpi_fig = px.bar(
            filtered_kpi_df,
            x="kpi_name",
            y="kpi_value",
            title=f'KPIs de {selected_user}',
            labels={"kpi_value": "Valor KPI", "kpi_name": "KPI"}
        )
        
        # Crear gráfico de progreso
        progress_fig = px.pie(
            filtered_kpi_df,
            names="kpi_name",
            values="kpi_value",
            title=f'Progreso de KPIs de {selected_user}'
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
        
        # Gráfico de progreso general por departamento
        progress_fig = px.pie(
            agg_kpi_df,
            names="user",
            values="kpi_value",
            title=f'Progreso de KPIs {f"en {selected_dept}" if selected_dept else ""}'
        )
    
    # Gráfico de Gantt
    gantt_fig = px.timeline(
        filtered_activity_df,
        x_start="start_date",
        x_end="end_date",
        y="activity",
        color="user",
        title=f'Actividades {f"en {selected_dept}" if selected_dept else ""} {f"de {selected_user}" if selected_user else ""}',
        labels={"activity": "Actividad", "user": "Usuario"}
    )
    gantt_fig.update_yaxes(categoryorder="total ascending")  # Ordenar las actividades
    gantt_html = gantt_fig.to_html(full_html=False)
    
    # Convertir los gráficos a HTML
    kpi_graph_html = kpi_fig.to_html(full_html=False)
    progress_graph_html = progress_fig.to_html(full_html=False)
    
    return render_template(
        'dashboard.html',
        kpi_graph_html=kpi_graph_html,
        gantt_graph_html=gantt_html,
        progress_graph_html=progress_graph_html,
        departments=departments,
        selected_dept=selected_dept,
        users=users,
        selected_user=selected_user
        
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
