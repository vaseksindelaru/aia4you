"""
Test script for the Shakeout strategy detection module using real CSV data (standalone).
"""
from detect import Detector
import pandas as pd
import numpy as np
import os

def main():
    print("Testing Shakeout Strategy Detector with real CSV data (standalone)...")
    detector = Detector('sample_data.csv')
    detector.set_detection_params(
        volume_percentile_threshold=80,
        body_percentage_threshold=30,
        lookback_candles=20
    )
    print("Detector initialized with parameters:")
    print(f"  - volume_percentile_threshold: {detector.detection_params['volume_percentile_threshold']}")
    print(f"  - body_percentage_threshold: {detector.detection_params['body_percentage_threshold']}")
    print(f"  - lookback_candles: {detector.detection_params['lookback_candles']}")
    results = detector.process_csv()
    if results:
        print(f"\nKey candles detected: {len(results)}")
        for i, candle in enumerate(results):
            print(f"Key candle {i+1}: Index: {candle['index']}, Volume: {candle['volume']:.2f}, Open: {candle['open']:.2f}, Close: {candle['close']:.2f}")
    else:
        print("\nNo key candles detected.")

if __name__ == "__main__":
    main()
