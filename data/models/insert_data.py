import mysql.connector

# Configuración de la conexión
config = {
    "host": 'localhost',
    "user": 'root',
    "password": '21blackjack',
    "database": 'sql1'
}

# Datos a insertar
data = {
    'uuid': '550e8400-e29b-41d4-a716-446655440000',
    'name': 'MomentumTrading',
    'description': 'La estrategia busca detectar un movimiento sostenido del precio en una dirección (alcista o bajista). Esto implica medir la fuerza y la persistencia del movimiento.',
    'config_yaml': '''indicators:
  - momentum
  - rsi
  - macd
inputs:
  - price_data: "Serie temporal de precios (cierre)"
  - volume_data: "Volumen (opcional para sinergia)"
conditions:
  momentum:
    period: 14
    signal: "MOM > 0 (alcista), MOM < 0 (bajista)"
  rsi:
    period: 14
    signal: "50 < RSI < 70 (alcista), 30 < RSI < 50 (bajista)"
  macd:
    settings: [12, 26, 9]
    signal: "MACD > Signal Line (alcista), MACD < Signal Line (bajista)"
correlations:
  orderFlow: "Confirmar volumen alto en la dirección del movimiento"'''
}

try:
    # Establecer conexión
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    # Verificar si el registro existe
    check_query = "SELECT uuid FROM apis_db WHERE uuid = %(uuid)s"
    cursor.execute(check_query, {'uuid': data['uuid']})
    exists = cursor.fetchone()
    
    if exists:
        # Actualizar el registro existente
        update_query = """
        UPDATE apis_db 
        SET name = %(name)s, 
            description = %(description)s, 
            config_yaml = %(config_yaml)s
        WHERE uuid = %(uuid)s
        """
        cursor.execute(update_query, data)
        print("Registro actualizado correctamente")
    else:
        # Insertar nuevo registro
        insert_query = """
        INSERT INTO apis_db (uuid, name, description, config_yaml) 
        VALUES (%(uuid)s, %(name)s, %(description)s, %(config_yaml)s)
        """
        cursor.execute(insert_query, data)
        print("Nuevo registro insertado correctamente")
    
    # Confirmar la transacción
    conn.commit()
    
except mysql.connector.Error as err:
    print(f"Error: {err}")
    
finally:
    if 'conn' in locals() and conn.is_connected():
        cursor.close()
        conn.close()
        print("Conexión cerrada")
