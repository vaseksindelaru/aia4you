import mysql.connector
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
db_config = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "21blackjack"),
    "database": os.getenv("MYSQL_DATABASE", "sql1")
}

def check_strategies():
    """Consulta las estrategias guardadas en la base de datos"""
    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # Consultar las estrategias
        cursor.execute("SELECT uuid, name, description, created_at FROM strategies")
        strategies = cursor.fetchall()
        
        if strategies:
            print(f"Se encontraron {len(strategies)} estrategias:")
            for strategy in strategies:
                print(f"UUID: {strategy['uuid']}")
                print(f"Nombre: {strategy['name']}")
                print(f"Descripción: {strategy['description']}")
                print(f"Fecha de creación: {strategy['created_at']}")
                print("-" * 50)
        else:
            print("No se encontraron estrategias en la base de datos.")
        
    except Exception as e:
        print(f"Error al consultar las estrategias: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    check_strategies()
