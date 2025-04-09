import os
import mysql.connector
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'binance_lob')
}

print("Configuración de la base de datos:")
for key, value in DB_CONFIG.items():
    print(f"  {key}: {value}")

try:
    print("\nIntentando conectar a la base de datos...")
    conn = mysql.connector.connect(**DB_CONFIG)
    print("Conexión exitosa!")
    
    # Verificar si las tablas existen
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES LIKE 'A_%'")
    tables = cursor.fetchall()
    
    print("\nTablas encontradas:")
    for table in tables:
        print(f"  {table[0]}")
    
    cursor.close()
    conn.close()
    
except mysql.connector.Error as err:
    print(f"Error al conectar a la base de datos: {err}")
