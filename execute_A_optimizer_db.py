import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import json
import mysql.connector
from dotenv import load_dotenv
import traceback

# Cargar variables de entorno
load_dotenv()

# Añadir el directorio raíz al path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Importar módulos de A_optimizer
from actions.evolve.A_optimizer.detection import A_Detection
from actions.evolve.A_optimizer.range import A_Range
from actions.evolve.A_optimizer.breakout import A_Breakout

# Configuración de la base de datos
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'binance_lob')
}

def get_db_connection():
    """Obtener conexión a la base de datos MySQL
    
    Returns:
        mysql.connector.connection.MySQLConnection: Conexión a la base de datos
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None

def load_data(data_path=None):
    """Cargar y preparar los datos para el análisis
    
    Args:
        data_path (str, optional): Ruta al archivo de datos. Si es None, se buscará en la carpeta data.
        
    Returns:
        pd.DataFrame: DataFrame con los datos cargados y preparados
    """
    # Si no se especifica una ruta, buscar en la carpeta data
    if data_path is None:
        # Buscar en la carpeta data
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        for root, dirs, files in os.walk(data_dir):
            for dir_name in dirs:
                if 'BTCUSDC-5m-2025-04-08' in dir_name:
                    data_path = os.path.join(root, dir_name, 'BTCUSDC-5m-2025-04-08.csv')
                    print(f"Archivo encontrado: {data_path}")
                    break
    
    # Si no se encontró el archivo, retornar None
    if data_path is None or not os.path.exists(data_path):
        print("Error: No se encontró el archivo de datos.")
        return None
    
    # Cargar los datos
    try:
        data = pd.read_csv(data_path)
        print(f"Datos cargados: {len(data)} filas")
        
        # Renombrar columnas si es necesario
        if 'time' in data.columns and 'timestamp' not in data.columns:
            data['timestamp'] = pd.to_datetime(data['time'])
            print("Columnas renombradas para facilitar el procesamiento")
        
        return data
    
    except Exception as e:
        print(f"Error al cargar los datos: {e}")
        return None

def detect_key_candles(data, params=None):
    """Detectar velas clave en los datos
    
    Args:
        data (pd.DataFrame): DataFrame con los datos
        params (dict, optional): Parámetros para la detección
        
    Returns:
        list: Índices de las velas clave detectadas
    """
    # Si no se especifican parámetros, usar valores predeterminados
    if params is None:
        params = {
            'volume_percentile_threshold': 80,
            'body_percentage_threshold': 30,
            'lookback_candles': 20
        }
    
    print("\n=== DETECCIÓN DE VELAS CLAVE ===")
    print("Parámetros utilizados:")
    for key, value in params.items():
        print(f"  - {key}: {value}")
    
    # Crear instancia del detector
    detector = A_Detection()
    
    # Detectar velas clave
    key_candles = []
    for i in range(params['lookback_candles'], len(data)):
        is_key_candle = detector.detect_key_candle(
            data, 
            i, 
            params
        )
        
        if is_key_candle:
            key_candles.append(i)
    
    # Imprimir resultados
    print(f"Velas clave detectadas: {len(key_candles)} de {len(data) - params['lookback_candles']} ({len(key_candles)/(len(data) - params['lookback_candles'])*100:.2f}%)")
    if key_candles:
        print(f"Primeras 5 velas clave: {key_candles[:5]}")
    
    return key_candles

def calculate_ranges(data, key_candles, params=None):
    """Calcular rangos para las velas clave detectadas
    
    Args:
        data (pd.DataFrame): DataFrame con los datos
        key_candles (list): Índices de las velas clave detectadas
        params (dict, optional): Parámetros para el cálculo de rangos
        
    Returns:
        list: Lista de diccionarios con los datos de los rangos calculados
    """
    # Si no se especifican parámetros, usar valores predeterminados
    if params is None:
        params = {
            'atr_period': 14,
            'atr_multiplier': 1.5
        }
    
    print("\n=== CÁLCULO DE RANGOS ===")
    print("Parámetros utilizados:")
    for key, value in params.items():
        print(f"  - {key}: {value}")
    
    # Crear instancia del calculador de rangos
    range_calculator = A_Range()
    
    # Calcular rangos
    ranges = []
    for idx in key_candles:
        range_data = range_calculator.calculate_range(
            data, 
            idx, 
            None,  # detection_id
            params
        )
        
        # Añadir el índice para referencia
        range_data['index'] = idx
        range_data['timestamp'] = data['timestamp'].iloc[idx]
        
        ranges.append(range_data)
    
    # Imprimir resultados
    print(f"Rangos calculados: {len(ranges)}")
    if ranges:
        print(f"Ejemplo de rango (índice {ranges[0]['index']}):")
        for key, value in ranges[0].items():
            if key not in ['index', 'timestamp']:
                print(f"  - {key}: {value}")
    
    return ranges

def evaluate_breakouts(data, ranges, params=None):
    """Evaluar breakouts para los rangos calculados
    
    Args:
        data (pd.DataFrame): DataFrame con los datos
        ranges (list): Lista de diccionarios con los datos de los rangos
        params (dict, optional): Parámetros para la evaluación de breakouts
        
    Returns:
        list: Lista de diccionarios con los datos de los breakouts válidos
    """
    # Si no se especifican parámetros, usar valores predeterminados
    if params is None:
        params = {
            'breakout_threshold_percentage': 0.5,
            'max_candles_to_return': 3
        }
    
    print("\n=== EVALUACIÓN DE BREAKOUTS ===")
    print("Parámetros utilizados:")
    for key, value in params.items():
        print(f"  - {key}: {value}")
    
    # Crear instancia del evaluador de breakouts
    breakout_evaluator = A_Breakout()
    
    # Evaluar breakouts
    valid_breakouts = []
    for range_data in ranges:
        idx = range_data['index']
        
        # Verificar que hay suficientes velas después del índice
        if idx + params['max_candles_to_return'] >= len(data):
            continue
        
        is_valid, breakout_data = breakout_evaluator.evaluate_breakout(
            data, 
            idx, 
            range_data, 
            params
        )
        
        if is_valid:
            # Añadir datos adicionales
            breakout_data['range_index'] = idx
            breakout_data['breakout_index'] = breakout_data['candle_index']
            breakout_data['timestamp'] = data['timestamp'].iloc[breakout_data['candle_index']]
            
            valid_breakouts.append(breakout_data)
    
    # Imprimir resultados
    print(f"Breakouts válidos: {len(valid_breakouts)} de {len(ranges)} rangos evaluados")
    if valid_breakouts:
        print("Ejemplos de breakouts válidos:")
        for i, breakout in enumerate(valid_breakouts[:4], 1):
            print(f"  {i}. Índice: {breakout['range_index']} -> {breakout['breakout_index']}, Dirección: {breakout['direction']}, Porcentaje: {breakout['breakout_percentage']:.2f}%")
    
    return valid_breakouts

def save_to_db(detection_params, range_params, breakout_params, key_candles, ranges, valid_breakouts, data):
    """Guardar resultados en la base de datos
    
    Args:
        detection_params (dict): Parámetros de detección
        range_params (dict): Parámetros de rango
        breakout_params (dict): Parámetros de breakout
        key_candles (list): Índices de las velas clave detectadas
        ranges (list): Lista de rangos calculados
        valid_breakouts (list): Lista de breakouts válidos
        data (pd.DataFrame): DataFrame con los datos
        
    Returns:
        dict: IDs de los parámetros guardados en la base de datos
    """
    try:
        print("\n=== GUARDANDO RESULTADOS EN LA BASE DE DATOS ===")
        
        conn = get_db_connection()
        if not conn:
            print("Error: No se pudo conectar a la base de datos")
            return None
        
        cursor = conn.cursor()
        
        # 1. Guardar parámetros de detección
        try:
            query = """
            INSERT INTO A_detection_params 
            (volume_percentile_threshold, body_percentage_threshold, lookback_candles, created_at) 
            VALUES (%s, %s, %s, %s)
            """
            values = (
                float(detection_params['volume_percentile_threshold']),
                float(detection_params['body_percentage_threshold']),
                int(detection_params['lookback_candles']),
                datetime.now()
            )
            
            cursor.execute(query, values)
            detection_param_id = cursor.lastrowid
            conn.commit()
            print(f"Parámetros de detección guardados con ID: {detection_param_id}")
        except Exception as e:
            print(f"Error al guardar parámetros de detección: {e}")
            detection_param_id = None
        
        # 2. Guardar datos de detección
        detection_ids = {}
        if detection_param_id:
            try:
                for idx in key_candles:
                    # Calcular porcentaje del cuerpo
                    candle_body = abs(data['close'].iloc[idx] - data['open'].iloc[idx])
                    candle_range = data['high'].iloc[idx] - data['low'].iloc[idx]
                    body_percentage = (candle_body / candle_range * 100) if candle_range > 0 else 0
                    
                    # Convertir timestamp a datetime
                    timestamp = data['timestamp'].iloc[idx]
                    if isinstance(timestamp, pd.Timestamp):
                        timestamp = timestamp.to_pydatetime()
                    
                    query = """
                    INSERT INTO A_detection_data 
                    (timestamp, is_key_candle, volume, body_percentage, param_id, created_at) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    values = (
                        timestamp,
                        True,
                        float(data['volume'].iloc[idx]),
                        float(body_percentage),
                        detection_param_id,
                        datetime.now()
                    )
                    
                    cursor.execute(query, values)
                    detection_id = cursor.lastrowid
                    conn.commit()
                    detection_ids[idx] = detection_id
                
                print(f"Datos de detección guardados: {len(detection_ids)} registros")
            except Exception as e:
                print(f"Error al guardar datos de detección: {e}")
        
        # 3. Guardar parámetros de rango
        try:
            query = """
            INSERT INTO A_range_params 
            (atr_period, atr_multiplier, created_at) 
            VALUES (%s, %s, %s)
            """
            values = (
                int(range_params['atr_period']),
                float(range_params['atr_multiplier']),
                datetime.now()
            )
            
            cursor.execute(query, values)
            range_param_id = cursor.lastrowid
            conn.commit()
            print(f"Parámetros de rango guardados con ID: {range_param_id}")
        except Exception as e:
            print(f"Error al guardar parámetros de rango: {e}")
            range_param_id = None
        
        # 4. Guardar datos de rango
        range_ids = {}
        if range_param_id:
            try:
                for range_data in ranges:
                    # Obtener detection_id correspondiente
                    detection_id = detection_ids.get(range_data['index'])
                    
                    # Convertir timestamp a datetime
                    timestamp = range_data['timestamp']
                    if isinstance(timestamp, pd.Timestamp):
                        timestamp = timestamp.to_pydatetime()
                    
                    query = """
                    INSERT INTO A_range_data 
                    (timestamp, reference_price, upper_limit, lower_limit, atr_value, param_id, detection_id, created_at) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (
                        timestamp,
                        float(range_data['reference_price']),
                        float(range_data['upper_limit']),
                        float(range_data['lower_limit']),
                        float(range_data['atr_value']),
                        range_param_id,
                        detection_id,
                        datetime.now()
                    )
                    
                    cursor.execute(query, values)
                    range_id = cursor.lastrowid
                    conn.commit()
                    range_ids[range_data['index']] = range_id
                
                print(f"Datos de rango guardados: {len(range_ids)} registros")
            except Exception as e:
                print(f"Error al guardar datos de rango: {e}")
        
        # 5. Guardar parámetros de breakout
        try:
            query = """
            INSERT INTO A_breakout_params 
            (breakout_threshold_percentage, max_candles_to_return, created_at) 
            VALUES (%s, %s, %s)
            """
            values = (
                float(breakout_params['breakout_threshold_percentage']),
                int(breakout_params['max_candles_to_return']),
                datetime.now()
            )
            
            cursor.execute(query, values)
            breakout_param_id = cursor.lastrowid
            conn.commit()
            print(f"Parámetros de breakout guardados con ID: {breakout_param_id}")
        except Exception as e:
            print(f"Error al guardar parámetros de breakout: {e}")
            breakout_param_id = None
        
        # 6. Guardar datos de breakout
        breakout_count = 0
        if breakout_param_id:
            try:
                for breakout in valid_breakouts:
                    # Obtener range_id correspondiente
                    range_id = range_ids.get(breakout['range_index'])
                    if not range_id:
                        continue
                    
                    # Convertir timestamp a datetime
                    timestamp = breakout['timestamp']
                    if isinstance(timestamp, pd.Timestamp):
                        timestamp = timestamp.to_pydatetime()
                    
                    query = """
                    INSERT INTO A_breakout_data 
                    (timestamp, direction, breakout_percentage, is_valid, param_id, range_id, created_at) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (
                        timestamp,
                        str(breakout['direction']),
                        float(breakout['breakout_percentage']),
                        True,
                        breakout_param_id,
                        range_id,
                        datetime.now()
                    )
                    
                    cursor.execute(query, values)
                    conn.commit()
                    breakout_count += 1
                
                print(f"Datos de breakout guardados: {breakout_count} registros")
            except Exception as e:
                print(f"Error al guardar datos de breakout: {e}")
        
        cursor.close()
        conn.close()
        
        print("Todos los resultados han sido guardados en la base de datos")
        
        return {
            'detection_param_id': detection_param_id,
            'range_param_id': range_param_id,
            'breakout_param_id': breakout_param_id
        }
    
    except Exception as e:
        print(f"Error general al guardar en la base de datos: {e}")
        traceback.print_exc()
        return None

