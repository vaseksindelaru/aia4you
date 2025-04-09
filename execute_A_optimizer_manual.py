"""
Script para ejecutar el sistema A_optimizer con datos reales

Este script implementa una versión optimizada del sistema A_optimizer
que incluye los tres componentes principales (detección, rango y breakout)
y mantiene la lógica de grid search sin ejecutarla directamente.
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import json
import mysql.connector
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Añadir el directorio raíz al path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

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
        data_path (str, optional): Ruta al archivo de datos CSV. Si es None, se usará el archivo por defecto.
        
    Returns:
        pandas.DataFrame: DataFrame con los datos cargados y columnas renombradas
    """
    if data_path is None:
        data_path = os.path.join('data', 'BTCUSDC-5m-2025-04-08', 'BTCUSDC-5m-2025-04-08.csv')
    
    if os.path.exists(data_path):
        print(f"Archivo encontrado: {data_path}")
        
        # Cargar datos
        data = pd.read_csv(data_path)
        print(f"Datos cargados: {len(data)} filas")
        
        # Renombrar columnas si es necesario
        if '1744070400000000' in data.columns:
            data.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                           'close_time', 'quote_volume', 'trades', 'taker_buy_volume', 
                           'taker_buy_quote_volume', 'ignored']
            print("Columnas renombradas para facilitar el procesamiento")
        
        return data
    else:
        print(f"Error: No se encontró el archivo de datos en {data_path}")
        return None

def generate_detection_grid_params(max_params=5):
    """Generar parámetros para grid search en el módulo de detección
    
    Args:
        max_params (int): Número máximo de combinaciones de parámetros a generar
        
    Returns:
        list: Lista de diccionarios con combinaciones de parámetros
    """
    # Definir rangos de parámetros
    volume_thresholds = [75, 80, 85, 90]
    body_thresholds = [20, 25, 30, 35, 40]
    lookback_periods = [15, 20, 25, 30]
    
    # Generar combinaciones (limitadas a max_params)
    param_grid = []
    for vol in volume_thresholds:
        for body in body_thresholds:
            for lookback in lookback_periods:
                param_grid.append({
                    'volume_percentile_threshold': vol,
                    'body_percentage_threshold': body,
                    'lookback_candles': lookback
                })
                if len(param_grid) >= max_params:
                    return param_grid
    
    return param_grid

def detect_key_candles(data, params=None):
    """Implementación del algoritmo de detección de velas clave
    
    Args:
        data (pandas.DataFrame): DataFrame con los datos de mercado
        params (dict, optional): Parámetros para la detección. Si es None, se usarán los valores por defecto.
        
    Returns:
        list: Lista de índices de las velas clave detectadas
    """
    print("\n=== DETECCIÓN DE VELAS CLAVE ===")
    
    # Parámetros por defecto
    if params is None:
        params = {
            'volume_percentile_threshold': 80,
            'body_percentage_threshold': 30,
            'lookback_candles': 20
        }
    
    # Extraer parámetros
    volume_percentile_threshold = params['volume_percentile_threshold']
    body_percentage_threshold = params['body_percentage_threshold']
    lookback_candles = params['lookback_candles']
    
    print(f"Parámetros utilizados:")
    print(f"  - volume_percentile_threshold: {volume_percentile_threshold}")
    print(f"  - body_percentage_threshold: {body_percentage_threshold}")
    print(f"  - lookback_candles: {lookback_candles}")
    
    # Detectar velas clave
    key_candles = []
    
    for i in range(lookback_candles, len(data)):
        # Calcular percentil de volumen
        recent_volumes = data['volume'].iloc[i-lookback_candles:i]
        volume_percentile = np.percentile(recent_volumes, volume_percentile_threshold)
        
        # Verificar si el volumen es alto
        is_high_volume = data['volume'].iloc[i] >= volume_percentile
        
        # Calcular porcentaje del cuerpo
        candle_body = abs(data['close'].iloc[i] - data['open'].iloc[i])
        candle_range = data['high'].iloc[i] - data['low'].iloc[i]
        body_percentage = (candle_body / candle_range * 100) if candle_range > 0 else 0
        
        # Verificar si el cuerpo es pequeño
        is_small_body = body_percentage <= body_percentage_threshold
        
        # Si cumple ambas condiciones, es una vela clave
        if is_high_volume and is_small_body:
            key_candles.append(i)
    
    print(f"Velas clave detectadas: {len(key_candles)} de {len(data) - lookback_candles} ({len(key_candles)/(len(data) - lookback_candles)*100:.2f}%)")
    if key_candles and len(key_candles) > 0:
        print(f"Primeras 5 velas clave: {key_candles[:5] if len(key_candles) >= 5 else key_candles}")
    
    return key_candles

