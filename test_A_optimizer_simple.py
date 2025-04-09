"""
Script simplificado para probar el sistema A_optimizer
"""
import os
import sys
import pandas as pd
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

# Cargar variables de entorno
load_dotenv()

# Importar componentes A_optimizer
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from actions.evolve.A_optimizer.detection import A_Detection
from actions.evolve.A_optimizer.range import A_Range
from actions.evolve.A_optimizer.breakout import A_Breakout

def load_test_data():
    """Cargar datos de prueba"""
    try:
        data_path = os.path.join('data', 'BTCUSDC-5m-2025-04-08', 'BTCUSDC-5m-2025-04-08.csv')
        if os.path.exists(data_path):
            data = pd.read_csv(data_path)
            print(f"[OK] Datos cargados: {len(data)} filas")
            return data
        else:
            print(f"[ERROR] No se encontró el archivo de datos: {data_path}")
            return None
    except Exception as e:
        print(f"[ERROR] Error al cargar datos: {e}")
        return None

def test_detection():
    """Probar el módulo de detección"""
    print("\n===== PRUEBA DEL MÓDULO DE DETECCIÓN =====")
    
    try:
        # Inicializar detector
        detector = A_Detection()
        print("[OK] Módulo de detección inicializado")
        
        # Cargar datos
        data = load_test_data()
        if data is None:
            return False
        
        # Detectar velas clave
        params = {
            'volume_percentile_threshold': 80,
            'body_percentage_threshold': 30,
            'lookback_candles': 20
        }
        
        key_candles = []
        for i in range(min(100, len(data))):
            if detector.detect_key_candle(data, i, params):
                key_candles.append(i)
        
        print(f"[OK] Velas clave detectadas: {len(key_candles)}")
        if key_candles:
            print(f"[OK] Primeras velas clave: {key_candles[:5]}")
        
        # Guardar parámetros
        param_id = detector.save_params(params)
        print(f"[OK] Parámetros guardados con ID: {param_id}")
        
        return True
    except Exception as e:
        print(f"[ERROR] Error en la prueba de detección: {e}")
        return False

def test_range():
    """Probar el módulo de rango"""
    print("\n===== PRUEBA DEL MÓDULO DE RANGO =====")
    
    try:
        # Inicializar calculador de rango
        range_calculator = A_Range()
        print("[OK] Módulo de rango inicializado")
        
        # Cargar datos
        data = load_test_data()
        if data is None:
            return False
        
        # Calcular rango
        params = {
            'atr_period': 14,
            'atr_multiplier': 1.5
        }
        
        index = 50
        range_data = range_calculator.calculate_range(data, index, None, params)
        
        print(f"[OK] Rango calculado para índice {index}:")
        print(f"  - Precio de referencia: {range_data['reference_price']}")
        print(f"  - Límite superior: {range_data['upper_limit']}")
        print(f"  - Límite inferior: {range_data['lower_limit']}")
        
        # Guardar parámetros
        param_id = range_calculator.save_params(params)
        print(f"[OK] Parámetros guardados con ID: {param_id}")
        
        return True
    except Exception as e:
        print(f"[ERROR] Error en la prueba de rango: {e}")
        return False

def test_breakout():
    """Probar el módulo de breakout"""
    print("\n===== PRUEBA DEL MÓDULO DE BREAKOUT =====")
    
    try:
        # Inicializar evaluador de breakout
        breakout_evaluator = A_Breakout()
        print("[OK] Módulo de breakout inicializado")
        
        # Cargar datos
        data = load_test_data()
        if data is None:
            return False
        
        # Evaluar breakout
        params = {
            'breakout_threshold_percentage': 0.5,
            'max_candles_to_return': 3
        }
        
        index = 50
        range_data = {
            'reference_price': data.iloc[index]['close'],
            'upper_limit': data.iloc[index]['close'] * 1.02,
            'lower_limit': data.iloc[index]['close'] * 0.98,
            'atr_value': data.iloc[index]['high'] - data.iloc[index]['low']
        }
        
        is_valid, breakout_data = breakout_evaluator.evaluate_breakout(data, index, range_data, params)
        
        print(f"[OK] Breakout evaluado para índice {index}:")
        print(f"  - Es válido: {is_valid}")
        if is_valid:
            print(f"  - Dirección: {breakout_data['direction']}")
            print(f"  - Porcentaje: {breakout_data['breakout_percentage']}")
        
        # Guardar parámetros
        param_id = breakout_evaluator.save_params(params)
        print(f"[OK] Parámetros guardados con ID: {param_id}")
        
        return True
    except Exception as e:
        print(f"[ERROR] Error en la prueba de breakout: {e}")
        return False

