"""
Script para verificar la estructura de la tabla de indicadores
"""
import os
import mysql.connector
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Conectar a la base de datos
connection = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST", "localhost"),
    user=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD", ""),
    database=os.getenv("MYSQL_DATABASE", "sql1")
)

cursor = connection.cursor(dictionary=True)

try:
    # Verificar la estructura de la tabla de indicadores
    print("Estructura de la tabla de indicadores:")
    cursor.execute("DESCRIBE indicators")
    columns = cursor.fetchall()
    for column in columns:
        print(f"Columna: {column['Field']}, Tipo: {column['Type']}, Nulo: {column['Null']}, Clave: {column['Key']}, Default: {column['Default']}")
    
    # Verificar los indicadores existentes
    print("\nIndicadores existentes:")
    cursor.execute("SELECT * FROM indicators")
    indicators = cursor.fetchall()
    for indicator in indicators:
        print(f"ID: {indicator['id']}, Nombre: {indicator['name']}")
        # Verificar si existen las columnas esperadas
        expected_columns = ['uuid', 'description', 'config_yaml', 'implementation_yaml']
        for col in expected_columns:
            if col in indicator:
                print(f"  {col}: {'Presente' if indicator[col] else 'Ausente'}")
            else:
                print(f"  {col}: No existe en la tabla")

except Exception as e:
    print(f"Error: {e}")

finally:
    cursor.close()
    connection.close()
