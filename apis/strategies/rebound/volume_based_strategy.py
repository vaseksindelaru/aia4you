import pandas as pd

class VolumeBasedDetectionStrategy:
    def __init__(self, config):
        self.volume_sma_window = config["volume_sma_window"]
        self.height_sma_window = config["height_sma_window"]

    def find_zones(self, df):
        df['Total_Height'] = df['high'] - df['low']
        df['Volume_SMA'] = df['volume'].rolling(window=self.volume_sma_window).mean()
        df['Total_Height_SMA'] = df['Total_Height'].rolling(window=self.height_sma_window).mean()

        df['High_Volume'] = df['volume'] > df['Volume_SMA']
        df['Small_Body'] = df['Total_Height'] < df['Total_Height_SMA']

        df_filtered = df[df['High_Volume'] & df['Small_Body']].copy()
        return df_filtered.apply(pd.to_numeric, errors='coerce')
