"""
A_optimizer Runner

This module integrates all three components of the A_optimizer system:
1. Detection - Identifies key candles based on volume and body size
2. Range - Calculates dynamic price ranges using ATR
3. Breakout - Evaluates breakouts from the range

It provides a unified interface for running the complete optimization process.
"""

import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
import json
import requests
from datetime import datetime
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import A_optimizer components
from actions.evolve.A_optimizer import A_Detection, A_Range, A_Breakout

class A_OptimizerRunner:
    def __init__(self):
        """Initialize the A_optimizer runner with all three components"""
        self.detector = A_Detection()
        self.range_calculator = A_Range()
        self.breakout_evaluator = A_Breakout()
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
    
    def load_data(self, symbol="BTCUSDC", timeframe="5m", date="2025-04-08"):
        """
        Load data from CSV file
        
        Args:
            symbol (str): Trading symbol
            timeframe (str): Timeframe (e.g., '5m', '1h')
            date (str): Date in YYYY-MM-DD format
            
        Returns:
            pd.DataFrame: DataFrame with OHLCV data
        """
        file_path = f"data/{symbol}-{timeframe}-{date}/{symbol}-{timeframe}-{date}.csv"
        
        try:
            df = pd.read_csv(file_path)
            
            # Rename columns for clarity
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                        'close_time', 'quote_asset_volume', 'number_of_trades', 
                        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
            
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
    
    def run_detection_optimization(self, data, max_params=50):
        """
        Run grid search for detection parameters
        
        Args:
            data (pd.DataFrame): DataFrame with OHLCV data
            max_params (int): Maximum number of parameter combinations to test
            
        Returns:
            dict: Best parameters and their performance
        """
        print("Running detection optimization...")
        return self.detector.run_grid_search(data, max_params)
    
    def run_range_optimization(self, data, key_candles, max_params=50):
        """
        Run grid search for range parameters
        
        Args:
            data (pd.DataFrame): DataFrame with OHLCV data
            key_candles (list): List of indices of key candles
            max_params (int): Maximum number of parameter combinations to test
            
        Returns:
            dict: Best parameters and their performance
        """
        print("Running range optimization...")
        return self.range_calculator.run_grid_search(data, key_candles, max_params)
    
    def run_breakout_optimization(self, data, range_data_list, max_params=50):
        """
        Run grid search for breakout parameters
        
        Args:
            data (pd.DataFrame): DataFrame with OHLCV data
            range_data_list (list): List of dictionaries with range data and indices
            max_params (int): Maximum number of parameter combinations to test
            
        Returns:
            dict: Best parameters and their performance
        """
        print("Running breakout optimization...")
        return self.breakout_evaluator.run_grid_search(data, range_data_list, max_params)
    
    def run_full_optimization(self, data, max_params=50):
        """
        Run the complete optimization process for all three components
        
        Args:
            data (pd.DataFrame): DataFrame with OHLCV data
            max_params (int): Maximum number of parameter combinations to test
            
        Returns:
            dict: Results for all three components
        """
        # Step 1: Optimize detection parameters
        detection_results = self.run_detection_optimization(data, max_params)
        
        if not detection_results:
            print("Detection optimization failed")
            return None
        
        # Use optimized detection parameters to find key candles
        detection_params = detection_results['params']
        key_candles = []
        
        for i in range(detection_params['lookback_candles'], len(data)):
            is_key, _ = self.detector.detect_key_candle(data, i, detection_params)
            if is_key:
                key_candles.append(i)
        
        print(f"Found {len(key_candles)} key candles")
        
        # Step 2: Optimize range parameters
        range_results = self.run_range_optimization(data, key_candles, max_params)
        
        if not range_results:
            print("Range optimization failed")
            return {
                'detection': detection_results,
                'range': None,
                'breakout': None
            }
        
        # Use optimized range parameters to calculate ranges for key candles
        range_params = range_results['params']
        range_data_list = []
        
        for idx in key_candles:
            if idx < range_params['atr_period']:
                continue
            
            range_data = self.range_calculator.calculate_range(data, idx, None, range_params)
            range_data_list.append({
                'index': idx,
                'range_data': range_data
            })
        
        # Step 3: Optimize breakout parameters
        breakout_results = self.run_breakout_optimization(data, range_data_list, max_params)
        
        return {
            'detection': detection_results,
            'range': range_results,
            'breakout': breakout_results
        }
    
    def apply_strategy(self, data, start_idx=None):
        """
        Apply the optimized strategy to data
        
        Args:
            data (pd.DataFrame): DataFrame with OHLCV data
            start_idx (int): Optional starting index
            
        Returns:
            list: Trading signals
        """
        # Get active parameters for all components
        detection_params = self.detector.get_active_params()
        range_params = self.range_calculator.get_active_params()
        breakout_params = self.breakout_evaluator.get_active_params()
        
        # Set default start index
        if start_idx is None:
            start_idx = max(detection_params['lookback_candles'], range_params['atr_period'])
        
        signals = []
        
        # Process each candle
        for i in range(start_idx, len(data)):
            # Step 1: Check if it's a key candle
            is_key, detection_data = self.detector.detect_key_candle(data, i, detection_params)
            
            if is_key:
                # Step 2: Calculate range
                range_data = self.range_calculator.calculate_range(data, i, None, range_params)
                
                # Save the key candle and its range
                key_candle = {
                    'index': i,
                    'timestamp': data['timestamp'].iloc[i] if 'timestamp' in data.columns else i,
                    'detection_data': detection_data,
                    'range_data': range_data,
                    'signals': []
                }
                
                # Step 3: Look for breakouts in the next 10 candles
                for j in range(1, 11):
                    breakout_idx = i + j
                    
                    # Skip if we don't have enough data
                    if breakout_idx >= len(data) or breakout_idx + breakout_params['max_candles_to_return'] >= len(data):
                        continue
                    
                    # Check for breakout
                    is_valid, breakout_data = self.breakout_evaluator.evaluate_breakout(
                        data, breakout_idx, range_data, breakout_params
                    )
                    
                    if breakout_data.get('direction') != 'none':
                        # Add signal
                        signal = {
                            'index': breakout_idx,
                            'timestamp': data['timestamp'].iloc[breakout_idx] if 'timestamp' in data.columns else breakout_idx,
                            'price': data['close'].iloc[breakout_idx],
                            'direction': breakout_data['direction'],
                            'is_valid': is_valid,
                            'breakout_distance': breakout_data['breakout_distance']
                        }
                        
                        key_candle['signals'].append(signal)
                        
                        # Stop looking for breakouts once we find one
                        break
                
                # Only add key candles that generated signals
                if key_candle['signals']:
                    signals.append(key_candle)
        
        return signals

# For testing
if __name__ == "__main__":
    # Example usage
    runner = A_OptimizerRunner()
    
    # Load data
    data = runner.load_data()
    
    if data is not None:
        # Run full optimization
        results = runner.run_full_optimization(data, max_params=50)
        
        if results:
            print("\nOptimization Results:")
            print(f"Detection: {results['detection']}")
            print(f"Range: {results['range']}")
            print(f"Breakout: {results['breakout']}")
            
            # Apply strategy to get signals
            signals = runner.apply_strategy(data)
            
            print(f"\nFound {len(signals)} trading signals")
            
            # Print first 5 signals
            for i, signal in enumerate(signals[:5]):
                print(f"\nSignal {i+1}:")
                print(f"Key Candle Index: {signal['index']}")
                print(f"Range: {signal['range_data']['range_lower']} - {signal['range_data']['range_upper']}")
                
                for s in signal['signals']:
                    print(f"  Breakout: {s['direction']} at price {s['price']}, valid: {s['is_valid']}")
    else:
        print("Failed to load data")
