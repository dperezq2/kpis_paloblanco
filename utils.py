from models import Usuario, Proyecto, Actividad, KPI, AvanceKPI, db
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
    Obtiene los proyectos creados por el usuario en sesión.
    """
    if 'user_id' not in session:
        return {"error": "Usuario no autenticado."}
    
    proyectos = Proyecto.query.filter_by(encargado=session['user_id']).all()
    
    return proyectos



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





# -----------------> KPIS <----------------------
# Crear el KPI
def crear_kpi(titulo, descripcion, meta_porcentaje, total_unidades, fecha_inicio, fecha_fin, id_usuario, fincas=None):
    """
    Crea un nuevo KPI en la base de datos y opcionalmente sus avances iniciales por finca.
    
    Args:
        titulo (str): Título del KPI.
        descripcion (str): Descripción del KPI.
        meta_porcentaje (float): Meta en porcentaje (ej: 95.0).
        total_unidades (int): Total de unidades objetivo (ej: 400).
        fecha_inicio (str): Fecha de inicio del KPI (formato 'YYYY-MM-DD').
        fecha_fin (str): Fecha de finalización del KPI (formato 'YYYY-MM-DD').
        id_usuario (int): ID del usuario responsable del KPI.
        fincas (list, optional): Lista de dicts con {'ubicacion': str, 'cantidad': int}.
        
    Returns:
        dict: Resultado de la operación.
    """
    try:
        nuevo_kpi = KPI(
            titulo=titulo,
            descripcion=descripcion,
            meta_porcentaje=float(meta_porcentaje),
            total_unidades=int(total_unidades),
            fecha_inicio=datetime.strptime(fecha_inicio, '%Y-%m-%d').date(),
            fecha_fin=datetime.strptime(fecha_fin, '%Y-%m-%d').date(),
            id_usuario=id_usuario,
            estado='en progreso',
            create_time=datetime.utcnow()
        )
        
        db.session.add(nuevo_kpi)
        db.session.flush()  # Obtener el ID del KPI antes de commit

        # Si hay fincas, registrarlas como avances iniciales
        if fincas:
            total_fincas = sum(finca['cantidad'] for finca in fincas)
            if total_fincas > nuevo_kpi.total_unidades:
                raise ValueError("La suma de unidades por finca excede el total de unidades.")
            
            for finca in fincas:
                if finca['ubicacion'] and finca['cantidad']:
                    avance = AvanceKPI(
                        id_kpi=nuevo_kpi.id,
                        fecha_avance=nuevo_kpi.fecha_inicio,  # Fecha inicial como referencia
                        ubicacion=finca['ubicacion'],
                        cantidad_avance=finca['cantidad'],
                        comentario="Asignación inicial",
                        create_time=datetime.utcnow()
                    )
                    db.session.add(avance)

        db.session.commit()
        return {"success": "KPI creado exitosamente.", "kpi_id": nuevo_kpi.id}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error al crear el KPI: {str(e)}"}

# Obtener los KPIs
def obtener_kpis_usuario():
    """
    Obtiene los KPIs creados por el usuario en sesión.
    
    Returns:
        list: Lista de objetos KPI o dict con error si no está autenticado.
    """
    if 'user_id' not in session:
        return {"error": "Usuario no autenticado."}
    
    kpis = KPI.query.filter_by(id_usuario=session['user_id']).all()
    
    return kpis

# Obtener detalles del KPI
def obtener_detalle_kpi(id_kpi):
    """
    Obtiene los detalles de un KPI específico y sus avances, si el usuario tiene permiso.
    
    Args:
        id_kpi (int): ID del KPI a consultar.
    
    Returns:
        KPI: Objeto KPI o dict con error si no se encuentra o no tiene permiso.
    """
    if 'user_id' not in session:
        return {"error": "Usuario no autenticado."}
    
    kpi = KPI.query.filter_by(id=id_kpi, id_usuario=session['user_id']).first()
    if not kpi:
        return {"error": "KPI no encontrado o no tienes permiso para verlo."}
    
    return kpi

# Agregar avances al KPI
def agregar_avance_kpi(id_kpi, fecha_avance, ubicacion, cantidad_avance, comentario=None):
    try:
        kpi = KPI.query.get(id_kpi)
        if not kpi:
            return {"error": "KPI no encontrado."}

        # Validar si el KPI ya está completado
        if kpi.estado == "completado":
            return {"error": "No puedes agregar avances a un KPI que ya está completado."}

        asignaciones = {a.ubicacion: a.cantidad_avance for a in kpi.avances if a.comentario == "Asignación inicial"}
        if asignaciones:
            if not ubicacion:
                return {"error": "Debes especificar una categoría válida del desglose inicial."}
            if ubicacion not in asignaciones:
                return {"error": f"La categoría '{ubicacion}' no está en el desglose inicial."}
        else:
            ubicacion = ubicacion if ubicacion else None

        if ubicacion and asignaciones and ubicacion in asignaciones:
            total_avances = sum(a.cantidad_avance for a in kpi.avances 
                              if a.ubicacion == ubicacion and a.comentario != "Asignación inicial")
            if total_avances + int(cantidad_avance) > asignaciones[ubicacion]:
                return {"error": f"No puedes exceder las {asignaciones[ubicacion]} unidades asignadas a {ubicacion}."}

        avance = AvanceKPI(
            id_kpi=id_kpi,
            fecha_avance=datetime.strptime(fecha_avance, '%Y-%m-%d').date(),
            ubicacion=ubicacion,
            cantidad_avance=int(cantidad_avance),
            comentario=comentario,
            create_time=datetime.utcnow()
        )
        
        db.session.add(avance)
        total_avances_global = sum(a.cantidad_avance for a in kpi.avances if a.comentario != "Asignación inicial") + int(cantidad_avance)
        if total_avances_global >= kpi.total_unidades:
            kpi.estado = "completado"
        else:
            kpi.estado = "en progreso"

        db.session.commit()
        return {"success": "Avance registrado exitosamente."}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error al registrar el avance: {str(e)}"}

def agregar_categoria_inicial(id_kpi, nueva_categoria, cantidad_categoria):
    try:
        kpi = KPI.query.get(id_kpi)
        if not kpi:
            return {"error": "KPI no encontrado."}

        # Verificar que la categoría no exista ya
        asignaciones = {a.ubicacion: a.cantidad_avance for a in kpi.avances if a.comentario == "Asignación inicial"}
        if nueva_categoria in asignaciones:
            return {"error": f"La categoría '{nueva_categoria}' ya existe en el desglose inicial."}

        # Calcular la suma actual de unidades asignadas
        total_asignado = sum(a.cantidad_avance for a in kpi.avances if a.comentario == "Asignación inicial")
        nueva_cantidad = int(cantidad_categoria)

        # Validar que no se exceda el total_unidades
        if total_asignado + nueva_cantidad > kpi.total_unidades:
            unidades_restantes = kpi.total_unidades - total_asignado
            if unidades_restantes <= 0:
                return {"error": "No puedes agregar más categorías: el total de unidades ya está completamente asignado."}
            return {"error": f"No puedes exceder el total de {kpi.total_unidades} unidades. Solo puedes asignar hasta {unidades_restantes} unidades más."}

        # Crear un nuevo avance como "Asignación inicial"
        nueva_asignacion = AvanceKPI(
            id_kpi=id_kpi,
            fecha_avance=kpi.fecha_inicio,  # Usar la fecha de inicio del KPI
            ubicacion=nueva_categoria,
            cantidad_avance=nueva_cantidad,
            comentario="Asignación inicial",
            create_time=datetime.utcnow()
        )

        db.session.add(nueva_asignacion)
        db.session.commit()
        return {"success": f"Categoría '{nueva_categoria}' agregada exitosamente."}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error al agregar la categoría: {str(e)}"}