def detection_grid_search(data, param_grid):
    """Realizar grid search para encontrar los mejores parámetros de detección
    
    Args:
        data (pandas.DataFrame): DataFrame con los datos de mercado
        param_grid (list): Lista de diccionarios con combinaciones de parámetros
        
    Returns:
        tuple: (Mejores parámetros, mejor puntuación)
    """
    print(f"Iniciando grid search con {len(param_grid)} combinaciones de parámetros...")
    
    best_score = -1
    best_params = None
    
    for params in param_grid:
        # Detectar velas clave con estos parámetros
        key_candles = detect_key_candles(data, params)
        
        # Calcular puntuación (porcentaje de velas clave detectadas)
        lookback = params['lookback_candles']
        score = len(key_candles) / (len(data) - lookback) * 100
        
        # Actualizar mejores parámetros si es necesario
        if score > best_score:
            best_score = score
            best_params = params
    
    print(f"\nMejores parámetros encontrados:")
    for key, value in best_params.items():
        print(f"  - {key}: {value}")
    print(f"Puntuación: {best_score:.2f}%")
    
    return best_params, best_score

def generate_range_grid_params(max_params=5):
    """Generar parámetros para grid search en el módulo de rango
    
    Args:
        max_params (int): Número máximo de combinaciones de parámetros a generar
        
    Returns:
        list: Lista de diccionarios con combinaciones de parámetros
    """
    # Definir rangos de parámetros
    atr_periods = [7, 14, 21, 28]
    atr_multipliers = [1.0, 1.5, 2.0, 2.5]
    
    # Generar combinaciones (limitadas a max_params)
    param_grid = []
    for period in atr_periods:
        for multiplier in atr_multipliers:
            param_grid.append({
                'atr_period': period,
                'atr_multiplier': multiplier
            })
            if len(param_grid) >= max_params:
                return param_grid
    
    return param_grid

def calculate_atr(data, period=14):
    """Calcular el ATR (Average True Range) para un DataFrame
    
    Args:
        data (pandas.DataFrame): DataFrame con los datos de mercado
        period (int): Período para el cálculo del ATR
        
    Returns:
        list: Lista de valores ATR
    """
    # Calcular True Range
    true_ranges = []
    for i in range(1, len(data)):
        high_low = data['high'].iloc[i] - data['low'].iloc[i]
        high_close_prev = abs(data['high'].iloc[i] - data['close'].iloc[i-1])
        low_close_prev = abs(data['low'].iloc[i] - data['close'].iloc[i-1])
        true_range = max(high_low, high_close_prev, low_close_prev)
        true_ranges.append(true_range)
    
    # Calcular ATR con media móvil simple
    atr_values = []
    for i in range(len(true_ranges)):
        if i < period - 1:
            atr = sum(true_ranges[:i+1]) / (i+1)
        else:
            atr = sum(true_ranges[i-period+1:i+1]) / period
        atr_values.append(atr)
    
    # Devolver lista de valores ATR con un 0 al principio para alinear con el DataFrame
    return [0] + atr_values

