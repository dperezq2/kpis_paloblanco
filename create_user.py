import sys
from app import app, db  # Importa tu aplicación Flask y la base de datos
from utils import crear_usuario  # Importa la función para crear usuarios

def main():
    # Verificar que tenemos los argumentos correctos
    if len(sys.argv) != 6:
        print("Uso: python create_user.py <username> <password> <email> <id_departamento> <status>")
        return
    
    # Obtener argumentos
    username = sys.argv[1]
    password = sys.argv[2]
    email = sys.argv[3]
    id_departamento = sys.argv[4]
    status = sys.argv[5]

    # Crear contexto de aplicación para poder usar la base de datos
    with app.app_context():
        try:
            # Crear el usuario
            resultado = crear_usuario(username, password, email, id_departamento, status)

            if "success" in resultado:
                print(resultado["success"])
            else:
                print(resultado["error"])
        except Exception as e:
            print(f"Error al crear usuario: {e}")

if __name__ == "__main__":
    main()
