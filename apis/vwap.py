# vwap.py
import pandas as pd

def calculate_vwap(data):
    df = pd.DataFrame(data)
    df['VWAP'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
    return df.to_dict(orient='records')