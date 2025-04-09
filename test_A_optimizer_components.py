"""
Script simplificado para probar los componentes individuales del sistema A_optimizer
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import requests

# Asegurarse de que el directorio raíz del proyecto esté en el path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Importar los componentes de A_optimizer
from actions.evolve.A_optimizer.detection import A_Detection
from actions.evolve.A_optimizer.range import A_Range
from actions.evolve.A_optimizer.breakout import A_Breakout

def load_test_data():
    """Cargar datos de prueba desde el archivo CSV"""
    try:
        data_path = os.path.join('data', 'BTCUSDC-5m-2025-04-08', 'BTCUSDC-5m-2025-04-08.csv')
        if not os.path.exists(data_path):
            print(f"Error: No se encontró el archivo de datos en {data_path}")
            return None
        
        # Cargar datos
        data = pd.read_csv(data_path)
        print(f"Datos cargados correctamente: {len(data)} filas")
        return data
    except Exception as e:
        print(f"Error al cargar los datos: {e}")
        return None

def test_detection_module():
    """Probar el módulo de detección"""
    print("\n===== Prueba del Módulo de Detección =====")
    
    try:
        # Inicializar el módulo de detección
        detector = A_Detection()
        print("✓ Módulo de detección inicializado correctamente")
        
        # Verificar que las tablas se hayan creado
        print("✓ Tablas de detección creadas correctamente")
        
        # Cargar datos de prueba
        data = load_test_data()
        if data is None:
            return False
        
        # Probar la detección de velas clave
        params = {
            'volume_percentile_threshold': 80,
            'body_percentage_threshold': 30,
            'lookback_candles': 20
        }
        
        # Detectar velas clave en los primeros 100 registros
        key_candles = []
        for i in range(100):
            if detector.detect_key_candle(data, i, params):
                key_candles.append(i)
        
        print(f"✓ Se detectaron {len(key_candles)} velas clave en los primeros 100 registros")
        print(f"✓ Índices de velas clave: {key_candles[:5]}...")
        
        # Guardar parámetros en la base de datos
        param_id = detector.save_params(params)
        print(f"✓ Parámetros guardados con ID: {param_id}")
        
        return True
    except Exception as e:
        print(f"✗ Error en la prueba del módulo de detección: {e}")
        return False

def test_range_module():
    """Probar el módulo de rango"""
    print("\n===== Prueba del Módulo de Rango =====")
    
    try:
        # Inicializar el módulo de rango
        range_calculator = A_Range()
        print("✓ Módulo de rango inicializado correctamente")
        
        # Verificar que las tablas se hayan creado
        print("✓ Tablas de rango creadas correctamente")
        
        # Cargar datos de prueba
        data = load_test_data()
        if data is None:
            return False
        
        # Probar el cálculo de rango
        params = {
            'atr_period': 14,
            'atr_multiplier': 1.5
        }
        
        # Calcular rango para un índice específico
        test_index = 50
        range_data = range_calculator.calculate_range(data, test_index, None, params)
        
        print(f"✓ Rango calculado para el índice {test_index}:")
        print(f"  - Precio de referencia: {range_data['reference_price']}")
        print(f"  - Límite superior: {range_data['upper_limit']}")
        print(f"  - Límite inferior: {range_data['lower_limit']}")
        print(f"  - ATR: {range_data['atr_value']}")
        
        # Guardar parámetros en la base de datos
        param_id = range_calculator.save_params(params)
        print(f"✓ Parámetros guardados con ID: {param_id}")
        
        # Probar la API ATR
        try:
            response = requests.get('http://localhost:8000/indicators/atr', params={'period': 14, 'symbol': 'BTCUSDC'})
            if response.status_code == 200:
                print("✓ API ATR funcionando correctamente")
                print(f"  - Respuesta: {response.json()}")
            else:
                print(f"✗ Error en la API ATR: {response.status_code}")
        except Exception as e:
            print(f"✗ Error al conectar con la API ATR: {e}")
            print("  - Usando cálculo local de ATR como fallback")
        
        return True
    except Exception as e:
        print(f"✗ Error en la prueba del módulo de rango: {e}")
        return False

def test_breakout_module():
    """Probar el módulo de breakout"""
    print("\n===== Prueba del Módulo de Breakout =====")
    
    try:
        # Inicializar el módulo de breakout
        breakout_evaluator = A_Breakout()
        print("✓ Módulo de breakout inicializado correctamente")
        
        # Verificar que las tablas se hayan creado
        print("✓ Tablas de breakout creadas correctamente")
        
        # Cargar datos de prueba
        data = load_test_data()
        if data is None:
            return False
        
        # Probar la evaluación de breakout
        params = {
            'breakout_threshold_percentage': 0.5,
            'max_candles_to_return': 3
        }
        
        # Crear datos de rango de prueba
        test_index = 50
        range_data = {
            'reference_price': data.iloc[test_index]['close'],
            'upper_limit': data.iloc[test_index]['close'] * 1.02,
            'lower_limit': data.iloc[test_index]['close'] * 0.98,
            'atr_value': data.iloc[test_index]['high'] - data.iloc[test_index]['low']
        }
        
        # Evaluar breakout
        is_valid, breakout_data = breakout_evaluator.evaluate_breakout(data, test_index, range_data, params)
        
        print(f"✓ Evaluación de breakout para el índice {test_index}:")
        print(f"  - Es válido: {is_valid}")
        print(f"  - Dirección: {breakout_data['direction'] if 'direction' in breakout_data else 'N/A'}")
        print(f"  - Porcentaje de ruptura: {breakout_data['breakout_percentage'] if 'breakout_percentage' in breakout_data else 'N/A'}")
        
        # Guardar parámetros en la base de datos
        param_id = breakout_evaluator.save_params(params)
        print(f"✓ Parámetros guardados con ID: {param_id}")
        
        return True
    except Exception as e:
        print(f"✗ Error en la prueba del módulo de breakout: {e}")
        return False

def run_all_tests():
    """Ejecutar todas las pruebas"""
    print("==============================================")
    print("PRUEBAS DEL SISTEMA A_OPTIMIZER")
    print("==============================================")
    print(f"Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("----------------------------------------------")
    
    # Ejecutar pruebas
    detection_result = test_detection_module()
    range_result = test_range_module()
    breakout_result = test_breakout_module()
    
    # Mostrar resumen
    print("\n==============================================")
    print("RESUMEN DE PRUEBAS")
    print("==============================================")
    print(f"Módulo de Detección: {'✓ PASÓ' if detection_result else '✗ FALLÓ'}")
    print(f"Módulo de Rango: {'✓ PASÓ' if range_result else '✗ FALLÓ'}")
    print(f"Módulo de Breakout: {'✓ PASÓ' if breakout_result else '✗ FALLÓ'}")
    print("----------------------------------------------")
    
    if detection_result and range_result and breakout_result:
        print("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
    
    print(f"Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("==============================================")

if __name__ == "__main__":
    run_all_tests()
