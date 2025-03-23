import requests
import json
import time
import mysql.connector
import os
from dotenv import load_dotenv

def test_indicator_integration():
    """
    Prueba la integración entre el generador de indicadores y el sistema de estrategias.
    """
    print("===== PRUEBA DE INTEGRACIÓN DE INDICADORES =====")
    
    # 1. Verificar que el servicio de indicadores esté en ejecución
    print("\n1. Verificando servicio de indicadores...")
    indicator_service_running = check_service("http://localhost:8506/health")
    if not indicator_service_running:
        print("El servicio de indicadores no está en ejecución. Iniciándolo...")
        # Aquí podrías añadir código para iniciar el servicio automáticamente
        print("Por favor, ejecuta 'python actions\\generate\\indicator_generator.py' en otra ventana.")
        return
    else:
        print("Servicio de indicadores: ACTIVO")
    
    # 2. Generar un indicador personalizado
    print("\n2. Generando indicador personalizado...")
    try:
        response = requests.post(
            "http://localhost:8506/generate_indicator/",
            json={"prompt": "Crear indicador de divergencia RSI-Precio que detecte cuando el precio sube pero el RSI baja"}
        )
        
        print(f"Código de respuesta: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Respuesta: {data.get('status')}")
            
            # Verificar la estructura de la respuesta
            if 'indicator_data' in data:
                indicator = data['indicator_data']
                print(f"\nIndicador generado:")
                print(f"Nombre: {indicator.get('name', 'No disponible')}")
                print(f"Descripción: {indicator.get('description', 'No disponible')[:100]}...")
                
                # Verificar que los campos YAML estén presentes
                config_yaml = indicator.get('config_yaml', '')
                impl_yaml = indicator.get('implementation_yaml', '')
                print(f"Config YAML presente: {'Sí' if config_yaml else 'No'}")
                print(f"Implementation YAML presente: {'Sí' if impl_yaml else 'No'}")
                
                # Si ambos campos YAML están presentes, guardar el indicador
                if config_yaml and impl_yaml:
                    print("\n3. Guardando el indicador en la base de datos...")
                    save_response = requests.post(
                        "http://localhost:8506/save_indicator/",
                        json={"indicator_data": indicator}
                    )
                    
                    print(f"Código de respuesta: {save_response.status_code}")
                    if save_response.status_code == 200:
                        save_data = save_response.json()
                        print(f"Respuesta: {save_data.get('status')}")
                        print(f"Mensaje: {save_data.get('message', 'No hay mensaje')}")
                    else:
                        print(f"Error al guardar el indicador: {save_response.status_code}")
                        print(save_response.text)
            else:
                print("La respuesta no contiene datos del indicador")
        else:
            print(f"Error en la solicitud: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error al generar el indicador: {str(e)}")
    
    # 4. Verificar los indicadores en la base de datos
    print("\n4. Verificando los indicadores en la base de datos...")
    time.sleep(2)  # Esperar a que se completen las operaciones
    indicators = get_indicators()
    
    print(f"\nÚltimos 5 indicadores en la base de datos:")
    for ind in sorted(indicators, key=lambda x: x.get('created_at', ''), reverse=True)[:5]:
        print(f"ID: {ind.get('id')}, Nombre: {ind.get('name')}, UUID: {ind.get('uuid')}")
        print(f"  Descripción: {'Presente' if ind.get('description') else 'Ausente'}")
        print(f"  Config YAML: {'Presente' if ind.get('config_yaml') else 'Ausente'}")
        print(f"  Implementation YAML: {'Presente' if ind.get('implementation_yaml') else 'Ausente'}")
        print(f"  Creado: {ind.get('created_at')}")
        print("-" * 50)

def check_service(url):
    """
    Verifica si un servicio está en ejecución.
    """
    try:
        response = requests.get(url, timeout=2)
        return response.status_code == 200
    except:
        return False

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
    test_indicator_integration()