def calculate_ranges(data, key_candles, params=None):
    """Calcular rangos dinámicos basados en ATR para las velas clave
    
    Args:
        data (pandas.DataFrame): DataFrame con los datos de mercado
        key_candles (list): Lista de índices de velas clave
        params (dict, optional): Parámetros para el cálculo de rangos. Si es None, se usarán los valores por defecto.
        
    Returns:
        list: Lista de diccionarios con información de los rangos calculados
    """
    print("\n=== CÁLCULO DE RANGOS ===")
    
    # Parámetros por defecto
    if params is None:
        params = {
            'atr_period': 14,
            'atr_multiplier': 1.5
        }
    
    # Extraer parámetros
    atr_period = params['atr_period']
    atr_multiplier = params['atr_multiplier']
    
    print(f"Parámetros utilizados:")
    print(f"  - atr_period: {atr_period}")
    print(f"  - atr_multiplier: {atr_multiplier}")
    
    # Calcular ATR
    atr_values = calculate_atr(data, atr_period)
    
    # Añadir ATR al dataframe
    data['atr'] = atr_values
    
    # Calcular rangos para las velas clave
    ranges = []
    
    for idx in key_candles:
        if idx > 0:  # Asegurarse de que hay datos anteriores
            reference_price = data['close'].iloc[idx]
            atr_value = data['atr'].iloc[idx]
            
            # Calcular límites del rango
            upper_limit = reference_price + (atr_value * atr_multiplier)
            lower_limit = reference_price - (atr_value * atr_multiplier)
            
            range_data = {
                'index': idx,
                'timestamp': data['timestamp'].iloc[idx],
                'reference_price': reference_price,
                'upper_limit': upper_limit,
                'lower_limit': lower_limit,
                'atr_value': atr_value
            }
            
            ranges.append(range_data)
    
    print(f"Rangos calculados: {len(ranges)}")
    if ranges:
        print(f"Ejemplo de rango (índice {ranges[0]['index']}):")
        print(f"  - Precio de referencia: {ranges[0]['reference_price']}")
        print(f"  - Límite superior: {ranges[0]['upper_limit']}")
        print(f"  - Límite inferior: {ranges[0]['lower_limit']}")
        print(f"  - ATR: {ranges[0]['atr_value']}")
    
    return ranges

def range_grid_search(data, key_candles, param_grid):
    """Realizar grid search para encontrar los mejores parámetros de cálculo de rangos
    
    Args:
        data (pandas.DataFrame): DataFrame con los datos de mercado
        key_candles (list): Lista de índices de velas clave
        param_grid (list): Lista de diccionarios con combinaciones de parámetros
        
    Returns:
        tuple: (Mejores parámetros, mejor puntuación)
    """
    print(f"Iniciando grid search con {len(param_grid)} combinaciones de parámetros...")
    
    best_score = -1
    best_params = None
    
    for params in param_grid:
        # Calcular rangos con estos parámetros
        ranges = calculate_ranges(data.copy(), key_candles, params)
        
        # Calcular puntuación (cobertura de rango)
        if ranges:
            # Calcular cobertura promedio (diferencia entre límites superior e inferior dividida por el precio de referencia)
            coverage = sum([(r['upper_limit'] - r['lower_limit']) / r['reference_price'] for r in ranges]) / len(ranges)
            score = coverage * 100
            
            # Actualizar mejores parámetros si es necesario
            if score > best_score:
                best_score = score
                best_params = params
    
    if best_params:
        print(f"\nMejores parámetros encontrados:")
        for key, value in best_params.items():
            print(f"  - {key}: {value}")
        print(f"Puntuación: {best_score:.2f}%")
    else:
        print("No se encontraron parámetros válidos")
    
    return best_params, best_score

def generate_breakout_grid_params(max_params=5):
    """Generar parámetros para grid search en el módulo de breakout
    
    Args:
        max_params (int): Número máximo de combinaciones de parámetros a generar
        
    Returns:
        list: Lista de diccionarios con combinaciones de parámetros
    """
    # Definir rangos de parámetros
    threshold_percentages = [0.3, 0.5, 0.7, 1.0]
    max_candles = [1, 2, 3, 5]
    
    # Generar combinaciones (limitadas a max_params)
    param_grid = []
    for threshold in threshold_percentages:
        for candles in max_candles:
            param_grid.append({
                'breakout_threshold_percentage': threshold,
                'max_candles_to_return': candles
            })
            if len(param_grid) >= max_params:
                return param_grid
    
    return param_grid

