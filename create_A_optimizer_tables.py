import os
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'binance_lob')
}

def create_tables():
    """Crear las tablas necesarias para el sistema A_optimizer"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Tabla para parámetros de detección
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS A_detection_params (
            id INT AUTO_INCREMENT PRIMARY KEY,
            volume_percentile_threshold FLOAT NOT NULL,
            body_percentage_threshold FLOAT NOT NULL,
            lookback_candles INT NOT NULL,
            created_at DATETIME NOT NULL
        )
        """)
        
        # Tabla para datos de detección
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS A_detection_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME NOT NULL,
            is_key_candle BOOLEAN NOT NULL,
            volume FLOAT NOT NULL,
            body_percentage FLOAT NOT NULL,
            param_id INT NOT NULL,
            created_at DATETIME NOT NULL,
            FOREIGN KEY (param_id) REFERENCES A_detection_params(id)
        )
        """)
        
        # Tabla para parámetros de rango
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS A_range_params (
            id INT AUTO_INCREMENT PRIMARY KEY,
            atr_period INT NOT NULL,
            atr_multiplier FLOAT NOT NULL,
            created_at DATETIME NOT NULL
        )
        """)
        
        # Tabla para datos de rango
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS A_range_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME NOT NULL,
            reference_price FLOAT NOT NULL,
            upper_limit FLOAT NOT NULL,
            lower_limit FLOAT NOT NULL,
            atr_value FLOAT NOT NULL,
            param_id INT NOT NULL,
            detection_id INT,
            created_at DATETIME NOT NULL,
            FOREIGN KEY (param_id) REFERENCES A_range_params(id),
            FOREIGN KEY (detection_id) REFERENCES A_detection_data(id)
        )
        """)
        
        # Tabla para parámetros de breakout
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS A_breakout_params (
            id INT AUTO_INCREMENT PRIMARY KEY,
            breakout_threshold_percentage FLOAT NOT NULL,
            max_candles_to_return INT NOT NULL,
            created_at DATETIME NOT NULL
        )
        """)
        
        # Tabla para datos de breakout
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS A_breakout_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME NOT NULL,
            direction VARCHAR(10) NOT NULL,
            breakout_percentage FLOAT NOT NULL,
            is_valid BOOLEAN NOT NULL,
            param_id INT NOT NULL,
            range_id INT,
            created_at DATETIME NOT NULL,
            FOREIGN KEY (param_id) REFERENCES A_breakout_params(id),
            FOREIGN KEY (range_id) REFERENCES A_range_data(id)
        )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Tablas creadas correctamente.")
        return True
    
    except mysql.connector.Error as err:
        print(f"Error al crear las tablas: {err}")
        return False

if __name__ == "__main__":
    create_tables()