def run_A_optimizer(use_grid_search=False, save_to_database=True):
    """Ejecutar el proceso completo de A_optimizer
    
    Args:
        use_grid_search (bool): Si es True, se realizará grid search para optimizar los parámetros
        save_to_database (bool): Si es True, se guardarán los resultados en la base de datos
    """
    print("==============================================")
    print("EJECUCIÓN DEL SISTEMA A_OPTIMIZER")
    print("==============================================")
    print(f"Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Modo: {'Grid Search' if use_grid_search else 'Parámetros Predefinidos'}")
    print(f"Guardar en base de datos: {'Sí' if save_to_database else 'No'}")
    
    # Cargar datos
    data = load_data()
    if data is None:
        print("Error: No se pudieron cargar los datos. Abortando.")
        return
    
    try:
        # Parámetros para cada módulo
        detection_params = {
            'volume_percentile_threshold': 80,
            'body_percentage_threshold': 30,
            'lookback_candles': 20
        }
        
        # Detectar velas clave
        key_candles = detect_key_candles(data, detection_params)
        
        # Parámetros para el cálculo de rangos
        range_params = {
            'atr_period': 14,
            'atr_multiplier': 1.5
        }
        
        # Calcular rangos
        ranges = calculate_ranges(data, key_candles, range_params)
        
        # Parámetros para la evaluación de breakouts
        breakout_params = {
            'breakout_threshold_percentage': 0.5,
            'max_candles_to_return': 3
        }
        
        # Evaluar breakouts
        valid_breakouts = evaluate_breakouts(data, ranges, breakout_params)
        
        # Guardar resultados en la base de datos
        db_ids = None
        if save_to_database:
            db_ids = save_to_db(detection_params, range_params, breakout_params, key_candles, ranges, valid_breakouts, data)
        
        # Guardar resultados en un archivo JSON
        results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_file': 'BTCUSDC-5m-2025-04-08.csv',
            'data_rows': len(data),
            'grid_search_enabled': use_grid_search,
            'saved_to_database': save_to_database,
            'detection': {
                'params': detection_params,
                'param_id': db_ids['detection_param_id'] if db_ids else None,
                'key_candles_count': len(key_candles),
                'key_candles_percentage': len(key_candles)/(len(data) - 20)*100 if len(data) > 20 else 0
            },
            'range': {
                'params': range_params,
                'param_id': db_ids['range_param_id'] if db_ids else None,
                'ranges_calculated': len(ranges)
            },
            'breakout': {
                'params': breakout_params,
                'param_id': db_ids['breakout_param_id'] if db_ids else None,
                'valid_breakouts': len(valid_breakouts),
                'breakout_percentage': len(valid_breakouts)/len(ranges)*100 if ranges else 0
            }
        }
        
        # Guardar resultados en un archivo JSON
        with open('A_optimizer_results_db.json', 'w') as f:
            json.dump(results, f, indent=4)
        
        print(f"\nResultados guardados en: A_optimizer_results_db.json")
        
        # Resumen de resultados
        print("\n=== RESUMEN DE RESULTADOS ===")
        print(f"Velas clave detectadas: {len(key_candles)}")
        print(f"Rangos calculados: {len(ranges)}")
        print(f"Breakouts válidos: {len(valid_breakouts)}")
        
        print("\n==============================================")
        print("EJECUCIÓN COMPLETADA CON ÉXITO")
        print("==============================================")
        print(f"Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"Error durante la ejecución: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        # Verificar si se debe guardar en la base de datos
        save_to_database = True
        
        # Verificar si se puede conectar a la base de datos
        conn = get_db_connection()
        if not conn:
            print("ADVERTENCIA: No se pudo conectar a la base de datos. Se ejecutará sin guardar en la base de datos.")
            save_to_database = False
        else:
            conn.close()
            print("Conexión a la base de datos exitosa.")
        
        # Ejecutar el optimizador
        run_A_optimizer(use_grid_search=False, save_to_database=save_to_database)
    except Exception as e:
        print(f"Error al ejecutar A_optimizer: {e}")
        traceback.print_exc()
