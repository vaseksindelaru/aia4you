# detect_candle.py
import pandas as pd

def detect_candlesticks(data, volume_window=2, height_window=2):  # Reducido de 5 a 2 para datos pequeños
    df = pd.DataFrame(data)
    df['Total_Height'] = df['high'] - df['low']
    df['Volume_SMA'] = df['volume'].rolling(window=volume_window, min_periods=1).mean()  # min_periods=1 para pocos datos
    df['Total_Height_SMA'] = df['Total_Height'].rolling(window=height_window, min_periods=1).mean()
    df['High_Volume'] = df['volume'] > df['Volume_SMA']
    df['Small_Body'] = df['Total_Height'] < df['Total_Height_SMA']
    df_filtered = df[df['High_Volume'] & df['Small_Body']].copy()
    if df_filtered.empty:  # Si no hay velas filtradas, devolver todas para pruebas
        return df.to_dict(orient='records')
    return df_filtered.to_dict(orient='records')