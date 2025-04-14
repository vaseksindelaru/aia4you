"""
save_detection_results.py - Module for saving Shakeout strategy detection results to database

This module provides functionality to save key candle detection results from the
Shakeout strategy to the binance_lob database for further analysis and visualization.
"""

import os
import sys
import mysql.connector
from mysql.connector import Error
import pandas as pd
import numpy as np
import json
from datetime import datetime
import traceback
from dotenv import load_dotenv

# Add project root to path to allow imports from other modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from strategy.shakeout.detect import Detector


class DetectionResultSaver:
    """
    Class for saving Shakeout strategy detection results to the binance_lob database.
    
    This class handles the database connection and provides methods to save
    detection results, including key candle data and detection parameters.
    """
    
    def __init__(self, host=None, user=None, password=None, database=None):
        """
        Initialize the DetectionResultSaver with database connection parameters.
        If parameters are not provided, they will be loaded from .env file.
        
        Parameters:
        -----------
        host : str
            Database host address
        user : str
            Database username
        password : str
            Database password
        database : str
            Database name
        """
        # Load environment variables from .env file
        load_dotenv()
        
        # Use provided parameters or load from environment variables
        self.db_config = {
            'host': host or os.getenv('MYSQL_HOST', 'localhost'),
            'user': user or os.getenv('MYSQL_USER', 'root'),
            'password': password or os.getenv('MYSQL_PASSWORD', ''),
            'database': database or os.getenv('MYSQL_DATABASE', 'binance_lob')
        }
        
        print(f"Database configuration: host={self.db_config['host']}, user={self.db_config['user']}, database={self.db_config['database']}")
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """
        Establish connection to the database.
        
        Returns:
        --------
        bool
            True if connection was successful, False otherwise
        """
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            if self.connection.is_connected():
                self.cursor = self.connection.cursor()
                print(f"Connected to MySQL database: {self.db_config['database']}")
                return True
        except Error as e:
            print(f"Error connecting to MySQL database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.connection and self.connection.is_connected():
            if self.cursor:
                self.cursor.close()
            self.connection.close()
            print("MySQL connection closed")
    
    def create_tables(self):
        """
        Create necessary tables if they don't exist.
        
        Creates:
        - detection_sessions: Stores information about detection runs
        - detection_params: Stores parameters used for detection
        - key_candles: Stores detected key candles and their properties
        
        Returns:
        --------
        bool
            True if tables were created successfully, False otherwise
        """
        try:
            # Create detection_sessions table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS detection_sessions (
                    session_id INT AUTO_INCREMENT PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    timeframe VARCHAR(10) NOT NULL,
                    start_time BIGINT,
                    end_time BIGINT,
                    total_candles INT,
                    key_candles_count INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create detection_params table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS detection_params (
                    param_id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id INT,
                    param_name VARCHAR(50) NOT NULL,
                    param_value FLOAT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES detection_sessions(session_id)
                )
            """)
            
            # Create key_candles table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS key_candles (
                    candle_id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id INT,
                    candle_index INT NOT NULL,
                    timestamp BIGINT,
                    open FLOAT,
                    high FLOAT,
                    low FLOAT,
                    close FLOAT,
                    volume FLOAT,
                    body_size FLOAT,
                    range_size FLOAT,
                    body_percentage FLOAT,
                    volume_percentile FLOAT,
                    is_high_volume BOOLEAN,
                    is_small_body BOOLEAN,
                    detection_data JSON,
                    FOREIGN KEY (session_id) REFERENCES detection_sessions(session_id)
                )
            """)
            
            self.connection.commit()
            print("Tables created successfully")
            return True
            
        except Error as e:
            print(f"Error creating tables: {e}")
            return False
    
    def save_detection_results(self, detector, symbol="BTCUSDT", timeframe="5m"):
        """
        Save detection results from a Detector instance to the database.
        
        Parameters:
        -----------
        detector : Detector
            Instance of Detector class with results to save
        symbol : str
            Trading symbol (e.g., 'BTCUSDT')
        timeframe : str
            Timeframe of the data (e.g., '5m', '1h')
            
        Returns:
        --------
        int or None
            Session ID if results were saved successfully, None otherwise
        """
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return None
        
        try:
            # Ensure tables exist
            self.create_tables()
            
            # Extract data from detector
            results = detector.results
            params = detector.detection_params
            data = detector.data
            
            if not results:
                print("No results to save")
                return None
            
            # Get start and end timestamps and convert NumPy types to Python native types
            start_time = int(data['timestamp'].iloc[0]) if 'timestamp' in data.columns else None
            end_time = int(data['timestamp'].iloc[-1]) if 'timestamp' in data.columns else None
            
            # Insert detection session
            self.cursor.execute("""
                INSERT INTO detection_sessions 
                (symbol, timeframe, start_time, end_time, total_candles, key_candles_count)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (symbol, timeframe, start_time, end_time, len(data), len(results)))
            
            session_id = self.cursor.lastrowid
            
            # Insert detection parameters
            for param_name, param_value in params.items():
                self.cursor.execute("""
                    INSERT INTO detection_params 
                    (session_id, param_name, param_value)
                    VALUES (%s, %s, %s)
                """, (session_id, param_name, float(param_value)))
            
            # Insert key candles
            for result in results:
                # Convert NumPy types to Python native types
                candle_index = int(result['index'])
                timestamp = int(result['timestamp']) if result['timestamp'] is not None else None
                
                # Get OHLCV data for this candle and convert to Python native types
                open_price = float(data['open'].iloc[candle_index]) if 'open' in data.columns else None
                high_price = float(data['high'].iloc[candle_index]) if 'high' in data.columns else None
                low_price = float(data['low'].iloc[candle_index]) if 'low' in data.columns else None
                close_price = float(data['close'].iloc[candle_index]) if 'close' in data.columns else None
                volume = float(data['volume'].iloc[candle_index]) if 'volume' in data.columns else None
                
                # Get detection data and convert to Python native types
                body_size = float(result['current_body_size'])
                range_size = float(result['current_range'])
                body_percentage = float(result['body_percentage']) if 'body_percentage' in result else None
                volume_percentile = float(result['volume_percentile'])
                is_high_volume = bool(result['is_high_volume'])
                is_small_body = bool(result['is_small_body'])
                
                # Convert detection data to JSON, ensuring all NumPy types are converted to Python native types
                detection_data_dict = {}
                for k, v in result.items():
                    if k not in ['index', 'timestamp']:
                        # Convert NumPy types to Python native types
                        if isinstance(v, (np.integer, np.int64, np.int32)):
                            detection_data_dict[k] = int(v)
                        elif isinstance(v, (np.floating, np.float64, np.float32)):
                            detection_data_dict[k] = float(v)
                        elif isinstance(v, np.bool_):
                            detection_data_dict[k] = bool(v)
                        else:
                            detection_data_dict[k] = v
                detection_data = json.dumps(detection_data_dict)
                
                self.cursor.execute("""
                    INSERT INTO key_candles 
                    (session_id, candle_index, timestamp, open, high, low, close, volume,
                     body_size, range_size, body_percentage, volume_percentile,
                     is_high_volume, is_small_body, detection_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    session_id, candle_index, timestamp, open_price, high_price, low_price, 
                    close_price, volume, body_size, range_size, body_percentage, 
                    volume_percentile, is_high_volume, is_small_body, detection_data
                ))
            
            self.connection.commit()
            print(f"Detection results saved successfully. Session ID: {session_id}")
            return session_id
            
        except Error as e:
            print(f"Error saving detection results: {e}")
            traceback.print_exc()
            if self.connection:
                self.connection.rollback()
            return None
    
    def run_detection_and_save(self, csv_path, symbol="BTCUSDT", timeframe="5m", 
                              volume_percentile_threshold=80, 
                              body_percentage_threshold=30, 
                              lookback_candles=20):
        """
        Run detection on CSV data and save results to database.
        
        Parameters:
        -----------
        csv_path : str
            Path to CSV file with OHLCV data
        symbol : str
            Trading symbol (e.g., 'BTCUSDT')
        timeframe : str
            Timeframe of the data (e.g., '5m', '1h')
        volume_percentile_threshold : float
            Percentile threshold for high volume detection
        body_percentage_threshold : float
            Percentage threshold for small body detection
        lookback_candles : int
            Number of candles to look back for percentile calculation
            
        Returns:
        --------
        int or None
            Session ID if results were saved successfully, None otherwise
        """
        try:
            # Initialize detector
            detector = Detector(csv_path)
            
            # Set detection parameters
            detector.set_detection_params(
                volume_percentile_threshold=volume_percentile_threshold,
                body_percentage_threshold=body_percentage_threshold,
                lookback_candles=lookback_candles
            )
            
            # Process CSV data
            detector.process_csv()
            
            # Save results to database
            return self.save_detection_results(detector, symbol, timeframe)
            
        except Exception as e:
            print(f"Error in run_detection_and_save: {e}")
            traceback.print_exc()
            return None


