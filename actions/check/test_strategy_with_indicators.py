import requests
import json
import time
import mysql.connector
import os
from dotenv import load_dotenv

def test_strategy_with_indicators():
    """
    Prueba la generación de una estrategia que requiere indicadores específicos.
    Verifica que los indicadores se generen automáticamente si no existen.
    """
    print("===== PRUEBA DE GENERACIÓN DE ESTRATEGIA CON INDICADORES =====")
    
    # 1. Verificar indicadores existentes antes de la prueba
    print("\n1. Verificando indicadores existentes antes de la prueba...")
    existing_indicators = get_indicators()
    print(f"Indicadores existentes: {len(existing_indicators)}")
    for ind in existing_indicators[:5]:  # Mostrar solo los primeros 5
        print(f"  - {ind['name']}")
    
    # 2. Generar una estrategia que requiera indicadores específicos
    print("\n2. Generando estrategia que requiere indicadores específicos...")
    try:
        response = requests.post(
            "http://localhost:8505/generate_strategy/",
            json={"prompt": "Crear estrategia de trading que use RSI y Volume para detectar divergencias"}
        )
        
        print(f"Código de respuesta: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Respuesta: {data.get('status')}")
            print(f"Mensaje: {data.get('message', 'No hay mensaje')}")
            
            # Mostrar detalles de la estrategia si está disponible
            if 'strategy_data' in data:
                strategy = data['strategy_data']
                print(f"\nEstrategia generada:")
                print(f"Nombre: {strategy.get('name', 'No disponible')}")
                print(f"Descripción: {strategy.get('description', 'No disponible')[:100]}...")
                print(f"Indicadores utilizados: {strategy.get('indicators', [])}")
        else:
            print(f"Error en la solicitud: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error al generar la estrategia: {str(e)}")
        print("Es posible que el servicio de generación de estrategias no esté en ejecución.")
        print("Asegúrate de ejecutar 'python actions\\generate\\strategy_generator.py' en otra ventana.")
    
    # 3. Verificar indicadores después de la generación de la estrategia
    print("\n3. Verificando indicadores después de la generación de la estrategia...")
    time.sleep(2)  # Esperar a que se completen las operaciones
    new_indicators = get_indicators()
    print(f"Indicadores después de la prueba: {len(new_indicators)}")
    
    # Mostrar los indicadores más recientes
    print("\nIndicadores más recientes:")
    for ind in sorted(new_indicators, key=lambda x: x.get('created_at', ''), reverse=True)[:5]:
        print(f"  - {ind['name']} (Creado: {ind.get('created_at')})")
        print(f"    Descripción: {ind.get('description', 'No disponible')[:50]}...")
        print(f"    Config YAML: {'Presente' if ind.get('config_yaml') else 'Ausente'}")
        print(f"    Implementation YAML: {'Presente' if ind.get('implementation_yaml') else 'Ausente'}")
        print("-" * 50)
    
    # 4. Verificar si se generaron nuevos indicadores
    new_indicator_count = len(new_indicators) - len(existing_indicators)
    if new_indicator_count > 0:
        print(f"\nSe generaron {new_indicator_count} nuevos indicadores durante la prueba.")
    else:
        print("\nNo se generaron nuevos indicadores. Es posible que ya existieran todos los indicadores necesarios.")

def get_indicators():
    """
    Obtiene la lista de indicadores de la base de datos.
    """
    try:
        # Cargar variables de entorno
        load_dotenv()
        
        # Configuración de la base de datos
        db_config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "database": os.getenv("MYSQL_DATABASE", "sql1")
        }
        
        # Conectar a la base de datos
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Obtener todos los indicadores
        cursor.execute("SELECT * FROM indicators")
        indicators = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return indicators
    except Exception as e:
        print(f"Error al obtener indicadores: {str(e)}")
        return []

if __name__ == "__main__":
    test_strategy_with_indicators()
