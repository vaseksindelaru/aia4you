"""
A_optimizer Breakout Module

This module evaluates breakouts from the dynamic price range and determines if they are valid.
It identifies potential trading signals based on price movements outside the range.
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

class A_Breakout:
    def __init__(self):
        """Initialize the breakout module with database connection"""
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
            
            # Create table for breakout parameters (modifiable)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS A_breakout_params (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    breakout_threshold_percentage FLOAT NOT NULL,
                    max_candles_to_return INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT FALSE,
                    performance_score FLOAT DEFAULT 0.0
                )
            ''')
            
            # Create table for breakout results (observable data)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS A_breakout_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    param_id INT,
                    range_id INT,
                    timestamp BIGINT,
                    symbol VARCHAR(20),
                    direction VARCHAR(10),
                    breakout_distance FLOAT,
                    is_valid_breakout BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (param_id) REFERENCES A_breakout_params(id)
                )
            ''')
            
            conn.commit()
            print("A_Breakout tables created successfully")
        except Error as e:
            print(f"Error creating tables: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def insert_params(self, breakout_threshold_percentage, max_candles_to_return):
        """Insert a new set of parameters into the database"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            query = '''
                INSERT INTO A_breakout_params 
                (breakout_threshold_percentage, max_candles_to_return)
                VALUES (%s, %s)
            '''
            values = (breakout_threshold_percentage, max_candles_to_return)
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
            
            query = "SELECT * FROM A_breakout_params WHERE is_active = TRUE LIMIT 1"
            cursor.execute(query)
            result = cursor.fetchone()
            
            if not result:
                # If no active parameters, get the best performing one
                query = "SELECT * FROM A_breakout_params ORDER BY performance_score DESC LIMIT 1"
                cursor.execute(query)
                result = cursor.fetchone()
                
                # If still no result, use default values
                if not result:
                    return {
                        'id': None,
                        'breakout_threshold_percentage': 0.5,
                        'max_candles_to_return': 2
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
            cursor.execute("UPDATE A_breakout_params SET is_active = FALSE")
            
            # Activate the specified parameter
            cursor.execute("UPDATE A_breakout_params SET is_active = TRUE WHERE id = %s", (param_id,))
            
            conn.commit()
            return True
        except Error as e:
            print(f"Error setting active parameter: {e}")
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def evaluate_breakout(self, data, index, range_data, params=None):
        """
        Evaluate if a breakout is valid
        
        Args:
            data (pd.DataFrame): DataFrame with OHLCV data
            index (int): Index of the candle to evaluate
            range_data (dict): Range data with upper and lower boundaries
            params (dict): Optional parameters to override defaults
            
        Returns:
            tuple: (is_valid_breakout, breakout_data)
        """
        if params is None:
            params = self.get_active_params()
        
        # Make sure we have enough future data
        if index + params['max_candles_to_return'] >= len(data):
            return False, {}
        
        range_upper = range_data['range_upper']
        range_lower = range_data['range_lower']
        breakout_threshold = params['breakout_threshold_percentage']
        max_candles = params['max_candles_to_return']
        
        # Determine direction of breakout
        close_price = data['close'].iloc[index]
        
        if close_price > range_upper:
            direction = "bullish"
            breakout_distance = (close_price - range_upper) / range_upper * 100
            threshold_condition = breakout_distance >= breakout_threshold
            
            # Check if price returns to range within max_candles
            future_prices = data['close'].iloc[index + 1:index + 1 + max_candles]
            return_condition = any(price <= range_upper for price in future_prices)
            
        elif close_price < range_lower:
            direction = "bearish"
            breakout_distance = (range_lower - close_price) / range_lower * 100
            threshold_condition = breakout_distance >= breakout_threshold
            
            # Check if price returns to range within max_candles
            future_prices = data['close'].iloc[index + 1:index + 1 + max_candles]
            return_condition = any(price >= range_lower for price in future_prices)
            
        else:
            # No breakout
            return False, {
                'direction': "none",
                'breakout_distance': 0,
                'is_valid_breakout': False
            }
        
        is_valid_breakout = threshold_condition and not return_condition
        
        # Prepare breakout data
        breakout_data = {
            'direction': direction,
            'breakout_distance': breakout_distance,
            'is_valid_breakout': is_valid_breakout
        }
        
        return is_valid_breakout, breakout_data
    
    def save_breakout_data(self, param_id, range_id, timestamp, symbol, breakout_data):
        """Save breakout results to the database"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            query = '''
                INSERT INTO A_breakout_data 
                (param_id, range_id, timestamp, symbol, direction, breakout_distance, is_valid_breakout)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            values = (
                param_id,
                range_id,
                timestamp,
                symbol,
                breakout_data['direction'],
                breakout_data['breakout_distance'],
                breakout_data['is_valid_breakout']
            )
            cursor.execute(query, values)
            
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error saving breakout data: {e}")
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
                UPDATE A_breakout_params 
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
        breakout_thresholds = np.linspace(0.1, 2.0, 10)
        max_candles_values = [1, 2, 3, 5, 7]
        
        params_list = []
        
        # Generate combinations
        for threshold in breakout_thresholds:
            for max_candles in max_candles_values:
                params_list.append({
                    'breakout_threshold_percentage': round(threshold, 2),
                    'max_candles_to_return': int(max_candles)
                })
                
                # Limit to max number of parameters
                if len(params_list) >= num_params:
                    return params_list
        
        return params_list
    
    def run_grid_search(self, data, range_data_list, max_params=50):
        """
        Run grid search to find optimal parameters
        
        Args:
            data (pd.DataFrame): DataFrame with OHLCV data
            range_data_list (list): List of dictionaries with range data and indices
            max_params (int): Maximum number of parameter combinations to test
            
        Returns:
            dict: Best parameters and their performance
        """
        params_list = self.generate_grid_search_params(max_params)
        results = []
        
        for params in params_list:
            # Insert parameters to get an ID
            param_id = self.insert_params(
                params['breakout_threshold_percentage'],
                params['max_candles_to_return']
            )
            
            if not param_id:
                continue
            
            # Evaluate breakouts
            valid_breakouts = 0
            total_breakouts = 0
            profitable_trades = 0
            
            for range_item in range_data_list:
                range_data = range_item['range_data']
                key_candle_idx = range_item['index']
                
                # Look for breakouts in the next 10 candles
                for i in range(1, 11):
                    breakout_idx = key_candle_idx + i
                    
                    # Skip if we don't have enough future data
                    if breakout_idx + params['max_candles_to_return'] >= len(data):
                        continue
                    
                    # Check if there's a breakout
                    is_valid, breakout_data = self.evaluate_breakout(
                        data, breakout_idx, range_data, params
                    )
                    
                    if breakout_data.get('direction') != 'none':
                        total_breakouts += 1
                        
                        # Save breakout data
                        if 'timestamp' in data.columns:
                            timestamp = data['timestamp'].iloc[breakout_idx]
                        else:
                            timestamp = breakout_idx
                        
                        self.save_breakout_data(
                            param_id, None, timestamp, 'BTCUSDC', breakout_data
                        )
                        
                        if is_valid:
                            valid_breakouts += 1
                            
                            # Check if the breakout was profitable
                            direction = breakout_data['direction']
                            entry_price = data['close'].iloc[breakout_idx]
                            
                            # Look 5 candles ahead for profit calculation
                            future_idx = min(breakout_idx + 5, len(data) - 1)
                            exit_price = data['close'].iloc[future_idx]
                            
                            if (direction == 'bullish' and exit_price > entry_price) or \
                               (direction == 'bearish' and exit_price < entry_price):
                                profitable_trades += 1
                    
                    # Stop looking for breakouts once we find one
                    if breakout_data.get('direction') != 'none':
                        break
            
            # Calculate performance metrics
            if total_breakouts > 0:
                valid_ratio = (valid_breakouts / total_breakouts) * 100
                if valid_breakouts > 0:
                    profit_ratio = (profitable_trades / valid_breakouts) * 100
                else:
                    profit_ratio = 0
                
                # Combined score (weighted average)
                combined_score = (valid_ratio * 0.4) + (profit_ratio * 0.6)
                
                # Update performance score
                self.update_performance_score(param_id, combined_score)
                
                results.append({
                    'param_id': param_id,
                    'params': params,
                    'total_breakouts': total_breakouts,
                    'valid_breakouts': valid_breakouts,
                    'profitable_trades': profitable_trades,
                    'valid_ratio': valid_ratio,
                    'profit_ratio': profit_ratio,
                    'combined_score': combined_score
                })
        
        # Find best parameters (those with highest combined score)
        if results:
            results.sort(key=lambda x: x['combined_score'], reverse=True)
            best_result = results[0]
            
            # Set best parameters as active
            self.set_active_param(best_result['param_id'])
            
            return best_result
        
        return None

# For testing
if __name__ == "__main__":
    # Example usage
    from detection import A_Detection
    from range import A_Range
    
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
        detection_params = {
            'volume_percentile_threshold': 80,
            'body_percentage_threshold': 30,
            'lookback_candles': 50
        }
        
        # Find key candles
        key_candles = []
        for i in range(detection_params['lookback_candles'], len(df)):
            is_key, _ = detector.detect_key_candle(df, i, detection_params)
            if is_key:
                key_candles.append(i)
        
        # Calculate ranges for key candles
        range_optimizer = A_Range()
        range_params = {
            'atr_period': 14,
            'atr_multiplier': 1.5
        }
        
        range_data_list = []
        for idx in key_candles:
            if idx < range_params['atr_period']:
                continue
            
            range_data = range_optimizer.calculate_range(df, idx, None, range_params)
            range_data_list.append({
                'index': idx,
                'range_data': range_data
            })
        
        # Now run grid search for breakout parameters
        breakout_optimizer = A_Breakout()
        best_params = breakout_optimizer.run_grid_search(df, range_data_list, max_params=50)
        print(f"Best breakout parameters: {best_params}")
        
    except Exception as e:
        print(f"Error in testing: {e}")
