from models import Usuario, Proyecto, Actividad, db
from werkzeug.security import generate_password_hash
from flask import session
from datetime import datetime


def agregar_usuario(nombre, email):
    """
    Agrega un nuevo usuario a la base de datos.
    """
    usuario = Usuario(nombre=nombre, email=email)
    db.session.add(usuario)
    db.session.commit()


def crear_proyecto(descripcion, encargado, id_departamento, fecha_inicio, fecha_fin):
    """
    Crea un nuevo proyecto en la base de datos.
    
    Args:
        descripcion (str): Nombre o descripción del proyecto.
        encargado (int): ID del usuario encargado del proyecto.
        id_departamento (int): ID del departamento al que pertenece el proyecto.
        fecha_inicio (str): Fecha de inicio del proyecto (formato 'YYYY-MM-DD').
        fecha_fin (str): Fecha de finalización del proyecto (formato 'YYYY-MM-DD').
        
    Returns:
        dict: Resultado de la operación.
    """
    try:
        nuevo_proyecto = Proyecto(
            descripcion=descripcion,
            encargado=encargado,
            id_departamento=id_departamento,
            fecha_inicio=datetime.strptime(fecha_inicio, '%Y-%m-%d').date(),
            fecha_fin=datetime.strptime(fecha_fin, '%Y-%m-%d').date(),
            estado='en progreso'
        )
        
        db.session.add(nuevo_proyecto)
        db.session.commit()
        
        return {"success": "Proyecto creado exitosamente."}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error al crear el proyecto: {str(e)}"}


def obtener_proyectos_usuario():
    """
    Obtiene los proyectos creados o asignados al usuario en sesión.
    
    Returns:
        list: Lista de proyectos.
    """
    if 'user_id' not in session:
        return {"error": "Usuario no autenticado."}
    
    proyectos = Proyecto.query.filter(
        (Proyecto.encargado == session['user_id']) | 
        (Proyecto.id_departamento == session['id_departamento'])
    ).all()
    
    return [p for p in proyectos]


def agregar_actividad(id_proyecto, descripcion, id_usuario, fecha_inicio_planificada, fecha_fin_planificada, fecha_inicio_real=None, fecha_fin_real=None):
    """
    Crea una nueva actividad dentro de un proyecto.
    
    Args:
        id_proyecto (int): ID del proyecto al que pertenece la actividad.
        descripcion (str): Descripción de la actividad.
        id_usuario (int): ID del usuario asignado a la actividad.
        fecha_inicio_planificada (str): Fecha de inicio planificada (formato 'YYYY-MM-DD').
        fecha_fin_planificada (str): Fecha de finalización planificada (formato 'YYYY-MM-DD').
        fecha_inicio_real (str, optional): Fecha de inicio real (formato 'YYYY-MM-DD').
        fecha_fin_real (str, optional): Fecha de finalización real (formato 'YYYY-MM-DD').
        
    Returns:
        dict: Resultado de la operación.
    """
    try:
        nueva_actividad = Actividad(
            descripcion=descripcion,
            id_proyecto=id_proyecto,
            id_usuario=id_usuario,
            fecha_inicio_planificada=datetime.strptime(fecha_inicio_planificada, '%Y-%m-%d').date(),
            fecha_fin_planificada=datetime.strptime(fecha_fin_planificada, '%Y-%m-%d').date(),
            fecha_inicio_real=datetime.strptime(fecha_inicio_real, '%Y-%m-%d').date() if fecha_inicio_real else None,
            fecha_fin_real=datetime.strptime(fecha_fin_real, '%Y-%m-%d').date() if fecha_fin_real else None,
            estado='pendiente'
        )
        
        db.session.add(nueva_actividad)
        db.session.commit()
        
        return {"success": "Actividad agregada correctamente."}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error al agregar la actividad: {str(e)}"}


def obtener_actividades_proyecto(id_proyecto):
    """
    Obtiene todas las actividades de un proyecto.
    
    Args:
        id_proyecto (int): ID del proyecto.
        
    Returns:
        list: Lista de actividades.
    """
    actividades = Actividad.query.filter_by(id_proyecto=id_proyecto).all()
    return [a for a in actividades]


def actualizar_actividad(id_actividad, fecha_inicio_real=None, fecha_fin_real=None, estado=None):
    """
    Actualiza los datos de una actividad.
    
    Args:
        id_actividad (int): ID de la actividad.
        fecha_inicio_real (str, optional): Fecha de inicio real (formato 'YYYY-MM-DD').
        fecha_fin_real (str, optional): Fecha de finalización real (formato 'YYYY-MM-DD').
        estado (str, optional): Estado de la actividad (pendiente, en progreso, finalizada).
        
    Returns:
        dict: Resultado de la operación.
    """
    try:
        actividad = Actividad.query.get_or_404(id_actividad)
        
        if fecha_inicio_real:
            actividad.fecha_inicio_real = datetime.strptime(fecha_inicio_real, '%Y-%m-%d').date()
        if fecha_fin_real:
            actividad.fecha_fin_real = datetime.strptime(fecha_fin_real, '%Y-%m-%d').date()
        if estado:
            actividad.estado = estado
        
        db.session.commit()
        return {"success": "Actividad actualizada correctamente."}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error al actualizar la actividad: {str(e)}"}


def calcular_porcentaje_avance(actividad):
    hoy = datetime.now().date()  # Fecha actual
    inicio_planificado = actividad.fecha_inicio_planificada
    fin_planificado = actividad.fecha_fin_planificada
    inicio_real = actividad.fecha_inicio_real
    fin_real = actividad.fecha_fin_real

    # Si la actividad no ha comenzado
    if not inicio_real:
        return 0, "No iniciada"

    # Si la actividad está completada
    if fin_real:
        if fin_real <= fin_planificado:
            return 100, "Completada a tiempo"
        else:
            return 100, "Completada con retraso"

    # Si la actividad está en progreso
    dias_totales = (fin_planificado - inicio_planificado).days
    dias_transcurridos = (hoy - inicio_real).days

    if dias_totales <= 0:  # Evitar división por cero
        return 0, "Error en fechas"

    porcentaje = (dias_transcurridos / dias_totales) * 100
    return min(porcentaje, 100), "En progreso"


def crear_usuario(username, password, email, id_departamento, status):
    """
    Crea un nuevo usuario en la base de datos con contraseña hasheada.
    
    Args:
        username (str): Nombre de usuario único.
        password (str): Contraseña en texto plano (será hasheada).
        email (str): Correo electrónico del usuario.
        id_departamento (int): ID del departamento al que pertenece el usuario.
        status (str): Estado del usuario (activo, inactivo, etc.).
        
    Returns:
        dict: Resultado de la operación.
    """
    # Verificar si el usuario o email ya existen
    if Usuario.query.filter_by(username=username).first():
        return {"error": "El nombre de usuario ya existe."}

    if Usuario.query.filter_by(email=email).first():
        return {"error": "El correo ya está registrado."}
    
    # Hashear la contraseña
    password_hasheada = generate_password_hash(password, method='pbkdf2:sha256')
    
    # Crear el nuevo usuario
    nuevo_usuario = Usuario(
        username=username,
        password=password_hasheada,
        email=email,
        id_departamento=id_departamento,
        status=status
    )
    
    # Guardar en la base de datos
    db.session.add(nuevo_usuario)
    db.session.commit()
    
    return {"success": f"Usuario {username} creado correctamente."}