def evaluate_breakouts(data, ranges, params=None):
    """Evaluar breakouts para los rangos calculados
    
    Args:
        data (pandas.DataFrame): DataFrame con los datos de mercado
        ranges (list): Lista de diccionarios con información de los rangos
        params (dict, optional): Parámetros para la evaluación de breakouts. Si es None, se usarán los valores por defecto.
        
    Returns:
        list: Lista de diccionarios con información de los breakouts válidos
    """
    print("\n=== EVALUACIÓN DE BREAKOUTS ===")
    
    # Parámetros por defecto
    if params is None:
        params = {
            'breakout_threshold_percentage': 0.5,
            'max_candles_to_return': 3
        }
    
    # Extraer parámetros
    breakout_threshold_percentage = params['breakout_threshold_percentage']
    max_candles_to_return = params['max_candles_to_return']
    
    print(f"Parámetros utilizados:")
    print(f"  - breakout_threshold_percentage: {breakout_threshold_percentage}")
    print(f"  - max_candles_to_return: {max_candles_to_return}")
    
    # Evaluar breakouts
    valid_breakouts = []
    
    for range_data in ranges:
        idx = range_data['index']
        
        # Buscar breakouts en las siguientes velas (hasta max_candles_to_return)
        for j in range(idx + 1, min(idx + 1 + max_candles_to_return, len(data))):
            # Verificar si el precio ha roto el rango
            close_price = data['close'].iloc[j]
            
            # Calcular porcentaje de ruptura
            if close_price > range_data['upper_limit']:
                # Breakout alcista
                breakout_percentage = (close_price - range_data['upper_limit']) / range_data['atr_value'] * 100
                direction = 'up'
            elif close_price < range_data['lower_limit']:
                # Breakout bajista
                breakout_percentage = (range_data['lower_limit'] - close_price) / range_data['atr_value'] * 100
                direction = 'down'
            else:
                # No hay breakout
                continue
            
            # Verificar si el breakout supera el umbral
            if breakout_percentage >= breakout_threshold_percentage:
                breakout_data = {
                    'range_index': idx,
                    'breakout_index': j,
                    'direction': direction,
                    'breakout_percentage': breakout_percentage,
                    'timestamp': data['timestamp'].iloc[j]
                }
                
                valid_breakouts.append(breakout_data)
                break  # Solo considerar el primer breakout válido
    
    print(f"Breakouts válidos: {len(valid_breakouts)} de {len(ranges)} rangos evaluados")
    if valid_breakouts:
        print(f"Ejemplos de breakouts válidos:")
        for i, breakout in enumerate(valid_breakouts[:5]):
            print(f"  {i+1}. Índice: {breakout['range_index']} -> {breakout['breakout_index']}, Dirección: {breakout['direction']}, Porcentaje: {breakout['breakout_percentage']:.2f}%")
    
    return valid_breakouts

def breakout_grid_search(data, ranges, param_grid):
    """Realizar grid search para encontrar los mejores parámetros de evaluación de breakouts
    
    Args:
        data (pandas.DataFrame): DataFrame con los datos de mercado
        ranges (list): Lista de diccionarios con información de los rangos
        param_grid (list): Lista de diccionarios con combinaciones de parámetros
        
    Returns:
        tuple: (Mejores parámetros, mejor puntuación)
    """
    print(f"Iniciando grid search con {len(param_grid)} combinaciones de parámetros...")
    
    best_score = -1
    best_params = None
    
    for params in param_grid:
        # Evaluar breakouts con estos parámetros
        valid_breakouts = evaluate_breakouts(data, ranges, params)
        
        # Calcular puntuación (ratio de breakouts válidos)
        if ranges:
            score = len(valid_breakouts) / len(ranges) * 100
            
            # Actualizar mejores parámetros si es necesario
            if score > best_score:
                best_score = score
                best_params = params
    
    if best_params:
        print(f"\nMejores parámetros encontrados:")
        for key, value in best_params.items():
            print(f"  - {key}: {value}")
        print(f"Puntuación: {best_score:.2f}%")
    else:
        print("No se encontraron parámetros válidos")
    
    return best_params, best_score

