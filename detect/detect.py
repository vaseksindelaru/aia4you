"""
detect.py - Shakeout Strategy Detection Module (Standalone Copy)

Key candles are identified by high volume and small body, which often indicate
potential market reversals or continuation patterns.
"""

import pandas as pd
import numpy as np
import os

class Detector:
    """
    Detector class for identifying key candles in the Shakeout strategy (standalone).
    """
    def __init__(self, csv_path=None):
        self.detection_params = {}
        self.detection_data = {}
        self.results = []
        self.data = None
        if csv_path:
            self.load_csv(csv_path)

    def load_csv(self, csv_path):
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        # Nombres de columna esperados en el formato original de Binance
        binance_columns = [
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ]
        # Lee el archivo como CSV sin encabezado y asigna nombres
        self.data = pd.read_csv(csv_path, names=binance_columns, header=None)
        # Elimina la columna 'timestamp' si está presente
        if self.data.columns[0] in ['timestamp', 'open_time']:
            self.data = self.data.iloc[:, 1:]
        # Verifica columnas requeridas
        required_cols = {'open', 'high', 'low', 'close', 'volume'}
        if not required_cols.issubset(self.data.columns):
            raise ValueError(f"CSV missing required columns: {required_cols - set(self.data.columns)}")
        # Documentación: Ahora soporta archivos CSV de Binance sin encabezado, asignando nombres automáticamente.

    def set_detection_params(self, volume_percentile_threshold=80, body_percentage_threshold=30, lookback_candles=50):
        self.detection_params = {
            'volume_percentile_threshold': volume_percentile_threshold,
            'body_percentage_threshold': body_percentage_threshold,
            'lookback_candles': lookback_candles
        }

    def detect_key_candle(self, index):
        params = self.detection_params
        vpt = params.get('volume_percentile_threshold', 80)
        bpt = params.get('body_percentage_threshold', 30)
        lookback = params.get('lookback_candles', 50)
        if self.data is None or index < lookback:
            return False
        volume_percentile = np.percentile(self.data['volume'].iloc[index - lookback:index], vpt)
        current = self.data.iloc[index]
        current_volume = current['volume']
        current_body_size = abs(current['close'] - current['open'])
        current_range = current['high'] - current['low']
        if current_range == 0:
            return False
        body_percentage = 100 * current_body_size / current_range
        is_high_volume = current_volume >= volume_percentile
        is_small_body = body_percentage <= bpt
        return is_high_volume and is_small_body

    def process_csv(self):
        if self.data is None:
            return []
        key_candles = []
        params = self.detection_params
        vpt = params.get('volume_percentile_threshold', 80)
        bpt = params.get('body_percentage_threshold', 30)
        lookback = params.get('lookback_candles', 50)
        for idx in range(len(self.data)):
            if idx < lookback:
                continue
            volume_percentile = float(np.percentile(self.data['volume'].iloc[idx - lookback:idx], vpt))
            current = self.data.iloc[idx]
            current_volume = float(current['volume'])
            current_body_size = abs(float(current['close']) - float(current['open']))
            current_range = float(current['high']) - float(current['low'])
            if current_range == 0:
                continue
            body_percentage = 100 * current_body_size / current_range
            is_high_volume = current_volume >= volume_percentile
            is_small_body = body_percentage <= bpt
            is_key_candle = is_high_volume and is_small_body
            if is_key_candle:
                key_candles.append({
                    'index': idx,
                    'open': float(current['open']),
                    'high': float(current['high']),
                    'low': float(current['low']),
                    'close': float(current['close']),
                    'volume': current_volume,
                    'volume_percentile': volume_percentile,
                    'body_percentage': body_percentage,
                    'is_key_candle': is_key_candle
                })
        return key_candles

# Example usage (standalone):
# detector = Detector('your_file.csv')
# detector.set_detection_params(80, 30, 50)
# results = detector.process_csv()
# print(results)
