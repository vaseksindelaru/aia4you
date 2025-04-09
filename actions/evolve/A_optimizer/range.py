"""
A_optimizer Range Module

This module handles the calculation of dynamic price ranges based on ATR (Average True Range).
It defines upper and lower boundaries for potential trading zones.
"""

import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import json
import requests
from datetime import datetime

# Load environment variables
load_dotenv()

class A_Range:
    def __init__(self):
        """Initialize the range module with database connection"""
        self.db_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'binance_lob')
        }
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        self.create_tables()
    
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Create table for range parameters (modifiable)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS A_range_params (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    atr_period INT NOT NULL,
                    atr_multiplier FLOAT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT FALSE,
                    performance_score FLOAT DEFAULT 0.0
                )
            ''')
            
            # Create table for range results (observable data)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS A_range_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    param_id INT,
                    detection_id INT,
                    timestamp BIGINT,
                    symbol VARCHAR(20),
                    range_center FLOAT,
                    atr_value FLOAT,
                    range_upper FLOAT,
                    range_lower FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (param_id) REFERENCES A_range_params(id)
                )
            ''')
            
            conn.commit()
            print("A_Range tables created successfully")
        except Error as e:
            print(f"Error creating tables: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def insert_params(self, atr_period, atr_multiplier):
        """Insert a new set of parameters into the database"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            query = '''
                INSERT INTO A_range_params 
                (atr_period, atr_multiplier)
                VALUES (%s, %s)
            '''
            values = (atr_period, atr_multiplier)
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
            
            query = "SELECT * FROM A_range_params WHERE is_active = TRUE LIMIT 1"
            cursor.execute(query)
            result = cursor.fetchone()
            
            if not result:
                # If no active parameters, get the best performing one
                query = "SELECT * FROM A_range_params ORDER BY performance_score DESC LIMIT 1"
                cursor.execute(query)
                result = cursor.fetchone()
                
                # If still no result, use default values
                if not result:
                    return {
                        'id': None,
                        'atr_period': 14,
                        'atr_multiplier': 1.5
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
            cursor.execute("UPDATE A_range_params SET is_active = FALSE")
            
            # Activate the specified parameter
            cursor.execute("UPDATE A_range_params SET is_active = TRUE WHERE id = %s", (param_id,))
            
            conn.commit()
            return True
        except Error as e:
            print(f"Error setting active parameter: {e}")
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def get_atr_from_api(self, symbol="BTCUSDC", period=14):
        """
        Get ATR values from the API
        
        Args:
            symbol (str): Trading symbol
            period (int): ATR period
            
        Returns:
            dict: API response with ATR values
        """
        try:
            url = f"{self.api_base_url}/atr"
            params = {
                "period": period,
                "symbol": symbol
            }
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error fetching ATR from API: {e}")
            return None
    
    def calculate_range(self, data, index, detection_id=None, params=None):
        """
        Calculate the dynamic range based on ATR
        
        Args:
            data (pd.DataFrame): DataFrame with OHLCV data
            index (int): Index of the candle to calculate range for
            detection_id (int): Optional ID from detection table
            params (dict): Optional parameters to override defaults
            
        Returns:
            dict: Range data
        """
        if params is None:
            params = self.get_active_params()
        
        # Try to get ATR from API first
        atr_data = self.get_atr_from_api(period=params['atr_period'])
        
        if atr_data and 'atr_values' in atr_data and len(atr_data['atr_values']) > 0:
            # Use the latest ATR value from API
            atr_value = atr_data['atr_current']
        else:
            # Calculate ATR locally if API fails
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            
            # Create DataFrame with the three components
            ranges = pd.DataFrame({
                'high_low': high_low,
                'high_close': high_close,
                'low_close': low_close
            })
            
            # True Range is the maximum of the three components
            true_range = ranges.max(axis=1)
            
            # ATR is the moving average of True Range
            atr = true_range.rolling(window=params['atr_period']).mean()
            atr_value = atr.iloc[index]
        
        # Calculate range center and boundaries
        range_center = (data['high'].iloc[index] + data['low'].iloc[index]) / 2
        margin = params['atr_multiplier'] * atr_value
        range_upper = range_center + margin
        range_lower = range_center - margin
        
        # Prepare range data
        range_data = {
            'range_center': range_center,
            'atr_value': atr_value,
            'range_upper': range_upper,
            'range_lower': range_lower
        }
        
        return range_data
    
    def save_range_data(self, param_id, detection_id, timestamp, symbol, range_data):
        """Save range results to the database"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            query = '''
                INSERT INTO A_range_data 
                (param_id, detection_id, timestamp, symbol, range_center, atr_value, range_upper, range_lower)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            '''
            values = (
                param_id,
                detection_id,
                timestamp,
                symbol,
                range_data['range_center'],
                range_data['atr_value'],
                range_data['range_upper'],
                range_data['range_lower']
            )
            cursor.execute(query, values)
            
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error saving range data: {e}")
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
                UPDATE A_range_params 
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
        atr_periods = [5, 7, 10, 14, 21, 28]
        atr_multipliers = np.linspace(0.5, 3.0, 10)
        
        params_list = []
        
        # Generate combinations
        for period in atr_periods:
            for multiplier in atr_multipliers:
                params_list.append({
                    'atr_period': period,
                    'atr_multiplier': round(multiplier, 2)
                })
                
                # Limit to max number of parameters
                if len(params_list) >= num_params:
                    return params_list
        
        return params_list
    
    def run_grid_search(self, data, key_candles_indices, max_params=50):
        """
        Run grid search to find optimal parameters
        
        Args:
            data (pd.DataFrame): DataFrame with OHLCV data
            key_candles_indices (list): List of indices of key candles
            max_params (int): Maximum number of parameter combinations to test
            
        Returns:
            dict: Best parameters and their performance
        """
        params_list = self.generate_grid_search_params(max_params)
        results = []
        
        for params in params_list:
            # Insert parameters to get an ID
            param_id = self.insert_params(
                params['atr_period'],
                params['atr_multiplier']
            )
            
            if not param_id:
                continue
            
            # Calculate ranges for key candles
            range_coverage = []
            
            for idx in key_candles_indices:
                # Skip if we don't have enough data for ATR calculation
                if idx < params['atr_period']:
                    continue
                
                range_data = self.calculate_range(data, idx, None, params)
                
                # Save range data
                if 'timestamp' in data.columns:
                    timestamp = data['timestamp'].iloc[idx]
                else:
                    timestamp = idx
                
                self.save_range_data(param_id, None, timestamp, 'BTCUSDC', range_data)
                
                # Check how many of the next 10 candles stay within the range
                candles_in_range = 0
                future_candles = min(10, len(data) - idx - 1)
                
                for i in range(1, future_candles + 1):
                    future_idx = idx + i
                    high = data['high'].iloc[future_idx]
                    low = data['low'].iloc[future_idx]
                    
                    # Check if candle is completely within range
                    if low >= range_data['range_lower'] and high <= range_data['range_upper']:
                        candles_in_range += 1
                    # Or if range is breached but returns
                    elif (low < range_data['range_lower'] and high > range_data['range_lower']) or \
                         (high > range_data['range_upper'] and low < range_data['range_upper']):
                        candles_in_range += 0.5
                
                # Calculate percentage of future candles within range
                if future_candles > 0:
                    coverage = (candles_in_range / future_candles) * 100
                    range_coverage.append(coverage)
            
            # Calculate average coverage
            if range_coverage:
                avg_coverage = sum(range_coverage) / len(range_coverage)
                
                # Update performance score
                self.update_performance_score(param_id, avg_coverage)
                
                results.append({
                    'param_id': param_id,
                    'params': params,
                    'avg_coverage': avg_coverage,
                    'num_key_candles': len(range_coverage)
                })
        
        # Find best parameters (those with 60-80% coverage)
        optimal_results = [r for r in results if 60 <= r['avg_coverage'] <= 80]
        
        if optimal_results:
            # Sort by coverage closest to 70%
            optimal_results.sort(key=lambda x: abs(x['avg_coverage'] - 70))
            best_result = optimal_results[0]
        else:
            # If no optimal results, choose the one closest to 70%
            results.sort(key=lambda x: abs(x['avg_coverage'] - 70))
            best_result = results[0] if results else None
        
        # Set best parameters as active
        if best_result:
            self.set_active_param(best_result['param_id'])
        
        return best_result

# For testing
if __name__ == "__main__":
    # Example usage
    from detection import A_Detection
    
    # Load data
    try:
        file_path = "data/BTCUSDC-5m-2025-04-08/BTCUSDC-5m-2025-04-08.csv"
        df = pd.read_csv(file_path)
        
        # Rename columns for clarity
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                      'close_time', 'quote_asset_volume', 'number_of_trades', 
                      'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
        
        # First, detect key candles
        detector = A_Detection()
        
        # Use default parameters for detection
        params = {
            'volume_percentile_threshold': 80,
            'body_percentage_threshold': 30,
            'lookback_candles': 50
        }
        
        # Find key candles
        key_candles = []
        for i in range(params['lookback_candles'], len(df)):
            is_key, _ = detector.detect_key_candle(df, i, params)
            if is_key:
                key_candles.append(i)
        
        # Now run grid search for range parameters
        range_optimizer = A_Range()
        best_params = range_optimizer.run_grid_search(df, key_candles, max_params=50)
        print(f"Best range parameters: {best_params}")
        
    except Exception as e:
        print(f"Error in testing: {e}")