def save_detection_params(params):
    """Guardar parámetros de detección en la base de datos
    
    Args:
        params (dict): Parámetros de detección
        
    Returns:
        int: ID del registro insertado o None si hay error
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        query = """
        INSERT INTO A_detection_params 
        (volume_percentile_threshold, body_percentage_threshold, lookback_candles, created_at) 
        VALUES (%s, %s, %s, %s)
        """
        values = (
            params['volume_percentile_threshold'],
            params['body_percentage_threshold'],
            params['lookback_candles'],
            datetime.now()
        )
        
        cursor.execute(query, values)
        param_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Parámetros de detección guardados con ID: {param_id}")
        return param_id
    
    except mysql.connector.Error as err:
        print(f"Error al guardar parámetros de detección: {err}")
        if conn.is_connected():
            conn.close()
        return None

def save_detection_data(data_dict, param_id):
    """Guardar datos de detección en la base de datos
    
    Args:
        data_dict (dict): Datos de la vela clave detectada
        param_id (int): ID de los parámetros utilizados
        
    Returns:
        int: ID del registro insertado o None si hay error
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        # Convertir timestamp a datetime si es necesario
        timestamp = data_dict['timestamp']
        if isinstance(timestamp, pd.Timestamp):
            timestamp = timestamp.to_pydatetime()
        elif isinstance(timestamp, str):
            timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        
        # Asegurar que los valores numéricos sean del tipo correcto
        volume = float(data_dict['volume'])
        body_percentage = float(data_dict['body_percentage'])
        
        cursor = conn.cursor()
        query = """
        INSERT INTO A_detection_data 
        (timestamp, is_key_candle, volume, body_percentage, param_id, created_at) 
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            timestamp,
            bool(data_dict['is_key_candle']),
            volume,
            body_percentage,
            int(param_id),
            datetime.now()
        )
        
        print(f"Guardando datos de detección: {values}")
        cursor.execute(query, values)
        data_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        return data_id
    
    except mysql.connector.Error as err:
        print(f"Error al guardar datos de detección: {err}")
        print(f"Datos: {data_dict}")
        if conn.is_connected():
            conn.close()
        return None

def save_range_params(params):
    """Guardar parámetros de rango en la base de datos
    
    Args:
        params (dict): Parámetros de cálculo de rango
        
    Returns:
        int: ID del registro insertado o None si hay error
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        query = """
        INSERT INTO A_range_params 
        (atr_period, atr_multiplier, created_at) 
        VALUES (%s, %s, %s)
        """
        values = (
            params['atr_period'],
            params['atr_multiplier'],
            datetime.now()
        )
        
        cursor.execute(query, values)
        param_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Parámetros de rango guardados con ID: {param_id}")
        return param_id
    
    except mysql.connector.Error as err:
        print(f"Error al guardar parámetros de rango: {err}")
        if conn.is_connected():
            conn.close()
        return None

def save_range_data(data_dict, param_id, detection_id=None):
    """Guardar datos de rango en la base de datos
    
    Args:
        data_dict (dict): Datos del rango calculado
        param_id (int): ID de los parámetros utilizados
        detection_id (int, optional): ID del registro de detección relacionado
        
    Returns:
        int: ID del registro insertado o None si hay error
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        # Convertir timestamp a datetime si es necesario
        timestamp = data_dict['timestamp']
        if isinstance(timestamp, pd.Timestamp):
            timestamp = timestamp.to_pydatetime()
        elif isinstance(timestamp, str):
            timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        
        # Asegurar que los valores numéricos sean del tipo correcto
        reference_price = float(data_dict['reference_price'])
        upper_limit = float(data_dict['upper_limit'])
        lower_limit = float(data_dict['lower_limit'])
        atr_value = float(data_dict['atr_value'])
        
        cursor = conn.cursor()
        query = """
        INSERT INTO A_range_data 
        (timestamp, reference_price, upper_limit, lower_limit, atr_value, param_id, detection_id, created_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            timestamp,
            reference_price,
            upper_limit,
            lower_limit,
            atr_value,
            int(param_id),
            int(detection_id) if detection_id is not None else None,
            datetime.now()
        )
        
        print(f"Guardando datos de rango: {values}")
        cursor.execute(query, values)
        data_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        return data_id
    
    except mysql.connector.Error as err:
        print(f"Error al guardar datos de rango: {err}")
        print(f"Datos: {data_dict}")
        if conn.is_connected():
            conn.close()
        return None