# Example usage
if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Shakeout detection and save results to database')
    parser.add_argument('--csv', type=str, default="data/models/strategies/klines/BTCUSDT-5m-2025-04-10.csv",
                        help='Path to CSV file with OHLCV data')
    parser.add_argument('--symbol', type=str, default="BTCUSDT",
                        help='Trading symbol')
    parser.add_argument('--timeframe', type=str, default="5m",
                        help='Timeframe of the data')
    parser.add_argument('--volume-threshold', type=float, default=80,
                        help='Percentile threshold for high volume detection')
    parser.add_argument('--body-threshold', type=float, default=30,
                        help='Percentage threshold for small body detection')
    parser.add_argument('--lookback', type=int, default=20,
                        help='Number of candles to look back for percentile calculation')
    parser.add_argument('--host', type=str, default="localhost",
                        help='Database host')
    parser.add_argument('--user', type=str, default="root",
                        help='Database user')
    parser.add_argument('--password', type=str, default="",
                        help='Database password')
    parser.add_argument('--database', type=str, default="binance_lob",
                        help='Database name')
    
    args = parser.parse_args()
    
    # Create saver and run detection
    saver = DetectionResultSaver(
        host=args.host,
        user=args.user,
        password=args.password,
        database=args.database
    )
    
    session_id = saver.run_detection_and_save(
        csv_path=args.csv,
        symbol=args.symbol,
        timeframe=args.timeframe,
        volume_percentile_threshold=args.volume_threshold,
        body_percentage_threshold=args.body_threshold,
        lookback_candles=args.lookback
    )
    
    if session_id:
        print(f"Detection completed and saved with session ID: {session_id}")
    else:
        print("Failed to complete detection and save results")
    
    # Close database connection
    saver.disconnect()
