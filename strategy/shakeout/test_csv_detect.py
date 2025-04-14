"""
Test script for the Shakeout strategy detection module using real CSV data.

This script tests the key candle detection functionality with real market data.
"""

from detect import Detector
import pandas as pd
import numpy as np
import os

def main():
    """Main test function."""
    print("Testing Shakeout Strategy Detector with real CSV data...")
    
    # Initialize detector with default CSV path
    detector = Detector()
    
    # Set detection parameters
    detector.set_detection_params(
        volume_percentile_threshold=80,
        body_percentage_threshold=30,
        lookback_candles=20  # Using a smaller lookback for testing
    )
    print("Detector initialized with parameters:")
    print(f"  - volume_percentile_threshold: {detector.detection_params['volume_percentile_threshold']}")
    print(f"  - body_percentage_threshold: {detector.detection_params['body_percentage_threshold']}")
    print(f"  - lookback_candles: {detector.detection_params['lookback_candles']}")
    
    # Process the CSV data
    results = detector.process_csv()
    
    # Display results
    if results:
        print("\nKey candles detected:")
        for i, result in enumerate(results):
            print(f"\nKey candle {i+1}:")
            print(f"  - Index: {result['index']}")
            print(f"  - Timestamp: {result['timestamp']}")
            print(f"  - Volume: {result['current_volume']:.2f} (Percentile: {result['volume_percentile']:.2f})")
            print(f"  - Body size: {result['current_body_size']:.2f}")
            print(f"  - Range: {result['current_range']:.2f}")
            print(f"  - Body percentage: {result['body_percentage']:.2f}%")
    else:
        print("\nNo key candles detected.")

if __name__ == "__main__":
    main()
