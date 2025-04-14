"""
detect.py - Shakeout Strategy Detection Module

This module provides functionality to detect key candles for the Shakeout strategy.
Key candles are identified by high volume and small body, which often indicate
potential market reversals or continuation patterns.
"""

import pandas as pd
import numpy as np
import os


class Detector:
    """
    Detector class for identifying key candles in the Shakeout strategy.

    This class analyzes price and volume data to detect candles with high volume
    and small body relative to their range, which are potential indicators of
    market manipulation or significant price action.
    """

    def __init__(self, csv_path="data/models/strategies/klines/BTCUSDT-5m-2025-04-10.csv"):
        """
        Initialize the Detector with data from a CSV file.

        Parameters:
        -----------
        csv_path : str
            Path to the CSV file containing OHLCV data.
        """
        self.detection_params = {}
        self.detection_data = {}
        self.results = []

        # Load data from CSV if path is provided
        if csv_path:
            self.load_csv(csv_path)

    def set_detection_params(self, volume_percentile_threshold=80, body_percentage_threshold=30, lookback_candles=50):
        """
        Set parameters for key candle detection.

        Parameters:
        -----------
        volume_percentile_threshold : float
            The percentile threshold for volume (0-100). Candles with volume above this
            percentile are considered high volume candles.
        body_percentage_threshold : float
            The maximum percentage of body size relative to the candle's range.
            Candles with body percentage below this threshold are considered small body candles.
        lookback_candles : int
            Number of previous candles to consider when calculating volume percentile.

        Returns:
        --------
        None
        """
        self.detection_params = {
            'volume_percentile_threshold': volume_percentile_threshold,
            'body_percentage_threshold': body_percentage_threshold,
            'lookback_candles': lookback_candles
        }

    def detect_key_candle(self, index):
        """
        Evaluate if the candle at the specified index is a key candle.

        A key candle has high volume and small body relative to its range.

        Parameters:
        -----------
        index : int
            The index of the candle to evaluate in the data DataFrame.

        Returns:
        --------
        bool
            True if the candle is a key candle, False otherwise.
        """
        # Get parameters
        volume_percentile_threshold = self.detection_params.get('volume_percentile_threshold', 80)
        body_percentage_threshold = self.detection_params.get('body_percentage_threshold', 30)
        lookback_candles = self.detection_params.get('lookback_candles', 50)

        # Check if we have enough historical data
        if index < lookback_candles or self.data is None:
            self.detection_data = {
                'error': 'Insufficient historical data or data not set',
                'is_key_candle': False
            }
            return False

        # Calculate lookback range
        lookback = min(lookback_candles, index)

        try:
            # Calculate volume percentile
            volume_percentile = np.percentile(
                self.data['volume'].iloc[index - lookback:index],
                volume_percentile_threshold
            )

            # Get current candle data
            current_volume = self.data['volume'].iloc[index]
            current_body_size = abs(self.data['close'].iloc[index] - self.data['open'].iloc[index])
            current_range = self.data['high'].iloc[index] - self.data['low'].iloc[index]

            # Check if volume is high
            is_high_volume = current_volume > volume_percentile

            # Check if body is small relative to range
            is_small_body = False
            if current_range > 0:  # Avoid division by zero
                body_percentage = (current_body_size / current_range) * 100
                is_small_body = body_percentage < body_percentage_threshold

            # Determine if this is a key candle
            is_key_candle = is_high_volume and is_small_body

            # Store detection data for analysis
            self.detection_data = {
                'current_volume': current_volume,
                'current_body_size': current_body_size,
                'current_range': current_range,
                'volume_percentile': volume_percentile,
                'body_percentage': body_percentage if current_range > 0 else None,
                'is_high_volume': is_high_volume,
                'is_small_body': is_small_body,
                'is_key_candle': is_key_candle
                # Future correlation data could include:
                # 'is_buyer_maker': self.data['is_buyer_maker'].iloc[index] if 'is_buyer_maker' in self.data.columns else None,
                # 'imbalance': self.data['imbalance'].iloc[index] if 'imbalance' in self.data.columns else None
            }

            return is_key_candle

        except Exception as e:
            self.detection_data = {
                'error': str(e),
                'is_key_candle': False
            }
            return False

    def load_csv(self, csv_path):
        """
        Load and prepare data from a CSV file.

        Parameters:
        -----------
        csv_path : str
            Path to the CSV file containing OHLCV data.

        Returns:
        --------
        bool
            True if data was loaded successfully, False otherwise.
        """
        try:
            # Check if file exists
            if not os.path.exists(csv_path):
                # Try with absolute path from project root
                root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                full_path = os.path.join(root_path, csv_path)
                if not os.path.exists(full_path):
                    raise FileNotFoundError(f"CSV file not found at {csv_path} or {full_path}")
                csv_path = full_path

            # Load CSV data
            # For Binance format: timestamp,open,high,low,close,volume,close_time,quote_asset_volume,trades,taker_buy_base,taker_buy_quote,ignored
            column_names = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                           'quote_asset_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignored']

            self.data = pd.read_csv(csv_path, header=None, names=column_names)

            # Verify required columns exist
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in self.data.columns:
                    # Try to find case-insensitive match and rename
                    for existing_col in self.data.columns:
                        if existing_col.lower() == col:
                            self.data.rename(columns={existing_col: col}, inplace=True)
                            break
                    else:  # No match found
                        raise ValueError(f"Required column '{col}' not found in CSV data")

            print(f"Successfully loaded data from {csv_path} with {len(self.data)} candles")
            return True

        except Exception as e:
            print(f"Error loading CSV data: {str(e)}")
            self.data = None
            return False

    def process_csv(self):
        """
        Process the entire CSV data to detect key candles.

        Iterates through all valid indices in the data (those with enough history)
        and detects key candles. Results are stored in self.results list.

        Returns:
        --------
        list
            List of dictionaries containing detection data for key candles.
        """
        if self.data is None:
            print("No data available. Please initialize with a valid CSV file.")
            return []

        # Get lookback parameter
        lookback_candles = self.detection_params.get('lookback_candles', 50)

        # Reset results
        self.results = []

        # Process each valid candle
        for index in range(lookback_candles, len(self.data)):
            is_key = self.detect_key_candle(index)

            # If it's a key candle, store the result with index information
            if is_key:
                result_data = self.detection_data.copy()
                result_data['index'] = index
                result_data['timestamp'] = self.data['timestamp'].iloc[index] if 'timestamp' in self.data.columns else None
                self.results.append(result_data)

        print(f"Detected {len(self.results)} key candles out of {len(self.data) - lookback_candles} valid candles "
              f"({len(self.results)/(len(self.data) - lookback_candles)*100:.2f}%)")

        return self.results


# Example usage:
# detector = Detector()  # Will load data from default CSV path
# detector.set_detection_params(80, 30, 50)
# detector.process_csv()
# print(detector.results)
