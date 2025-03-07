from models import ActividadInicio, ActividadDuracion, ActividadInicioReal, ActividadDuracionReal, Usuario, Proyecto, Actividad, db
from werkzeug.security import generate_password_hash
from flask import session


def agregar_usuario(nombre, email):
    usuario = Usuario(nombre=nombre, email=email)
    db.session.add(usuario)
    db.session.commit()

def crear_proyecto(descripcion, encargado, id_departamento):
    """
    Crea un nuevo proyecto en la base de datos.
    
    Args:
        descripcion (str): Nombre o descripción del proyecto
        encargado (str): Nombre del encargado del proyecto
        id_departamento (int): ID del departamento al que pertenece el proyecto
        frecuencia (str, optional): Frecuencia del proyecto (Mensual, Bimestral, etc.)
        mes_inicio (str, optional): Mes de inicio del proyecto
        
    Returns:
        dict: Resultado de la operación
    """
    try:
        nuevo_proyecto = Proyecto(
            descripcion=descripcion,
            encargado=encargado,
            id_departamento=id_departamento
        )
        
        db.session.add(nuevo_proyecto)
        db.session.commit()
        
        return {"success": "Proyecto creado exitosamente"}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error al crear el proyecto: {str(e)}"}


def obtener_proyectos_usuario():
    """Obtiene los proyectos creados o asignados al usuario en sesión."""
    if 'user_id' not in session:
        return {"error": "Usuario no autenticado."}
    
    proyectos = Proyecto.query.filter((Proyecto.encargado == session['username']) | 
                                    (Proyecto.id_departamento == session['id_departamento'])).all()
    
    return [p.descripcion for p in proyectos]

def agregar_actividad(id_proyecto, descripcion, id_usuario):
    """Crea una actividad dentro de un proyecto."""
    nueva_actividad = Actividad(
        descripcion=descripcion,
        id_proyecto=id_proyecto,
        id_usuario=id_usuario
    )
    db.session.add(nueva_actividad)
    db.session.commit()
    return {"success": "Actividad agregada correctamente."}


def obtener_actividades_proyecto(id_proyecto):
    """Obtiene todas las actividades de un proyecto."""
    actividades = Actividad.query.filter_by(id_proyecto=id_proyecto).all()
    return [{"id": a.id, "descripcion": a.descripcion} for a in actividades]


def registrar_inicio_actividad(id_actividad, anio, mes, dia, id_usuario):
    """
    Registra el inicio planificado de una actividad.
    
    Args:
        id_actividad (int): ID de la actividad
        anio (int): Año de inicio planificado
        mes (int): Mes de inicio planificado
        dia (int): Día de inicio planificado
        id_usuario (int): ID del usuario que registra el inicio
    """
    try:
        # Convertir la fecha a un valor único (por ejemplo, días desde el inicio del año)
        valor = (mes - 1) * 31 + dia  # Ejemplo simple, ajustar según necesidades
        
        inicio = ActividadInicio(
            id_actividad=id_actividad,
            anio=anio,
            valor=valor,
            id_usuario=id_usuario
        )
        
        db.session.add(inicio)
        db.session.commit()
        return {"success": "Inicio planificado registrado."}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error al registrar el inicio planificado: {str(e)}"}


def registrar_duracion_actividad(id_actividad, anio, valor, id_usuario):
    """Registra la duración planificada de una actividad."""
    duracion = ActividadDuracion(id_actividad=id_actividad, anio=anio, valor=valor, id_usuario=id_usuario)
    db.session.add(duracion)
    db.session.commit()
    return {"success": "Duración planificada registrada."}


def registrar_inicio_real(id_actividad, anio, mes, dia, id_usuario):
    """
    Registra el inicio real de una actividad.
    
    Args:
        id_actividad (int): ID de la actividad
        anio (int): Año de inicio real
        mes (int): Mes de inicio real
        dia (int): Día de inicio real
        id_usuario (int): ID del usuario que registra el inicio
    """
    try:
        # Convertir la fecha a un valor único (por ejemplo, días desde el inicio del año)
        valor = (mes - 1) * 31 + dia  # Ejemplo simple, ajustar según necesidades
        
        inicio_real = ActividadInicioReal(
            id_actividad=id_actividad,
            anio=anio,
            valor=valor,
            id_usuario=id_usuario
        )
        
        db.session.add(inicio_real)
        db.session.commit()
        return {"success": "Inicio real registrado."}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error al registrar el inicio real: {str(e)}"}


def registrar_duracion_real(id_actividad, anio, valor, id_usuario):
    """Registra la duración real de una actividad cuando se finaliza."""
    duracion_real = ActividadDuracionReal(id_actividad=id_actividad, anio=anio, valor=valor, id_usuario=id_usuario)
    db.session.add(duracion_real)
    db.session.commit()
    return {"success": "Duración real registrada."}

def crear_usuario(username, password, email, id_departamento, status):
    """
    Crea un nuevo usuario en la base de datos con contraseña hasheada.
    
    Args:
        username: Nombre de usuario único
        password: Contraseña en texto plano (será hasheada)
        email: Correo electrónico del usuario
        id_departamento: ID del departamento al que pertenece el usuario
        status: Estado del usuario (activo, inactivo, etc.)
        
    Returns:
        Diccionario con el resultado de la operación.
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
        status = status
    )
    
    # Guardar en la base de datos
    db.session.add(nuevo_usuario)
    db.session.commit()
    
    return {"success": f"Usuario {username} creado correctamente."}

