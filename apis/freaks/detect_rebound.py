import pandas as pd

class ReboteDetector:
    def __init__(self, db_manager, config_loader, detection_strategy):
        self.db = db_manager
        self.config = config_loader.get_detection_params()
        self.strategy = detection_strategy

    def find_zones(self, df):
        df_filtered = self.strategy.find_zones(df)
        self.db.save_data(df_filtered)
        return df_filtered

    def confirm_rebote(self, df, index):
        intermedias_window = self.config["intermedias_window"]
        vela_i = df.iloc[index]
        promedio_precio = (vela_i['high'] + vela_i['low']) / 2
        direccion = 'alcista' if vela_i['close'] > vela_i['open'] else 'bajista'

        for i in range(index + intermedias_window + 1, len(df)):
            vela_actual = df.iloc[i]
            if vela_actual['low'] <= promedio_precio <= vela_actual['high']:
                if direccion == 'alcista' and vela_actual['close'] > promedio_precio:
                    return i
                elif direccion == 'bajista' and vela_actual['close'] < promedio_precio:
                    return i
        return None
