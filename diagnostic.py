"""
Script de diagnóstico para verificar la estructura del proyecto y los módulos
"""
import os
import sys
import importlib
import pandas as pd
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def check_environment():
    """Verificar variables de entorno"""
    print("===== Verificando Variables de Entorno =====")
    env_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE', 'API_BASE_URL']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Ocultar contraseña
            if var == 'MYSQL_PASSWORD':
                print(f"[OK] {var}: ****** (configurado)")
            else:
                print(f"[OK] {var}: {value}")
        else:
            print(f"[ERROR] {var}: No configurado")
    print()

def check_project_structure():
    """Verificar estructura del proyecto"""
    print("===== Verificando Estructura del Proyecto =====")
    
    # Verificar directorios principales
    dirs_to_check = [
        'actions/evolve/A_optimizer',
        'apis/indicators/atr',
        'data/BTCUSDC-5m-2025-04-08'
    ]
    
    for dir_path in dirs_to_check:
        full_path = os.path.join(os.path.dirname(__file__), dir_path)
        if os.path.exists(full_path):
            print(f"[OK] Directorio {dir_path} existe")
        else:
            print(f"[ERROR] Directorio {dir_path} no existe")
    
    # Verificar archivos principales
    files_to_check = [
        'actions/evolve/A_optimizer/detection.py',
        'actions/evolve/A_optimizer/range.py',
        'actions/evolve/A_optimizer/breakout.py',
        'apis/indicators/atr/A_atr.py',
        'main.py',
        'data/BTCUSDC-5m-2025-04-08/BTCUSDC-5m-2025-04-08.csv'
    ]
    
    for file_path in files_to_check:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            print(f"[OK] Archivo {file_path} existe")
        else:
            print(f"[ERROR] Archivo {file_path} no existe")
    print()

def check_imports():
    """Verificar importaciones de módulos"""
    print("===== Verificando Importaciones de Módulos =====")
    
    modules_to_check = [
        ('pandas', 'pd'),
        ('numpy', 'np'),
        ('mysql.connector', None),
        ('dotenv', 'load_dotenv'),
        ('fastapi', 'FastAPI'),
        ('requests', None)
    ]
    
    for module, attr in modules_to_check:
        try:
            if attr:
                # Verificar si se puede importar el atributo específico
                exec(f"from {module} import {attr}")
                print(f"[OK] Módulo {module} (atributo {attr}) importado correctamente")
            else:
                # Verificar si se puede importar el módulo
                importlib.import_module(module)
                print(f"[OK] Módulo {module} importado correctamente")
        except ImportError as e:
            print(f"[ERROR] Error al importar {module}: {e}")
    print()

def check_data_file():
    """Verificar archivo de datos"""
    print("===== Verificando Archivo de Datos =====")
    
    data_path = os.path.join('data', 'BTCUSDC-5m-2025-04-08', 'BTCUSDC-5m-2025-04-08.csv')
    full_path = os.path.join(os.path.dirname(__file__), data_path)
    
    if os.path.exists(full_path):
        try:
            data = pd.read_csv(full_path)
            print(f"[OK] Archivo de datos cargado correctamente: {len(data)} filas")
            print(f"[OK] Columnas disponibles: {', '.join(data.columns)}")
            print(f"[OK] Primeras 3 filas:")
            print(data.head(3))
        except Exception as e:
            print(f"[ERROR] Error al cargar el archivo de datos: {e}")
    else:
        print(f"[ERROR] Archivo de datos no encontrado en {full_path}")
    print()

def check_mysql_connection():
    """Verificar conexión a MySQL"""
    print("===== Verificando Conexión a MySQL =====")
    
    try:
        import mysql.connector
        from mysql.connector import Error
        
        # Obtener configuración de la base de datos
        host = os.getenv('MYSQL_HOST', 'localhost')
        user = os.getenv('MYSQL_USER', 'root')
        password = os.getenv('MYSQL_PASSWORD', '')
        database = os.getenv('MYSQL_DATABASE', 'binance_lob')
        
        # Intentar conectar a MySQL
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        
        if connection.is_connected():
            print(f"[OK] Conexión a MySQL establecida correctamente")
            
            # Verificar si la base de datos existe
            cursor = connection.cursor()
            cursor.execute(f"SHOW DATABASES LIKE '{database}'")
            result = cursor.fetchone()
            
            if result:
                print(f"[OK] Base de datos '{database}' existe")
                
                # Conectar a la base de datos
                cursor.execute(f"USE {database}")
                
                # Verificar tablas
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                
                if tables:
                    print(f"[OK] Tablas en la base de datos:")
                    for table in tables:
                        print(f"  - {table[0]}")
                else:
                    print(f"[OK] No hay tablas en la base de datos (se crearán al ejecutar los módulos)")
            else:
                print(f"[ERROR] Base de datos '{database}' no existe")
            
            cursor.close()
            connection.close()
            print("[OK] Conexión a MySQL cerrada correctamente")
        else:
            print(f"[ERROR] No se pudo establecer conexión a MySQL")
    
    except Error as e:
        print(f"[ERROR] Error al conectar a MySQL: {e}")
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")
    print()

def check_api_connection():
    """Verificar conexión a la API"""
    print("===== Verificando Conexión a la API =====")
    
    try:
        import requests
        
        # Obtener URL base de la API
        api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        
        # Intentar conectar a la API
        response = requests.get(f"{api_base_url}/docs")
        
        if response.status_code == 200:
            print(f"[OK] Conexión a la API establecida correctamente")
            
            # Probar endpoint ATR
            try:
                atr_response = requests.get(f"{api_base_url}/indicators/atr", params={'period': 14, 'symbol': 'BTCUSDC'})
                
                if atr_response.status_code == 200:
                    print(f"[OK] Endpoint ATR funcionando correctamente")
                    print(f"  Respuesta: {atr_response.json()}")
                else:
                    print(f"[ERROR] Error en el endpoint ATR: {atr_response.status_code}")
            except Exception as e:
                print(f"[ERROR] Error al probar el endpoint ATR: {e}")
        else:
            print(f"[ERROR] No se pudo conectar a la API: {response.status_code}")
    
    except Exception as e:
        print(f"[ERROR] Error al verificar la API: {e}")
    print()

def main():
    """Función principal"""
    print("==============================================")
    print("DIAGNÓSTICO DEL SISTEMA A_OPTIMIZER")
    print("==============================================")
    
    # Ejecutar verificaciones
    check_environment()
    check_project_structure()
    check_imports()
    check_data_file()
    check_mysql_connection()
    check_api_connection()
    
    print("==============================================")
    print("DIAGNÓSTICO COMPLETADO")
    print("==============================================")

if __name__ == "__main__":
    main()
