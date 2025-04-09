"""
Script minimalista para ejecutar el sistema A_optimizer
"""
import os
import sys
import pandas as pd
import numpy as np
import json
from datetime import datetime

# Parametros por defecto
DETECTION_PARAMS = {
    'volume_percentile_threshold': 80,
    'body_percentage_threshold': 30,
    'lookback_candles': 20
}

RANGE_PARAMS = {
    'atr_period': 14,
    'atr_multiplier': 1.5
}

BREAKOUT_PARAMS = {
    'breakout_threshold_percentage': 0.5,
    'max_candles_to_return': 3
}

def load_data():
    """Cargar datos de BTCUSDC"""
    print("Cargando datos...")
    
    # Buscar el archivo de datos
    data_path = None
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    for root, dirs, files in os.walk(data_dir):
        for dir_name in dirs:
            if 'BTCUSDC-5m-2025-04-08' in dir_name:
                potential_path = os.path.join(root, dir_name, 'BTCUSDC-5m-2025-04-08.csv')
                if os.path.exists(potential_path):
                    data_path = potential_path
                    break
    
    if not data_path:
        print("Error: No se encontro el archivo de datos")
        return None
    
    print(f"Archivo encontrado: {data_path}")
    
    # Leer el archivo CSV
    data = pd.read_csv(data_path, header=0)
    
    # Asignar nombres de columnas
    column_names = [
        'time',
        'open',
        'high',
        'low',
        'close',
        'volume',
        'close_time',
        'quote_asset_volume',
        'number_of_trades',
        'taker_buy_base_asset_volume',
        'taker_buy_quote_asset_volume',
        'ignore'
    ]
    
    # Ajustar la lista de nombres si es necesario
    if len(data.columns) != len(column_names):
        if len(data.columns) < len(column_names):
            column_names = column_names[:len(data.columns)]
        else:
            for i in range(len(column_names), len(data.columns)):
                column_names.append(f"column_{i+1}")
    
    # Renombrar columnas
    data.columns = column_names
    
    print(f"Datos cargados: {len(data)} filas")
    return data

def detect_key_candles(data):
    """Detectar velas clave"""
    print("Detectando velas clave...")
    
    key_candles = []
    
    # Iterar sobre las velas
    for i in range(DETECTION_PARAMS['lookback_candles'], len(data)):
        try:
            # Obtener datos de la vela actual
            candle = data.iloc[i]
            
            # Calcular percentil de volumen
            lookback_data = data.iloc[i-DETECTION_PARAMS['lookback_candles']:i]
            volume_percentile = np.percentile(lookback_data['volume'], DETECTION_PARAMS['volume_percentile_threshold'])
            
            # Verificar si el volumen supera el percentil
            is_high_volume = candle['volume'] > volume_percentile
            
            # Calcular porcentaje del cuerpo
            body_size = abs(candle['close'] - candle['open'])
            candle_range = candle['high'] - candle['low']
            body_percentage = (body_size / candle_range * 100) if candle_range > 0 else 0
            
            # Verificar si el cuerpo es pequeño
            is_small_body = body_percentage < DETECTION_PARAMS['body_percentage_threshold']
            
            # Una vela es clave si tiene alto volumen y cuerpo pequeño
            if is_high_volume and is_small_body:
                key_candles.append(i)
        except Exception as e:
            print(f"Error al procesar vela {i}: {e}")
            continue
    
    print(f"Velas clave detectadas: {len(key_candles)}")
    if key_candles:
        print(f"Primeras 5 velas clave: {key_candles[:min(5, len(key_candles))]}")
    
    return key_candles

def calculate_atr(data, period=14):
    """Calcular ATR"""
    high_low = data['high'] - data['low']
    high_close = abs(data['high'] - data['close'].shift(1))
    low_close = abs(data['low'] - data['close'].shift(1))
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr

def calculate_ranges(data, key_candles):
    """Calcular rangos dinamicos"""
    print("Calculando rangos...")
    
    if not key_candles:
        print("No hay velas clave para calcular rangos")
        return []
    
    # Calcular ATR para todo el DataFrame
    atr_values = calculate_atr(data, period=RANGE_PARAMS['atr_period'])
    
    ranges = []
    
    # Calcular rangos para cada vela clave
    for idx in key_candles:
        try:
            # Verificar que hay suficientes datos para el ATR
            if idx < RANGE_PARAMS['atr_period']:
                continue
            
            # Obtener el valor ATR para la vela actual
            atr_value = atr_values.iloc[idx]
            
            # Obtener precio de referencia (cierre de la vela clave)
            reference_price = data.iloc[idx]['close']
            
            # Calcular limites del rango
            upper_limit = reference_price + (atr_value * RANGE_PARAMS['atr_multiplier'])
            lower_limit = reference_price - (atr_value * RANGE_PARAMS['atr_multiplier'])
            
            # Crear diccionario con informacion del rango
            range_data = {
                'index': idx,
                'reference_price': reference_price,
                'upper_limit': upper_limit,
                'lower_limit': lower_limit,
                'atr_value': atr_value
            }
            
            ranges.append(range_data)
        except Exception as e:
            print(f"Error al calcular rango para indice {idx}: {e}")
            continue
    
    print(f"Rangos calculados: {len(ranges)}")
    
    if ranges:
        print(f"Ejemplo de rango (indice {ranges[0]['index']}):")
        print(f"  - Precio referencia: {ranges[0]['reference_price']}")
        print(f"  - Limite superior: {ranges[0]['upper_limit']}")
        print(f"  - Limite inferior: {ranges[0]['lower_limit']}")
    
    return ranges

