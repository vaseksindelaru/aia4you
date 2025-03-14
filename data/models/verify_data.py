import mysql.connector

# Configuración de la conexión
config = {
    "host": 'localhost',
    "user": 'root',
    "password": '21blackjack',
    "database": 'sql1'
}

try:
    # Establecer conexión
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor(dictionary=True)
    
    # Consultar el registro
    query = "SELECT * FROM apis_db WHERE uuid = '550e8400-e29b-41d4-a716-446655440000'"
    cursor.execute(query)
    result = cursor.fetchone()
    
    if result:
        print("\nRegistro encontrado:")
        print(f"UUID: {result['uuid']}")
        print(f"Nombre: {result['name']}")
        print(f"Descripción: {result['description']}")
        print("\nConfiguración YAML:")
        print(result['config_yaml'])
    else:
        print("No se encontró el registro")
    
except mysql.connector.Error as err:
    print(f"Error: {err}")
    
finally:
    if 'conn' in locals() and conn.is_connected():
        cursor.close()
        conn.close()
        print("\nConexión cerrada")
