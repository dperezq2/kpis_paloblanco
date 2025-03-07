from database import db
from datetime import datetime

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(16), nullable=False, unique=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(32), nullable=False)
    id_departamento = db.Column(db.Integer, db.ForeignKey('departamento.id'))
    status = db.Column(db.String(15))
    create_time = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    departamento = db.relationship('Departamento', backref=db.backref('usuarios', lazy=True))


class Departamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200))
    create_time = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    update_time = db.Column(db.TIMESTAMP, nullable=True)


class Proyecto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    encargado = db.Column(db.String(200))  # Puede ser el usuario creador o un usuario asignado
    id_departamento = db.Column(db.Integer, db.ForeignKey('departamento.id'))
    descripcion = db.Column(db.String(200))
    create_time = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    update_time = db.Column(db.TIMESTAMP, nullable=True)

    departamento = db.relationship('Departamento', backref=db.backref('proyectos', lazy=True))


class Actividad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200), nullable=False)
    id_proyecto = db.Column(db.Integer, db.ForeignKey('proyecto.id'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'))  # Puede ser asignado a un usuario
    create_time = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    update_time = db.Column(db.TIMESTAMP, nullable=True)

    proyecto = db.relationship('Proyecto', backref=db.backref('actividades', lazy=True))
    usuario = db.relationship('Usuario', backref=db.backref('actividades', lazy=True))


class ActividadInicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    anio = db.Column(db.Integer, nullable=False)
    id_actividad = db.Column(db.Integer, db.ForeignKey('actividad.id'), nullable=False)
    valor = db.Column(db.Integer, nullable=False)  # Fecha de inicio planificado
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    create_time = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    update_time = db.Column(db.TIMESTAMP, nullable=True)

    actividad = db.relationship('Actividad', backref=db.backref('inicio', lazy=True))


class ActividadDuracion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    anio = db.Column(db.Integer, nullable=False)
    id_actividad = db.Column(db.Integer, db.ForeignKey('actividad.id'), nullable=False)
    valor = db.Column(db.Integer, nullable=False)  # Duración planificada en días
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    create_time = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    update_time = db.Column(db.TIMESTAMP, nullable=True)

    actividad = db.relationship('Actividad', backref=db.backref('duracion', lazy=True))


class ActividadInicioReal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    anio = db.Column(db.Integer, nullable=False)
    id_actividad = db.Column(db.Integer, db.ForeignKey('actividad.id'), nullable=False)
    valor = db.Column(db.Integer, nullable=True)  # Fecha de inicio real
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    create_time = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    update_time = db.Column(db.TIMESTAMP, nullable=True)

    actividad = db.relationship('Actividad', backref=db.backref('inicio_real', lazy=True))


class ActividadDuracionReal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    anio = db.Column(db.Integer, nullable=False)
    id_actividad = db.Column(db.Integer, db.ForeignKey('actividad.id'), nullable=False)
    valor = db.Column(db.Integer, nullable=True)  # Duración real en días
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    create_time = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    update_time = db.Column(db.TIMESTAMP, nullable=True)

    actividad = db.relationship('Actividad', backref=db.backref('duracion_real', lazy=True))


class Mes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(100), nullable=False)


class Dia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dia = db.Column(db.String(255), nullable=False, unique=True)
    id_mes = db.Column(db.Integer, db.ForeignKey('mes.id'))

    mes = db.relationship('Mes', backref=db.backref('dias', lazy=True))
