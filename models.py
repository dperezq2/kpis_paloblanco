from database import db
from datetime import datetime

# Tablas existentes (sin cambios)
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(16), nullable=False, unique=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255), nullable=False)
    id_departamento = db.Column(db.Integer, db.ForeignKey('departamento.id'))
    status = db.Column(db.String(15))
    create_time = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    departamento = db.relationship('Departamento', backref=db.backref('usuarios', lazy=True))


class Departamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200))
    create_time = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    update_time = db.Column(db.TIMESTAMP, nullable=True)


# Nuevas tablas
class Proyecto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200), nullable=False)
    encargado = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    id_departamento = db.Column(db.Integer, db.ForeignKey('departamento.id'), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(20), default='en progreso')
    create_time = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    update_time = db.Column(db.TIMESTAMP, nullable=True)

    usuario_encargado = db.relationship('Usuario', backref=db.backref('proyectos_encargados', lazy=True))
    departamento = db.relationship('Departamento', backref=db.backref('proyectos', lazy=True))


class Actividad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200), nullable=False)
    id_proyecto = db.Column(db.Integer, db.ForeignKey('proyecto.id'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    fecha_inicio_planificada = db.Column(db.Date, nullable=False)
    fecha_fin_planificada = db.Column(db.Date, nullable=False)
    fecha_inicio_real = db.Column(db.Date, nullable=True)
    fecha_fin_real = db.Column(db.Date, nullable=True)
    estado = db.Column(db.String(20), default='pendiente')
    create_time = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    update_time = db.Column(db.TIMESTAMP, nullable=True)

    proyecto = db.relationship('Proyecto', backref=db.backref('actividades', lazy=True))
    usuario = db.relationship('Usuario', backref=db.backref('actividades', lazy=True))
    
    
class KPI(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    meta_porcentaje = db.Column(db.Float, nullable=False)  # Ejemplo: 95% 
    total_unidades = db.Column(db.Integer, nullable=False)  # Ejemplo: 400 equipos
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(20), default='en progreso')  # 'en progreso', 'completado'
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)  # Responsable
    create_time = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    usuario = db.relationship('Usuario', backref=db.backref('kpis', lazy=True))


class AvanceKPI(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_kpi = db.Column(db.Integer, db.ForeignKey('kpi.id'), nullable=False)
    fecha_avance = db.Column(db.Date, nullable=False)
    ubicacion = db.Column(db.String(100), nullable=False)  # Ejemplo: "Finca 1"
    cantidad_avance = db.Column(db.Integer, nullable=False)  # Cantidad de equipos mantenidos en esa finca
    comentario = db.Column(db.Text, nullable=True)  # Observaciones opcionales
    create_time = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    kpi = db.relationship('KPI', backref=db.backref('avances', lazy=True))
