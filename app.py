from flask import Flask, render_template, request, redirect, url_for, flash, session
import plotly.express as px
import pandas as pd
import random

app = Flask(__name__)
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
    "email": "admin@ejemplo.com"
}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == USER_CREDENTIALS["username"] and password == USER_CREDENTIALS["password"]:
            session['logged_in'] = True
            session['user_name'] = USER_CREDENTIALS["name"]
            session['user_email'] = USER_CREDENTIALS["email"]
            return redirect(url_for('dashboard'))
        else:
            flash("Credenciales incorrectas. Intenta de nuevo.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

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
        selected_user=selected_user,
        user_name=session.get('user_name'),
        user_email=session.get('user_email')
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)
