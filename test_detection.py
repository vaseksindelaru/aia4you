"""
Script simple para probar el módulo de detección
"""
import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Añadir el directorio raíz al path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Cargar variables de entorno
load_dotenv()

# Importar el módulo de detección
from actions.evolve.A_optimizer.detection import A_Detection

def main():
    print("Iniciando prueba del módulo de detección...")
    
    try:
        # Inicializar el módulo de detección
        detector = A_Detection()
        print("✓ Módulo de detección inicializado correctamente")
        
        # Cargar datos de prueba
        data_path = os.path.join('data', 'BTCUSDC-5m-2025-04-08', 'BTCUSDC-5m-2025-04-08.csv')
        if os.path.exists(data_path):
            data = pd.read_csv(data_path)
            print(f"✓ Datos cargados correctamente: {len(data)} filas")
            
            # Probar la detección de velas clave
            params = {
                'volume_percentile_threshold': 80,
                'body_percentage_threshold': 30,
                'lookback_candles': 20
            }
            
            # Detectar velas clave en los primeros 100 registros
            key_candles = []
            for i in range(min(100, len(data))):
                if detector.detect_key_candle(data, i, params):
                    key_candles.append(i)
            
            print(f"✓ Se detectaron {len(key_candles)} velas clave en los primeros 100 registros")
            if key_candles:
                print(f"✓ Índices de velas clave: {key_candles[:5]}...")
            
            # Guardar parámetros en la base de datos
            param_id = detector.save_params(params)
            print(f"✓ Parámetros guardados con ID: {param_id}")
            
            print("✅ Prueba del módulo de detección completada con éxito")
        else:
            print(f"✗ Error: No se encontró el archivo de datos en {data_path}")
    
    except Exception as e:
        print(f"✗ Error en la prueba del módulo de detección: {e}")

if __name__ == "__main__":
    main()
