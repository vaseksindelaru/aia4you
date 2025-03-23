"""
Script para actualizar la estructura de la tabla de indicadores
"""
import os
import mysql.connector
from dotenv import load_dotenv
import uuid

# Cargar variables de entorno
load_dotenv()

# Conectar a la base de datos
connection = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST", "localhost"),
    user=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD", ""),
    database=os.getenv("MYSQL_DATABASE", "sql1")
)

cursor = connection.cursor()

try:
    print("Actualizando la estructura de la tabla de indicadores...")
    
    # Verificar si las columnas ya existen
    cursor.execute("SHOW COLUMNS FROM indicators LIKE 'uuid'")
    uuid_exists = cursor.fetchone() is not None
    
    if not uuid_exists:
        # Añadir las nuevas columnas
        alter_queries = [
            "ALTER TABLE indicators ADD COLUMN uuid VARCHAR(36) AFTER id",
            "ALTER TABLE indicators ADD COLUMN description TEXT AFTER name",
            "ALTER TABLE indicators ADD COLUMN config_yaml TEXT AFTER description",
            "ALTER TABLE indicators ADD COLUMN implementation_yaml TEXT AFTER config_yaml",
            "ALTER TABLE indicators ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP AFTER implementation_yaml"
        ]
        
        for query in alter_queries:
            print(f"Ejecutando: {query}")
            cursor.execute(query)
            
        # Actualizar los registros existentes con UUIDs
        cursor.execute("SELECT id FROM indicators")
        indicators = cursor.fetchall()
        
        for indicator_id in indicators:
            new_uuid = str(uuid.uuid4())
            update_query = "UPDATE indicators SET uuid = %s WHERE id = %s"
            cursor.execute(update_query, (new_uuid, indicator_id[0]))
            print(f"Actualizado indicador ID {indicator_id[0]} con UUID {new_uuid}")
        
        connection.commit()
        print("Estructura de la tabla actualizada correctamente.")
    else:
        print("La estructura de la tabla ya está actualizada.")
    
    # Verificar la estructura actualizada
    print("\nEstructura actualizada de la tabla de indicadores:")
    cursor.execute("DESCRIBE indicators")
    columns = cursor.fetchall()
    for column in columns:
        print(f"Columna: {column[0]}, Tipo: {column[1]}")

except Exception as e:
    print(f"Error: {e}")
    connection.rollback()

finally:
    cursor.close()
    connection.close()
