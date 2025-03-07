from app import app
from database import db

# Crear las tablas dentro del contexto de la aplicación
with app.app_context():
    db.create_all()
    print("✅ Tablas creadas exitosamente.")
# Ejecutar este script para crear las tablas en la base de datos.