def test_integration():
    """Probar la integración de los tres componentes"""
    print("\n===== PRUEBA DE INTEGRACIÓN =====")
    
    try:
        # Inicializar componentes
        detector = A_Detection()
        range_calculator = A_Range()
        breakout_evaluator = A_Breakout()
        print("[OK] Componentes inicializados")
        
        # Cargar datos
        data = load_test_data()
        if data is None:
            return False
        
        # Parámetros
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
        
        # Proceso completo
        valid_breakouts = []
        
        for i in range(min(200, len(data))):
            # Paso 1: Detectar vela clave
            is_key_candle = detector.detect_key_candle(data, i, detection_params)
            
            if is_key_candle:
                # Paso 2: Calcular rango
                detection_id = detector.save_data({
                    'timestamp': data.iloc[i]['timestamp'] if 'timestamp' in data.columns else str(i),
                    'is_key_candle': True,
                    'volume': data.iloc[i]['volume'],
                    'body_percentage': abs(data.iloc[i]['close'] - data.iloc[i]['open']) / (data.iloc[i]['high'] - data.iloc[i]['low']) * 100
                })
                
                range_data = range_calculator.calculate_range(data, i, detection_id, range_params)
                
                # Paso 3: Evaluar breakout
                is_valid, breakout_data = breakout_evaluator.evaluate_breakout(data, i, range_data, breakout_params)
                
                if is_valid:
                    valid_breakouts.append((i, breakout_data['direction']))
        
        print(f"[OK] Proceso completo ejecutado")
        print(f"[OK] Breakouts válidos encontrados: {len(valid_breakouts)}")
        if valid_breakouts:
            print(f"[OK] Primeros breakouts: {valid_breakouts[:5]}")
        
        return True
    except Exception as e:
        print(f"[ERROR] Error en la prueba de integración: {e}")
        return False

def check_database_tables():
    """Verificar tablas en la base de datos"""
    print("\n===== VERIFICACIÓN DE TABLAS EN LA BASE DE DATOS =====")
    
    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DATABASE', 'binance_lob')
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Verificar tablas
            tables_to_check = [
                'A_detection_params',
                'A_detection_data',
                'A_range_params',
                'A_range_data',
                'A_breakout_params',
                'A_breakout_data'
            ]
            
            existing_tables = []
            for table in tables_to_check:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if cursor.fetchone():
                    existing_tables.append(table)
            
            if existing_tables:
                print(f"[OK] Tablas encontradas en la base de datos:")
                for table in existing_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  - {table}: {count} registros")
            else:
                print("[ERROR] No se encontraron tablas del sistema A_optimizer")
            
            cursor.close()
            connection.close()
            
            return True
    except Error as e:
        print(f"[ERROR] Error al verificar tablas: {e}")
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")
    
    return False

def main():
    """Función principal"""
    print("==============================================")
    print("PRUEBA DEL SISTEMA A_OPTIMIZER")
    print("==============================================")
    
    # Ejecutar pruebas
    detection_result = test_detection()
    range_result = test_range()
    breakout_result = test_breakout()
    integration_result = test_integration()
    database_result = check_database_tables()
    
    # Resumen
    print("\n==============================================")
    print("RESUMEN DE PRUEBAS")
    print("==============================================")
    print(f"Módulo de Detección: {'[OK]' if detection_result else '[ERROR]'}")
    print(f"Módulo de Rango: {'[OK]' if range_result else '[ERROR]'}")
    print(f"Módulo de Breakout: {'[OK]' if breakout_result else '[ERROR]'}")
    print(f"Integración: {'[OK]' if integration_result else '[ERROR]'}")
    print(f"Base de Datos: {'[OK]' if database_result else '[ERROR]'}")
    
    if all([detection_result, range_result, breakout_result, integration_result, database_result]):
        print("\n[OK] TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
    else:
        print("\n[ERROR] ALGUNAS PRUEBAS FALLARON")
    
    print("==============================================")

if __name__ == "__main__":
    main()
