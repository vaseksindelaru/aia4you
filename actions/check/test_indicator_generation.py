import requests
import json
import time
import mysql.connector
import os
from dotenv import load_dotenv

def test_indicator_generation():
    """
    Prueba la generación y guardado de indicadores
    """
    print("===== PRUEBA DE GENERACIÓN DE INDICADORES =====")
    
    # Probar generación de indicador de volumen
    print("\n1. Generando indicador de volumen...")
    try:
        response = requests.post(
            "http://localhost:8506/generate_indicator/",
            json={"prompt": "Crear indicador de trading Volume"}
        )
        
        print(f"Código de respuesta: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Respuesta: {data.get('status')}")
            print(f"Estructura completa de la respuesta: {json.dumps(data, indent=2)}")
            
            if data.get('status') == 'success':
                indicator_data = data.get('indicator_data', {})
                print(f"Nombre del indicador: {indicator_data.get('name')}")
                print(f"Descripción: {indicator_data.get('description', 'No disponible')[:50]}...")
                print(f"Config YAML presente: {'Sí' if 'config_yaml' in indicator_data and indicator_data['config_yaml'] else 'No'}")
                print(f"Implementation YAML presente: {'Sí' if 'implementation_yaml' in indicator_data and indicator_data['implementation_yaml'] else 'No'}")
                
                # Guardar el indicador
                print("\n2. Guardando el indicador en la base de datos...")
                save_response = requests.post(
                    "http://localhost:8506/save_indicator/",
                    json={"indicator_data": indicator_data}
                )
                
                print(f"Código de respuesta: {save_response.status_code}")
                if save_response.status_code == 200:
                    save_data = save_response.json()
                    print(f"Respuesta: {save_data.get('status')}")
                    print(f"Mensaje: {save_data.get('message')}")
                else:
                    print(f"Error al guardar el indicador: {save_response.status_code}")
                    print(save_response.text)
            else:
                print(f"Error en la generación: {data.get('message', 'Error desconocido')}")
        else:
            print(f"Error en la solicitud: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error al generar el indicador de volumen: {str(e)}")
    
    # Probar generación de indicador RSI
    print("\n3. Generando indicador RSI...")
    try:
        response = requests.post(
            "http://localhost:8506/generate_indicator/",
            json={"prompt": "Crear indicador de trading RSI"}
        )
        
        print(f"Código de respuesta: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Respuesta: {data.get('status')}")
            print(f"Estructura completa de la respuesta: {json.dumps(data, indent=2)}")
            
            if data.get('status') == 'success':
                indicator_data = data.get('indicator_data', {})
                print(f"Nombre del indicador: {indicator_data.get('name')}")
                print(f"Descripción: {indicator_data.get('description', 'No disponible')[:50]}...")
                print(f"Config YAML presente: {'Sí' if 'config_yaml' in indicator_data and indicator_data['config_yaml'] else 'No'}")
                print(f"Implementation YAML presente: {'Sí' if 'implementation_yaml' in indicator_data and indicator_data['implementation_yaml'] else 'No'}")
                
                # Guardar el indicador
                print("\n4. Guardando el indicador RSI en la base de datos...")
                save_response = requests.post(
                    "http://localhost:8506/save_indicator/",
                    json={"indicator_data": indicator_data}
                )
                
                print(f"Código de respuesta: {save_response.status_code}")
                if save_response.status_code == 200:
                    save_data = save_response.json()
                    print(f"Respuesta: {save_data.get('status')}")
                    print(f"Mensaje: {save_data.get('message')}")
                else:
                    print(f"Error al guardar el indicador: {save_response.status_code}")
                    print(save_response.text)
            else:
                print(f"Error en la generación: {data.get('message', 'Error desconocido')}")
        else:
            print(f"Error en la solicitud: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error al generar el indicador RSI: {str(e)}")
    
    # Esperar un momento para que se procesen los cambios
    print("\nEsperando 2 segundos para que se procesen los cambios...")
    time.sleep(2)
    
    # Verificar los indicadores en la base de datos
    print("\n5. Verificando los indicadores en la base de datos...")
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
        
        # Buscar indicadores recién creados
        cursor.execute("SELECT * FROM indicators ORDER BY created_at DESC LIMIT 5")
        indicators = cursor.fetchall()
        
        print("\nÚltimos 5 indicadores en la base de datos:")
        for ind in indicators:
            print(f"ID: {ind['id']}, Nombre: {ind['name']}, UUID: {ind.get('uuid', 'N/A')}")
            print(f"  Descripción: {'Presente' if ind.get('description') else 'Ausente'}")
            print(f"  Config YAML: {'Presente' if ind.get('config_yaml') else 'Ausente'}")
            print(f"  Implementation YAML: {'Presente' if ind.get('implementation_yaml') else 'Ausente'}")
            print(f"  Creado: {ind.get('created_at', 'N/A')}")
            print("-" * 50)
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al verificar los indicadores en la base de datos: {str(e)}")

if __name__ == "__main__":
    test_indicator_generation()