def save_breakout_params(params):
    """Guardar parámetros de breakout en la base de datos
    
    Args:
        params (dict): Parámetros de evaluación de breakout
        
    Returns:
        int: ID del registro insertado o None si hay error
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        query = """
        INSERT INTO A_breakout_params 
        (breakout_threshold_percentage, max_candles_to_return, created_at) 
        VALUES (%s, %s, %s)
        """
        values = (
            params['breakout_threshold_percentage'],
            params['max_candles_to_return'],
            datetime.now()
        )
        
        cursor.execute(query, values)
        param_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Parámetros de breakout guardados con ID: {param_id}")
        return param_id
    
    except mysql.connector.Error as err:
        print(f"Error al guardar parámetros de breakout: {err}")
        if conn.is_connected():
            conn.close()
        return None

def save_breakout_data(data_dict, param_id, range_id=None):
    """Guardar datos de breakout en la base de datos
    
    Args:
        data_dict (dict): Datos del breakout evaluado
        param_id (int): ID de los parámetros utilizados
        range_id (int, optional): ID del registro de rango relacionado
        
    Returns:
        int: ID del registro insertado o None si hay error
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        # Convertir timestamp a datetime si es necesario
        timestamp = data_dict['timestamp']
        if isinstance(timestamp, pd.Timestamp):
            timestamp = timestamp.to_pydatetime()
        elif isinstance(timestamp, str):
            timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        
        # Asegurar que los valores sean del tipo correcto
        direction = str(data_dict['direction'])
        breakout_percentage = float(data_dict['breakout_percentage'])
        is_valid = bool(data_dict['is_valid'])
        
        cursor = conn.cursor()
        query = """
        INSERT INTO A_breakout_data 
        (timestamp, direction, breakout_percentage, is_valid, param_id, range_id, created_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            timestamp,
            direction,
            breakout_percentage,
            is_valid,
            int(param_id),
            int(range_id) if range_id is not None else None,
            datetime.now()
        )
        
        print(f"Guardando datos de breakout: {values}")
        cursor.execute(query, values)
        data_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        return data_id
    
    except mysql.connector.Error as err:
        print(f"Error al guardar datos de breakout: {err}")
        print(f"Datos: {data_dict}")
        if conn.is_connected():
            conn.close()
        return None

def save_results_to_db(detection_params, range_params, breakout_params, key_candles, ranges, valid_breakouts, data):
    """Guardar los resultados en la base de datos
    
    Args:
        detection_params (dict): Parámetros de detección
        range_params (dict): Parámetros de rango
        breakout_params (dict): Parámetros de breakout
        key_candles (list): Índices de las velas clave detectadas
        ranges (list): Datos de los rangos calculados
        valid_breakouts (list): Datos de los breakouts válidos
        data (pd.DataFrame): Datos de las velas
    """
    try:
        print("\n=== GUARDANDO RESULTADOS EN LA BASE DE DATOS ===")
        
        # 1. Guardar parámetros de detección
        conn = get_db_connection()
        if not conn:
            print("Error: No se pudo conectar a la base de datos")
            return
        
        cursor = conn.cursor()
        
        # Insertar parámetros de detección
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
        
        # 2. Guardar datos de detección
        detection_ids = {}
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
        
        # 3. Guardar parámetros de rango
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
        
        # 4. Guardar datos de rango
        range_ids = {}
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
        
        # 5. Guardar parámetros de breakout
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
        
        # 6. Guardar datos de breakout
        breakout_count = 0
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
        
        cursor.close()
        conn.close()
        
        print("Todos los resultados han sido guardados en la base de datos")
        
        return {
            'detection_param_id': detection_param_id,
            'range_param_id': range_param_id,
            'breakout_param_id': breakout_param_id
        }
        
    except Exception as e:
        print(f"Error al guardar resultados en la base de datos: {e}")
        import traceback
        traceback.print_exc()
        return None

def run_A_optimizer(use_grid_search=False):
    """Ejecutar el proceso completo de A_optimizer
    
    Args:
        use_grid_search (bool): Si es True, se realizará grid search para optimizar los parámetros
    """
    print("==============================================")
    print("EJECUCIÓN DEL SISTEMA A_OPTIMIZER")
    print("==============================================")
    print(f"Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Modo: {'Grid Search' if use_grid_search else 'Parámetros Predefinidos'}")
    
    # Cargar datos
    data = load_data()
    if data is None:
        print("Error: No se pudieron cargar los datos. Abortando.")
        return
    
    try:
        # Parámetros para cada módulo
        detection_params = None
        range_params = None
        breakout_params = None
        
        # Detectar velas clave
        if use_grid_search:
            print("\n--- OPTIMIZACIÓN DE PARÁMETROS DE DETECCIÓN ---")
            param_grid = generate_detection_grid_params(max_params=10)
            detection_params, _ = detection_grid_search(data, param_grid)
        else:
            detection_params = {
                'volume_percentile_threshold': 80,
                'body_percentage_threshold': 30,
                'lookback_candles': 20
            }
        
        # Detectar velas clave
        key_candles = detect_key_candles(data, detection_params)
        
        # Calcular rangos
        if use_grid_search and key_candles:
            print("\n--- OPTIMIZACIÓN DE PARÁMETROS DE RANGO ---")
            param_grid = generate_range_grid_params(max_params=10)
            range_params, _ = range_grid_search(data, key_candles, param_grid)
        else:
            range_params = {
                'atr_period': 14,
                'atr_multiplier': 1.5
            }
        
        # Calcular rangos
        ranges = calculate_ranges(data, key_candles, range_params)
        
        # Evaluar breakouts
        if use_grid_search and ranges:
            print("\n--- OPTIMIZACIÓN DE PARÁMETROS DE BREAKOUT ---")
            param_grid = generate_breakout_grid_params(max_params=10)
            breakout_params, _ = breakout_grid_search(data, ranges, param_grid)
        else:
            breakout_params = {
                'breakout_threshold_percentage': 0.5,
                'max_candles_to_return': 3
            }
        
        # Evaluar breakouts
        valid_breakouts = evaluate_breakouts(data, ranges, breakout_params)
        
        # Guardar resultados en la base de datos
        db_ids = save_results_to_db(detection_params, range_params, breakout_params, key_candles, ranges, valid_breakouts, data)
        
        # Guardar resultados en un archivo JSON
        results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_file': 'BTCUSDC-5m-2025-04-08.csv',
            'data_rows': len(data),
            'grid_search_enabled': use_grid_search,
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
        
        results_file = 'A_optimizer_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=4)
        
        print(f"\nResultados guardados en: {results_file}")
        
        print("\n=== RESUMEN DE RESULTADOS ===")
        print(f"Velas clave detectadas: {len(key_candles)}")
        print(f"Rangos calculados: {len(ranges)}")
        print(f"Breakouts válidos: {len(valid_breakouts)}")
        
        print("\n==============================================")
        print("EJECUCIÓN COMPLETADA CON ÉXITO")
        print("==============================================")
        print(f"Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\nError durante la ejecución: {e}")
        import traceback
        traceback.print_exc()
        print("==============================================")
        print("EJECUCIÓN FALLIDA")
        print("==============================================")

if __name__ == "__main__":
    try:
        run_A_optimizer(use_grid_search=False)
    except Exception as e:
        import traceback
        print(f"Error al ejecutar A_optimizer: {e}")
        traceback.print_exc()
