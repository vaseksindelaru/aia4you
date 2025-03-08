# gridCandleRebound.py
from apis.detect_candle import detect_candlesticks
import pandas as pd

def grid_search(data, volume_windows, height_windows):
    best_score = -1
    best_params = {}
    df = pd.DataFrame(data)
    for vw in volume_windows:
        for hw in height_windows:
            filtered_data = detect_candlesticks(df, volume_window=vw, height_window=hw)
            score = len(filtered_data) / len(df)
            if score > best_score:
                best_score = score
                best_params = {'volume_window': vw, 'height_window': hw}
    return {'best_params': best_params, 'score': best_score}