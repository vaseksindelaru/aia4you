import os
import sys
import pandas as pd
import json
from datetime import datetime

# Anadir el directorio raiz al path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def main():
    print("Iniciando A_optimizer en modo basico...")
    
    # 1. Cargar datos
    print("\nCargando datos...")
    try:
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        data_path = None
        
        for root, dirs, files in os.walk(data_dir):
            for dir_name in dirs:
                if 'BTCUSDC-5m-2025-04-08' in dir_name:
                    data_path = os.path.join(root, dir_name, 'BTCUSDC-5m-2025-04-08.csv')
                    print(f"Archivo encontrado: {data_path}")
                    break
        
        if data_path is None or not os.path.exists(data_path):
            print("Error: No se encontro el archivo de datos.")
            return
        
        data = pd.read_csv(data_path)
        print(f"Datos cargados: {len(data)} filas")
        
        if 'time' in data.columns and 'timestamp' not in data.columns:
            data['timestamp'] = pd.to_datetime(data['time'])
            print("Columnas renombradas para facilitar el procesamiento")
    
    except Exception as e:
        print(f"Error al cargar datos: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. Importar modulos
    print("\nImportando modulos...")
    try:
        from actions.evolve.A_optimizer.detection import A_Detection
        from actions.evolve.A_optimizer.range import A_Range
        from actions.evolve.A_optimizer.breakout import A_Breakout
        print("Modulos importados correctamente")
    except Exception as e:
        print(f"Error al importar modulos: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Parametros
    detection_params = {
        'volume_percentile_threshold': 80,
        'body_percentage_threshold': 30,
        'lookback_candles': 20
    }
    
    range_params = {
        'atr_period': 14,
        'atr_multiplier': 1.5
    }
    
    breakout_params = {
        'breakout_threshold_percentage': 0.5,
        'max_candles_to_return': 3
    }
    
    # 4. Deteccion de velas clave
    print("\nDetectando velas clave...")
    try:
        detector = A_Detection()
        key_candles = []
        
        for i in range(detection_params['lookback_candles'], len(data)):
            is_key_candle = detector.detect_key_candle(data, i, detection_params)
            if is_key_candle:
                key_candles.append(i)
        
        print(f"Velas clave detectadas: {len(key_candles)}")
    except Exception as e:
        print(f"Error en deteccion: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 5. Calculo de rangos
    print("\nCalculando rangos...")
    try:
        range_calculator = A_Range()
        ranges = []
        
        for idx in key_candles:
            range_data = range_calculator.calculate_range(data, idx, None, range_params)
            range_data['index'] = idx
            ranges.append(range_data)
        
        print(f"Rangos calculados: {len(ranges)}")
    except Exception as e:
        print(f"Error en calculo de rangos: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 6. Evaluacion de breakouts
    print("\nEvaluando breakouts...")
    try:
        breakout_evaluator = A_Breakout()
        valid_breakouts = []
        
        for range_data in ranges:
            idx = range_data['index']
            
            if idx + breakout_params['max_candles_to_return'] >= len(data):
                continue
            
            is_valid, breakout_data = breakout_evaluator.evaluate_breakout(
                data, idx, range_data, breakout_params
            )
            
            if is_valid:
                breakout_data['range_index'] = idx
                breakout_data['breakout_index'] = breakout_data['candle_index']
                valid_breakouts.append(breakout_data)
        
        print(f"Breakouts validos: {len(valid_breakouts)}")
    except Exception as e:
        print(f"Error en evaluacion de breakouts: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 7. Guardar resultados
    print("\nGuardando resultados...")
    try:
        results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_file': 'BTCUSDC-5m-2025-04-08.csv',
            'data_rows': len(data),
            'detection': {
                'params': detection_params,
                'key_candles_count': len(key_candles)
            },
            'range': {
                'params': range_params,
                'ranges_calculated': len(ranges)
            },
            'breakout': {
                'params': breakout_params,
                'valid_breakouts': len(valid_breakouts)
            }
        }
        
        with open('A_optimizer_results_basic.json', 'w') as f:
            json.dump(results, f, indent=4)
        
        print("Resultados guardados en A_optimizer_results_basic.json")
    except Exception as e:
        print(f"Error al guardar resultados: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nProceso completado.")

if __name__ == "__main__":
    main()
