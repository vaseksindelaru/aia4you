"""
Script para borrar todos los indicadores excepto Momentum y Bollinger Bands
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
    # Primero, listar todos los indicadores para verificar
    print("Indicadores antes de la eliminación:")
    cursor.execute("SELECT id, name FROM indicators")
    indicators = cursor.fetchall()
    for indicator in indicators:
        print(f"ID: {indicator['id']}, Nombre: {indicator['name']}")
    
    # Borrar todos los indicadores excepto Momentum y Bollinger Bands
    cursor.execute("""
        DELETE FROM indicators 
        WHERE name NOT LIKE '%Momentum%' 
        AND name NOT LIKE '%Bollinger%'
    """)
    
    # Confirmar los cambios
    connection.commit()
    
    # Verificar los indicadores restantes
    print("\nIndicadores después de la eliminación:")
    cursor.execute("SELECT id, name FROM indicators")
    remaining = cursor.fetchall()
    for indicator in remaining:
        print(f"ID: {indicator['id']}, Nombre: {indicator['name']}")
    
    print(f"\nSe eliminaron {len(indicators) - len(remaining)} indicadores.")
    print(f"Quedan {len(remaining)} indicadores en la base de datos.")

except Exception as e:
    print(f"Error: {e}")
    connection.rollback()

finally:
    cursor.close()
    connection.close()
