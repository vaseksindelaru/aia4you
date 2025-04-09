import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import json

# Añadir el directorio raíz al path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Importar módulos de A_optimizer
from actions.evolve.A_optimizer.detection import A_Detection
from actions.evolve.A_optimizer.range import A_Range
from actions.evolve.A_optimizer.breakout import A_Breakout

def load_data(data_path=None):
    """Cargar y preparar los datos para el análisis"""
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

def run_A_optimizer():
    """Ejecutar el proceso completo de A_optimizer"""
    print("==============================================")
    print("EJECUCION DEL SISTEMA A_OPTIMIZER (MINIMAL)")
    print("==============================================")
    print(f"Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
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
        
        print("\n=== DETECCION DE VELAS CLAVE ===")
        print("Parámetros utilizados:")
        for key, value in detection_params.items():
            print(f"  - {key}: {value}")
        
        # Crear instancia del detector
        detector = A_Detection()
        
        # Detectar velas clave
        key_candles = []
        for i in range(detection_params['lookback_candles'], len(data)):
            is_key_candle = detector.detect_key_candle(
                data, 
                i, 
                detection_params
            )
            
            if is_key_candle:
                key_candles.append(i)
        
        # Imprimir resultados
        print(f"Velas clave detectadas: {len(key_candles)} de {len(data) - detection_params['lookback_candles']} ({len(key_candles)/(len(data) - detection_params['lookback_candles'])*100:.2f}%)")
        if key_candles:
            print(f"Primeras 5 velas clave: {key_candles[:5]}")
        
        # Parámetros para el cálculo de rangos
        range_params = {
            'atr_period': 14,
            'atr_multiplier': 1.5
        }
        
        print("\n=== CALCULO DE RANGOS ===")
        print("Parámetros utilizados:")
        for key, value in range_params.items():
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
                range_params
            )
            
            # Añadir el índice para referencia
            range_data['index'] = idx
            
            ranges.append(range_data)
        
        # Imprimir resultados
        print(f"Rangos calculados: {len(ranges)}")
        if ranges:
            print(f"Ejemplo de rango (indice {ranges[0]['index']}):")
            for key, value in ranges[0].items():
                if key != 'index':
                    print(f"  - {key}: {value}")
        
        # Parámetros para la evaluación de breakouts
        breakout_params = {
            'breakout_threshold_percentage': 0.5,
            'max_candles_to_return': 3
        }
        
        print("\n=== EVALUACION DE BREAKOUTS ===")
        print("Parámetros utilizados:")
        for key, value in breakout_params.items():
            print(f"  - {key}: {value}")
        
        # Crear instancia del evaluador de breakouts
        breakout_evaluator = A_Breakout()
        
        # Evaluar breakouts
        valid_breakouts = []
        for range_data in ranges:
            idx = range_data['index']
            
            # Verificar que hay suficientes velas después del índice
            if idx + breakout_params['max_candles_to_return'] >= len(data):
                continue
            
            is_valid, breakout_data = breakout_evaluator.evaluate_breakout(
                data, 
                idx, 
                range_data, 
                breakout_params
            )
            
            if is_valid:
                # Añadir datos adicionales
                breakout_data['range_index'] = idx
                breakout_data['breakout_index'] = breakout_data['candle_index']
                
                valid_breakouts.append(breakout_data)
        
        # Imprimir resultados
        print(f"Breakouts validos: {len(valid_breakouts)} de {len(ranges)} rangos evaluados")
        if valid_breakouts:
            print("Ejemplos de breakouts validos:")
            for i, breakout in enumerate(valid_breakouts[:4], 1):
                print(f"  {i}. Indice: {breakout['range_index']} -> {breakout['breakout_index']}, Direccion: {breakout['direction']}, Porcentaje: {breakout['breakout_percentage']:.2f}%")
        
        # Guardar resultados en un archivo JSON
        results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_file': 'BTCUSDC-5m-2025-04-08.csv',
            'data_rows': len(data),
            'detection': {
                'params': detection_params,
                'key_candles_count': len(key_candles),
                'key_candles_percentage': len(key_candles)/(len(data) - 20)*100 if len(data) > 20 else 0
            },
            'range': {
                'params': range_params,
                'ranges_calculated': len(ranges)
            },
            'breakout': {
                'params': breakout_params,
                'valid_breakouts': len(valid_breakouts),
                'breakout_percentage': len(valid_breakouts)/len(ranges)*100 if ranges else 0
            }
        }
        
        # Guardar resultados en un archivo JSON
        with open('A_optimizer_results_minimal.json', 'w') as f:
            json.dump(results, f, indent=4)
        
        print(f"\nResultados guardados en: A_optimizer_results_minimal.json")
        
        # Resumen de resultados
        print("\n=== RESUMEN DE RESULTADOS ===")
        print(f"Velas clave detectadas: {len(key_candles)}")
        print(f"Rangos calculados: {len(ranges)}")
        print(f"Breakouts validos: {len(valid_breakouts)}")
        
        print("\n==============================================")
        print("EJECUCION COMPLETADA CON EXITO")
        print("==============================================")
        print(f"Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"Error durante la ejecucion: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        run_A_optimizer()
    except Exception as e:
        print(f"Error al ejecutar A_optimizer: {e}")
        import traceback
        traceback.print_exc()
