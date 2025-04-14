"""
Test script for the Shakeout strategy detection module.

This script creates sample data and tests the key candle detection functionality.
"""

import pandas as pd
import numpy as np
from detect import Detector

# Create sample data
def create_sample_data(num_candles=100):
    """Create sample OHLCV data for testing."""
    np.random.seed(42)  # For reproducibility
    
    # Base price and random walk
    base_price = 10000
    random_walk = np.cumsum(np.random.normal(0, 100, num_candles))
    
    # Generate OHLCV data
    data = []
    for i in range(num_candles):
        # Price components
        price = base_price + random_walk[i]
        range_size = abs(np.random.normal(0, 50))
        body_size = range_size * np.random.uniform(0.1, 0.9)  # Body size as percentage of range
        
        # Volume (mostly normal with occasional spikes)
        volume = abs(np.random.normal(1000, 200))
        if np.random.random() < 0.1:  # 10% chance of volume spike
            volume *= np.random.uniform(2, 5)
        
        # Create key candles occasionally (high volume, small body)
        if np.random.random() < 0.05:  # 5% chance of key candle
            volume *= np.random.uniform(3, 6)  # Higher volume
            body_size = range_size * np.random.uniform(0.05, 0.2)  # Smaller body
        
        # Determine open, high, low, close
        high = price + range_size/2
        low = price - range_size/2
        
        if np.random.random() < 0.5:  # 50% chance of bullish candle
            open_price = low + (range_size - body_size) * np.random.uniform(0, 1)
            close = open_price + body_size
        else:  # 50% chance of bearish candle
            close = low + (range_size - body_size) * np.random.uniform(0, 1)
            open_price = close + body_size
        
        data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    return pd.DataFrame(data)

# Test the detector
def test_detector():
    """Test the Detector class with sample data."""
    print("Testing Shakeout Strategy Detector...")
    
    # Create sample data
    df = create_sample_data(100)
    print(f"Created sample data with {len(df)} candles")
    
    # Initialize detector
    detector = Detector()
    detector.data = df
    detector.set_detection_params(
        volume_percentile_threshold=80,
        body_percentage_threshold=30,
        lookback_candles=20
    )
    print("Detector initialized with parameters:")
    print(f"  - volume_percentile_threshold: {detector.detection_params['volume_percentile_threshold']}")
    print(f"  - body_percentage_threshold: {detector.detection_params['body_percentage_threshold']}")
    print(f"  - lookback_candles: {detector.detection_params['lookback_candles']}")
    
    # Test detection on all candles
    key_candles = []
    for i in range(len(df)):
        if i < detector.detection_params['lookback_candles']:
            continue  # Skip initial candles where we don't have enough history
        
        is_key = detector.detect_key_candle(i)
        if is_key:
            key_candles.append(i)
            print(f"\nKey candle detected at index {i}:")
            print(f"  - Volume: {detector.detection_data['current_volume']:.2f} (Percentile: {detector.detection_data['volume_percentile']:.2f})")
            print(f"  - Body size: {detector.detection_data['current_body_size']:.2f}")
            print(f"  - Range: {detector.detection_data['current_range']:.2f}")
            print(f"  - Body percentage: {detector.detection_data['body_percentage']:.2f}%")
    
    print(f"\nDetected {len(key_candles)} key candles out of {len(df)} total candles ({len(key_candles)/len(df)*100:.2f}%)")
    print(f"Key candle indices: {key_candles}")

if __name__ == "__main__":
    test_detector()
