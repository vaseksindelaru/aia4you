# detect_rebound.py
import pandas as pd

def evaluar_rebote(data, index, siguientes_window=2):
    df = pd.DataFrame(data)
    vela_i = df.iloc[index]
    promedio_precio = (vela_i['high'] + vela_i['low']) / 2
    for i in range(index + 2, len(df)):
        vela_actual = df.iloc[i]
        if vela_actual['low'] <= promedio_precio <= vela_actual['high']:
            promedio_intermedias = df['close'].iloc[index + 1:i].mean()
            promedio_siguientes = df['close'].iloc[i + 1:i + 1 + siguientes_window].mean()
            if (promedio_intermedias < promedio_precio and promedio_siguientes < promedio_precio) or \
               (promedio_intermedias > promedio_precio and promedio_siguientes > promedio_precio):
                return 1
            else:
                return 0
    return 0