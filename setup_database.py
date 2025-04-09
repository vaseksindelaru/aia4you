"""
Script para verificar y crear la base de datos MySQL para A_optimizer
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def setup_database():
    """Verificar y crear la base de datos MySQL si no existe"""
    
    # Obtener configuración de la base de datos
    host = os.getenv('MYSQL_HOST', 'localhost')
    user = os.getenv('MYSQL_USER', 'root')
    password = os.getenv('MYSQL_PASSWORD', '')
    database = os.getenv('MYSQL_DATABASE', 'binance_lob')
    
    try:
        # Conectar sin especificar la base de datos
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Verificar si la base de datos existe
            cursor.execute(f"SHOW DATABASES LIKE '{database}'")
            result = cursor.fetchone()
            
            if not result:
                print(f"La base de datos '{database}' no existe. Creándola...")
                cursor.execute(f"CREATE DATABASE {database}")
                print(f"Base de datos '{database}' creada exitosamente.")
            else:
                print(f"La base de datos '{database}' ya existe.")
            
            # Conectar a la base de datos
            cursor.execute(f"USE {database}")
            
            # Verificar las tablas del sistema A_optimizer
            tables_to_check = [
                'A_detection_params',
                'A_detection_data',
                'A_range_params',
                'A_range_data',
                'A_breakout_params',
                'A_breakout_data'
            ]
            
            existing_tables = []
            for table in tables_to_check:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if cursor.fetchone():
                    existing_tables.append(table)
            
            if existing_tables:
                print(f"Tablas existentes: {', '.join(existing_tables)}")
            else:
                print("No se encontraron tablas del sistema A_optimizer. Se crearán al ejecutar los módulos.")
            
            print("\nConfiguración de la base de datos completada exitosamente.")
            
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexión a MySQL cerrada.")

if __name__ == "__main__":
    print("Configurando la base de datos para A_optimizer...")
    setup_database()
