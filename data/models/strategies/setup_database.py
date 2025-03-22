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

def execute_sql_file(file_path):
    """Ejecuta un archivo SQL en la base de datos"""
    try:
        # Leer el archivo SQL
        with open(file_path, 'r') as file:
            sql_script = file.read()
        
        # Conectar a la base de datos
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        # Ejecutar el script SQL
        for statement in sql_script.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        # Confirmar los cambios
        connection.commit()
        print(f"Script SQL ejecutado correctamente: {file_path}")
        
    except Exception as e:
        print(f"Error al ejecutar el script SQL: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    # Ruta a los archivos SQL
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ejecutar los scripts SQL
    execute_sql_file(os.path.join(base_dir, "setup_indicators.sql"))
    execute_sql_file(os.path.join(base_dir, "setup_strategies.sql"))
    
    print("Configuración de la base de datos completada.")
