"""
A_optimizer Detection Module

This module handles the detection of key candles based on volume and body size criteria.
It identifies potential reversal or continuation zones for trading strategies.
"""

import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

class A_Detection:
    def __init__(self):
        """Initialize the detection module with database connection"""
        self.db_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'binance_lob')
        }
        self.create_tables()
    
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Create table for detection parameters (modifiable)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS A_detection_params (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    volume_percentile_threshold FLOAT NOT NULL,
                    body_percentage_threshold FLOAT NOT NULL,
                    lookback_candles INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT FALSE,
                    performance_score FLOAT DEFAULT 0.0
                )
            ''')
            
            # Create table for detection results (observable data)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS A_detection_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    param_id INT,
                    timestamp BIGINT,
                    symbol VARCHAR(20),
                    current_volume FLOAT,
                    current_body_size FLOAT,
                    current_range FLOAT,
                    volume_percentile FLOAT,
                    is_key_candle BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (param_id) REFERENCES A_detection_params(id)
                )
            ''')
            
            conn.commit()
            print("A_Detection tables created successfully")
        except Error as e:
            print(f"Error creating tables: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def insert_params(self, volume_percentile_threshold, body_percentage_threshold, lookback_candles):
        """Insert a new set of parameters into the database"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            query = '''
                INSERT INTO A_detection_params 
                (volume_percentile_threshold, body_percentage_threshold, lookback_candles)
                VALUES (%s, %s, %s)
            '''
            values = (volume_percentile_threshold, body_percentage_threshold, lookback_candles)
            cursor.execute(query, values)
            
            param_id = cursor.lastrowid
            conn.commit()
            return param_id
        except Error as e:
            print(f"Error inserting parameters: {e}")
            return None
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def get_active_params(self):
        """Get the currently active parameters"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)
            
            query = "SELECT * FROM A_detection_params WHERE is_active = TRUE LIMIT 1"
            cursor.execute(query)
            result = cursor.fetchone()
            
            if not result:
                # If no active parameters, get the best performing one
                query = "SELECT * FROM A_detection_params ORDER BY performance_score DESC LIMIT 1"
                cursor.execute(query)
                result = cursor.fetchone()
                
                # If still no result, use default values
                if not result:
                    return {
                        'id': None,
                        'volume_percentile_threshold': 80,
                        'body_percentage_threshold': 30,
                        'lookback_candles': 50
                    }
            
            return result
        except Error as e:
            print(f"Error getting active parameters: {e}")
            return None
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def set_active_param(self, param_id):
        """Set a parameter set as active and deactivate others"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Deactivate all parameters
            cursor.execute("UPDATE A_detection_params SET is_active = FALSE")
            
            # Activate the specified parameter
            cursor.execute("UPDATE A_detection_params SET is_active = TRUE WHERE id = %s", (param_id,))
            
            conn.commit()
            return True
        except Error as e:
            print(f"Error setting active parameter: {e}")
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def detect_key_candle(self, data, index, params=None):
        """
        Detect if the candle at the given index is a key candle
        
        Args:
            data (pd.DataFrame): DataFrame with OHLCV data
            index (int): Index of the candle to check
            params (dict): Optional parameters to override defaults
            
        Returns:
            tuple: (is_key_candle, detection_data)
        """
        if params is None:
            params = self.get_active_params()
        
        lookback = params['lookback_candles']
        
        # Ensure we have enough data
        if index < lookback:
            return False, {}
        
        # Calculate volume percentile
        volume_percentile = np.percentile(
            data['volume'].iloc[index - lookback:index], 
            params['volume_percentile_threshold']
        )
        
        # Get current candle data
        current_volume = data['volume'].iloc[index]
        current_body_size = abs(data['close'].iloc[index] - data['open'].iloc[index])
        current_range = data['high'].iloc[index] - data['low'].iloc[index]
        
        # Check conditions
        is_high_volume = current_volume > volume_percentile
        
        # Avoid division by zero
        if current_range == 0:
            is_small_body = False
        else:
            is_small_body = (current_body_size / current_range) * 100 < params['body_percentage_threshold']
        
        is_key_candle = is_high_volume and is_small_body
        
        # Prepare detection data
        detection_data = {
            'current_volume': current_volume,
            'current_body_size': current_body_size,
            'current_range': current_range,
            'volume_percentile': volume_percentile,
            'is_key_candle': is_key_candle
        }
        
        return is_key_candle, detection_data
    
    def save_detection_data(self, param_id, timestamp, symbol, detection_data):
        """Save detection results to the database"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            query = '''
                INSERT INTO A_detection_data 
                (param_id, timestamp, symbol, current_volume, current_body_size, 
                current_range, volume_percentile, is_key_candle)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            '''
            values = (
                param_id,
                timestamp,
                symbol,
                detection_data['current_volume'],
                detection_data['current_body_size'],
                detection_data['current_range'],
                detection_data['volume_percentile'],
                detection_data['is_key_candle']
            )
            cursor.execute(query, values)
            
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error saving detection data: {e}")
            return None
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def update_performance_score(self, param_id, score):
        """Update the performance score for a parameter set"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            query = '''
                UPDATE A_detection_params 
                SET performance_score = %s
                WHERE id = %s
            '''
            values = (score, param_id)
            cursor.execute(query, values)
            
            conn.commit()
            return True
        except Error as e:
            print(f"Error updating performance score: {e}")
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def generate_grid_search_params(self, num_params=50):
        """
        Generate parameters for grid search
        
        Args:
            num_params (int): Maximum number of parameter combinations to generate
            
        Returns:
            list: List of parameter dictionaries
        """
        # Define parameter ranges
        volume_percentile_thresholds = np.linspace(70, 95, 6)
        body_percentage_thresholds = np.linspace(20, 50, 6)
        lookback_candles_values = [20, 30, 50, 70, 100]
        
        params_list = []
        
        # Generate combinations
        for vpt in volume_percentile_thresholds:
            for bpt in body_percentage_thresholds:
                for lc in lookback_candles_values:
                    params_list.append({
                        'volume_percentile_threshold': round(vpt, 2),
                        'body_percentage_threshold': round(bpt, 2),
                        'lookback_candles': int(lc)
                    })
                    
                    # Limit to max number of parameters
                    if len(params_list) >= num_params:
                        return params_list
        
        return params_list
    
    def run_grid_search(self, data, max_params=50):
        """
        Run grid search to find optimal parameters
        
        Args:
            data (pd.DataFrame): DataFrame with OHLCV data
            max_params (int): Maximum number of parameter combinations to test
            
        Returns:
            dict: Best parameters and their performance
        """
        params_list = self.generate_grid_search_params(max_params)
        results = []
        
        for params in params_list:
            # Insert parameters to get an ID
            param_id = self.insert_params(
                params['volume_percentile_threshold'],
                params['body_percentage_threshold'],
                params['lookback_candles']
            )
            
            if not param_id:
                continue
            
            # Count key candles
            key_candle_count = 0
            valid_candles = 0
            
            # Start from a point where we have enough lookback data
            start_idx = params['lookback_candles']
            
            for i in range(start_idx, len(data)):
                is_key, detection_data = self.detect_key_candle(data, i, params)
                
                # Save detection data
                if 'timestamp' in data.columns:
                    timestamp = data['timestamp'].iloc[i]
                else:
                    timestamp = i
                
                self.save_detection_data(param_id, timestamp, 'BTCUSDC', detection_data)
                
                if is_key:
                    key_candle_count += 1
                valid_candles += 1
            
            # Calculate performance (percentage of key candles)
            if valid_candles > 0:
                performance = (key_candle_count / valid_candles) * 100
                
                # Update performance score
                self.update_performance_score(param_id, performance)
                
                results.append({
                    'param_id': param_id,
                    'params': params,
                    'key_candle_count': key_candle_count,
                    'valid_candles': valid_candles,
                    'performance': performance
                })
        
        # Find best parameters (those that identify 5-15% of candles as key)
        optimal_results = [r for r in results if 5 <= r['performance'] <= 15]
        
        if optimal_results:
            # Sort by performance closest to 10%
            optimal_results.sort(key=lambda x: abs(x['performance'] - 10))
            best_result = optimal_results[0]
        else:
            # If no optimal results, choose the one closest to 10%
            results.sort(key=lambda x: abs(x['performance'] - 10))
            best_result = results[0] if results else None
        
        # Set best parameters as active
        if best_result:
            self.set_active_param(best_result['param_id'])
        
        return best_result

# For testing
if __name__ == "__main__":
    # Example usage
    detector = A_Detection()
    
    # Load data
    try:
        file_path = "data/BTCUSDC-5m-2025-04-08/BTCUSDC-5m-2025-04-08.csv"
        df = pd.read_csv(file_path)
        
        # Rename columns for clarity
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                      'close_time', 'quote_asset_volume', 'number_of_trades', 
                      'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
        
        # Run grid search
        best_params = detector.run_grid_search(df, max_params=50)
        print(f"Best parameters: {best_params}")
        
    except Exception as e:
        print(f"Error in testing: {e}")