def evaluate_breakouts(data, ranges):
    """Evaluar breakouts"""
    print("Evaluando breakouts...")
    
    if not ranges:
        print("No hay rangos para evaluar breakouts")
        return []
    
    valid_breakouts = []
    
    # Evaluar breakouts para cada rango
    for range_data in ranges:
        try:
            idx = range_data['index']
            max_candles = BREAKOUT_PARAMS['max_candles_to_return']
            
            # Verificar que hay suficientes velas despues del indice
            if idx + max_candles >= len(data):
                continue
            
            # Buscar breakout en las siguientes velas
            for i in range(1, max_candles + 1):
                current_idx = idx + i
                candle = data.iloc[current_idx]
                
                # Verificar breakout alcista (por encima del limite superior)
                if candle['close'] > range_data['upper_limit']:
                    breakout_percentage = ((candle['close'] - range_data['reference_price']) / range_data['reference_price']) * 100
                    
                    # Verificar si supera el umbral de porcentaje
                    if breakout_percentage > BREAKOUT_PARAMS['breakout_threshold_percentage']:
                        breakout_data = {
                            'range_index': idx,
                            'breakout_index': current_idx,
                            'direction': 'bullish',
                            'breakout_percentage': breakout_percentage,
                            'candle_close': candle['close']
                        }
                        valid_breakouts.append(breakout_data)
                        break
                
                # Verificar breakout bajista (por debajo del limite inferior)
                elif candle['close'] < range_data['lower_limit']:
                    breakout_percentage = ((range_data['reference_price'] - candle['close']) / range_data['reference_price']) * 100
                    
                    # Verificar si supera el umbral de porcentaje
                    if breakout_percentage > BREAKOUT_PARAMS['breakout_threshold_percentage']:
                        breakout_data = {
                            'range_index': idx,
                            'breakout_index': current_idx,
                            'direction': 'bearish',
                            'breakout_percentage': breakout_percentage,
                            'candle_close': candle['close']
                        }
                        valid_breakouts.append(breakout_data)
                        break
        except Exception as e:
            print(f"Error al evaluar breakout para indice {range_data['index']}: {e}")
            continue
    
    print(f"Breakouts validos: {len(valid_breakouts)}")
    
    if valid_breakouts:
        print("Ejemplos de breakouts validos:")
        for i, breakout in enumerate(valid_breakouts[:min(4, len(valid_breakouts))], 1):
            print(f"  {i}. Indice: {breakout['range_index']} -> {breakout['breakout_index']}")
            print(f"     Direccion: {breakout['direction']}")
            print(f"     Porcentaje: {breakout['breakout_percentage']:.2f}%")
    
    return valid_breakouts

def save_results(key_candles, ranges, valid_breakouts, data_rows):
    """Guardar resultados en un archivo JSON"""
    print("Guardando resultados...")
    
    results = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'data_rows': data_rows,
        'detection': {
            'params': DETECTION_PARAMS,
            'key_candles_count': len(key_candles),
            'key_candles_percentage': len(key_candles)/(data_rows - DETECTION_PARAMS['lookback_candles'])*100 if data_rows > DETECTION_PARAMS['lookback_candles'] else 0
        },
        'range': {
            'params': RANGE_PARAMS,
            'ranges_calculated': len(ranges)
        },
        'breakout': {
            'params': BREAKOUT_PARAMS,
            'valid_breakouts': len(valid_breakouts),
            'breakout_percentage': len(valid_breakouts)/len(ranges)*100 if ranges else 0,
            'breakouts': [
                {
                    'range_index': b['range_index'],
                    'breakout_index': b['breakout_index'],
                    'direction': b['direction'],
                    'percentage': b['breakout_percentage']
                } for b in valid_breakouts
            ]
        }
    }
    
    output_file = 'A_optimizer_results_minimal.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)
    
    print(f"Resultados guardados en: {output_file}")
    return output_file

def main():
    """Funcion principal"""
    print("Iniciando A_optimizer (version minimal)...")
    
    try:
        # 1. Cargar datos
        data = load_data()
        if data is None:
            return
        
        # 2. Detectar velas clave
        key_candles = detect_key_candles(data)
        
        # 3. Calcular rangos
        ranges = calculate_ranges(data, key_candles)
        
        # 4. Evaluar breakouts
        valid_breakouts = evaluate_breakouts(data, ranges)
        
        # 5. Guardar resultados
        save_results(key_candles, ranges, valid_breakouts, len(data))
        
        print("Proceso completado con exito.")
    
    except Exception as e:
        print(f"Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
