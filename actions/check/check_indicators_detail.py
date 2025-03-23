import mysql.connector
import os
from dotenv import load_dotenv
import sys

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
db_config = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "sql1")
}

def check_indicators():
    """
    Verifica la estructura y contenido de la tabla de indicadores.
    """
    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Obtener información de la tabla
        cursor.execute("DESCRIBE indicators")
        columns = cursor.fetchall()
        
        print("\n===== ESTRUCTURA DE LA TABLA DE INDICADORES =====")
        for column in columns:
            print(f"Columna: {column['Field']}, Tipo: {column['Type']}, Nulo: {column['Null']}")
        
        # Contar indicadores
        cursor.execute("SELECT COUNT(*) as count FROM indicators")
        count = cursor.fetchone()['count']
        print(f"\nTotal de indicadores en la base de datos: {count}")
        
        # Listar indicadores
        cursor.execute("SELECT id, name, uuid, description IS NOT NULL as has_description, "
                      "config_yaml IS NOT NULL as has_config, "
                      "implementation_yaml IS NOT NULL as has_implementation, "
                      "created_at FROM indicators")
        indicators = cursor.fetchall()
        
        print("\n===== LISTA DE INDICADORES =====")
        for ind in indicators:
            print(f"ID: {ind['id']}, Nombre: {ind['name']}, UUID: {ind.get('uuid', 'N/A')}")
            print(f"  Descripción: {'Presente' if ind['has_description'] else 'Ausente'}")
            print(f"  Config YAML: {'Presente' if ind['has_config'] else 'Ausente'}")
            print(f"  Implementation YAML: {'Presente' if ind['has_implementation'] else 'Ausente'}")
            print(f"  Creado: {ind.get('created_at', 'N/A')}")
            print("-" * 50)
        
        # Si se proporciona un nombre de indicador como argumento, mostrar detalles
        if len(sys.argv) > 1:
            indicator_name = sys.argv[1]
            cursor.execute("SELECT * FROM indicators WHERE name LIKE %s", (f"%{indicator_name}%",))
            indicator = cursor.fetchone()
            
            if indicator:
                print(f"\n===== DETALLES DEL INDICADOR: {indicator['name']} =====")
                print(f"ID: {indicator['id']}")
                print(f"UUID: {indicator.get('uuid', 'N/A')}")
                print(f"Descripción: {indicator.get('description', 'N/A')}")
                print(f"\nConfig YAML:")
                print(indicator.get('config_yaml', 'N/A'))
                print(f"\nImplementation YAML:")
                print(indicator.get('implementation_yaml', 'N/A'))
            else:
                print(f"\nNo se encontró un indicador con el nombre '{indicator_name}'")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"Error de base de datos: {err}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_indicators()
