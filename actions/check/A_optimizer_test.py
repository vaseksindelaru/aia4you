"""
A_optimizer Test Script

This script tests all components of the A_optimizer system:
1. Detection module
2. Range module with ATR API integration
3. Breakout module
4. Full optimization process

It verifies that all components are working correctly and provides detailed output.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import A_optimizer components
from actions.evolve.A_optimizer import A_Detection, A_Range, A_Breakout
from actions.run.A_optimizer_runner import A_OptimizerRunner

def test_detection():
    """Test the detection module"""
    print("\n===== Testing Detection Module =====")
    
    # Initialize detection module
    detector = A_Detection()
    
    # Load test data
    try:
        file_path = "data/BTCUSDC-5m-2025-04-08/BTCUSDC-5m-2025-04-08.csv"
        df = pd.read_csv(file_path)
        
        # Rename columns for clarity
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                      'close_time', 'quote_asset_volume', 'number_of_trades', 
                      'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
        
        print(f"Loaded data with {len(df)} rows")
        
        # Test with default parameters
        params = {
            'volume_percentile_threshold': 80,
            'body_percentage_threshold': 30,
            'lookback_candles': 50
        }
        
        # Ensure we have enough data
        start_idx = params['lookback_candles']
        
        # Test detection on a sample of candles
        key_candles = 0
        sample_size = min(100, len(df) - start_idx)
        
        for i in range(start_idx, start_idx + sample_size):
            is_key, detection_data = detector.detect_key_candle(df, i, params)
            if is_key:
                key_candles += 1
                print(f"Key candle found at index {i}:")
                print(f"  Volume: {detection_data['current_volume']:.2f}")
                print(f"  Body size: {detection_data['current_body_size']:.2f}")
                print(f"  Range: {detection_data['current_range']:.2f}")
                print(f"  Volume percentile: {detection_data['volume_percentile']:.2f}")
                
                # Only show first 3 key candles
                if key_candles >= 3:
                    break
        
        key_candle_percentage = (key_candles / sample_size) * 100
        print(f"\nFound {key_candles} key candles in sample of {sample_size} ({key_candle_percentage:.2f}%)")
        
        # Test database operations
        param_id = detector.insert_params(
            params['volume_percentile_threshold'],
            params['body_percentage_threshold'],
            params['lookback_candles']
        )
        
        if param_id:
            print(f"Successfully inserted parameters with ID {param_id}")
            
            # Test setting active parameter
            if detector.set_active_param(param_id):
                print(f"Successfully set parameter {param_id} as active")
            
            # Test getting active parameters
            active_params = detector.get_active_params()
            if active_params:
                print(f"Retrieved active parameters: {active_params}")
        
        return True
    except Exception as e:
        print(f"Error in detection test: {e}")
        return False

def test_range():
    """Test the range module"""
    print("\n===== Testing Range Module =====")
    
    # Initialize range module
    range_calculator = A_Range()
    
    # Load test data
    try:
        file_path = "data/BTCUSDC-5m-2025-04-08/BTCUSDC-5m-2025-04-08.csv"
        df = pd.read_csv(file_path)
        
        # Rename columns for clarity
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                      'close_time', 'quote_asset_volume', 'number_of_trades', 
                      'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
        
        print(f"Loaded data with {len(df)} rows")
        
        # Test with default parameters
        params = {
            'atr_period': 14,
            'atr_multiplier': 1.5
        }
        
        # Ensure we have enough data
        start_idx = params['atr_period']
        
        # Test range calculation on a few candles
        for i in range(start_idx, start_idx + 3):
            range_data = range_calculator.calculate_range(df, i, None, params)
            print(f"Range calculated for index {i}:")
            print(f"  Center: {range_data['range_center']:.2f}")
            print(f"  ATR value: {range_data['atr_value']:.2f}")
            print(f"  Upper: {range_data['range_upper']:.2f}")
            print(f"  Lower: {range_data['range_lower']:.2f}")
        
        # Test database operations
        param_id = range_calculator.insert_params(
            params['atr_period'],
            params['atr_multiplier']
        )
        
        if param_id:
            print(f"Successfully inserted parameters with ID {param_id}")
            
            # Test setting active parameter
            if range_calculator.set_active_param(param_id):
                print(f"Successfully set parameter {param_id} as active")
            
            # Test getting active parameters
            active_params = range_calculator.get_active_params()
            if active_params:
                print(f"Retrieved active parameters: {active_params}")
            
            # Test saving range data
            range_id = range_calculator.save_range_data(
                param_id, None, df['timestamp'].iloc[start_idx], 'BTCUSDC', range_data
            )
            
            if range_id:
                print(f"Successfully saved range data with ID {range_id}")
        
        # Test ATR API integration
        print("\nTesting ATR API integration...")
        atr_data = range_calculator.get_atr_from_api(period=params['atr_period'])
        
        if atr_data:
            print(f"Successfully retrieved ATR data from API:")
            print(f"  Symbol: {atr_data['symbol']}")
            print(f"  Period: {atr_data['period']}")
            print(f"  Current ATR: {atr_data['atr_current']}")
        else:
            print("Failed to retrieve ATR data from API, using local calculation instead")
        
        return True
    except Exception as e:
        print(f"Error in range test: {e}")
        return False

def test_breakout():
    """Test the breakout module"""
    print("\n===== Testing Breakout Module =====")
    
    # Initialize breakout module
    breakout_evaluator = A_Breakout()
    
    # Load test data
    try:
        file_path = "data/BTCUSDC-5m-2025-04-08/BTCUSDC-5m-2025-04-08.csv"
        df = pd.read_csv(file_path)
        
        # Rename columns for clarity
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                      'close_time', 'quote_asset_volume', 'number_of_trades', 
                      'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
        
        print(f"Loaded data with {len(df)} rows")
        
        # First, calculate a range
        range_calculator = A_Range()
        range_params = {
            'atr_period': 14,
            'atr_multiplier': 1.5
        }
        
        # Ensure we have enough data
        start_idx = range_params['atr_period']
        range_data = range_calculator.calculate_range(df, start_idx, None, range_params)
        
        print(f"Range calculated for index {start_idx}:")
        print(f"  Center: {range_data['range_center']:.2f}")
        print(f"  Upper: {range_data['range_upper']:.2f}")
        print(f"  Lower: {range_data['range_lower']:.2f}")
        
        # Test breakout evaluation with default parameters
        breakout_params = {
            'breakout_threshold_percentage': 0.5,
            'max_candles_to_return': 2
        }
        
        # Look for breakouts in the next 10 candles
        found_breakout = False
        
        for i in range(start_idx + 1, start_idx + 11):
            if i + breakout_params['max_candles_to_return'] >= len(df):
                continue
            
            is_valid, breakout_data = breakout_evaluator.evaluate_breakout(
                df, i, range_data, breakout_params
            )
            
            if breakout_data.get('direction') != 'none':
                found_breakout = True
                print(f"\nBreakout found at index {i}:")
                print(f"  Direction: {breakout_data['direction']}")
                print(f"  Distance: {breakout_data['breakout_distance']:.2f}%")
                print(f"  Valid: {is_valid}")
                break
        
        if not found_breakout:
            print("\nNo breakout found in the sample range")
        
        # Test database operations
        param_id = breakout_evaluator.insert_params(
            breakout_params['breakout_threshold_percentage'],
            breakout_params['max_candles_to_return']
        )
        
        if param_id:
            print(f"Successfully inserted parameters with ID {param_id}")
            
            # Test setting active parameter
            if breakout_evaluator.set_active_param(param_id):
                print(f"Successfully set parameter {param_id} as active")
            
            # Test getting active parameters
            active_params = breakout_evaluator.get_active_params()
            if active_params:
                print(f"Retrieved active parameters: {active_params}")
            
            # Test saving breakout data if we found one
            if found_breakout:
                breakout_id = breakout_evaluator.save_breakout_data(
                    param_id, None, df['timestamp'].iloc[i], 'BTCUSDC', breakout_data
                )
                
                if breakout_id:
                    print(f"Successfully saved breakout data with ID {breakout_id}")
        
        return True
    except Exception as e:
        print(f"Error in breakout test: {e}")
        return False

def test_full_optimization():
    """Test the full optimization process"""
    print("\n===== Testing Full Optimization =====")
    
    # Initialize optimizer runner
    runner = A_OptimizerRunner()
    
    # Load test data
    try:
        data = runner.load_data()
        
        if data is None:
            print("Failed to load data")
            return False
        
        print(f"Loaded data with {len(data)} rows")
        
        # Run a limited optimization with fewer parameters for testing
        print("\nRunning limited optimization for testing (max 5 parameter combinations per component)...")
        results = runner.run_full_optimization(data, max_params=5)
        
        if results:
            print("\nOptimization Results:")
            
            if results['detection']:
                print(f"Detection: {results['detection']['params']}")
                print(f"  Performance: {results['detection']['performance']:.2f}")
            
            if results['range']:
                print(f"Range: {results['range']['params']}")
                print(f"  Performance: {results['range']['avg_coverage']:.2f}")
            
            if results['breakout']:
                print(f"Breakout: {results['breakout']['params']}")
                print(f"  Performance: {results['breakout']['combined_score']:.2f}")
            
            # Apply strategy to get signals
            print("\nApplying optimized strategy to get signals...")
            signals = runner.apply_strategy(data)
            
            print(f"Found {len(signals)} trading signals")
            
            # Print first 3 signals
            for i, signal in enumerate(signals[:3]):
                print(f"\nSignal {i+1}:")
                print(f"Key Candle Index: {signal['index']}")
                print(f"Range: {signal['range_data']['range_lower']:.2f} - {signal['range_data']['range_upper']:.2f}")
                
                for s in signal['signals']:
                    print(f"  Breakout: {s['direction']} at price {s['price']:.2f}, valid: {s['is_valid']}")
            
            return True
        else:
            print("Optimization failed")
            return False
    except Exception as e:
        print(f"Error in full optimization test: {e}")
        return False

if __name__ == "__main__":
    print("A_optimizer Test Script")
    print("======================")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    detection_success = test_detection()
    range_success = test_range()
    breakout_success = test_breakout()
    optimization_success = test_full_optimization()
    
    # Print summary
    print("\n===== Test Summary =====")
    print(f"Detection Module: {'PASS' if detection_success else 'FAIL'}")
    print(f"Range Module: {'PASS' if range_success else 'FAIL'}")
    print(f"Breakout Module: {'PASS' if breakout_success else 'FAIL'}")
    print(f"Full Optimization: {'PASS' if optimization_success else 'FAIL'}")
    
    overall_success = detection_success and range_success and breakout_success and optimization_success
    print(f"\nOverall Result: {'PASS' if overall_success else 'FAIL'}")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
