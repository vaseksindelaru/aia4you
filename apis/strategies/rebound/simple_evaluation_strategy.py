class SimpleEvaluationStrategy:
    def __init__(self, config):
        self.siguientes_window = config["siguientes_window"]

    def calculate_next_avg(self, df, index):
        if index + self.siguientes_window < len(df):
            return df['close'].iloc[index + 1:index + self.siguientes_window + 1].mean()
        return None

    def calculate_intermediate_avg(self, df, index_start, index_end):
        if index_start + 1 < index_end:
            velas_intermedias = df.iloc[index_start + 1:index_end]
            return velas_intermedias['close'].mean()
        return None

    def evaluate_success(self, promedio_siguiente, rebote_close, inicial_price, signo):
        if (promedio_siguiente > rebote_close and rebote_close > inicial_price and signo == "-") or \
           (promedio_siguiente < rebote_close and rebote_close < inicial_price and signo == "+"):
            return "-"
        elif (promedio_siguiente < rebote_close and signo == "-") or \
             (promedio_siguiente > rebote_close and signo == "+"):
            return "+"
        elif (promedio_siguiente < rebote_close and rebote_close > promedio_siguiente and signo == "-") or \
             (promedio_siguiente > rebote_close and rebote_close < promedio_siguiente and signo == "+"):
            return "++"
        return None

    def evaluate(self, df, index, rebote_index, inicial_price, signo):
        promedio_siguiente = self.calculate_next_avg(df, rebote_index)
        promedio_intermedias = self.calculate_intermediate_avg(df, index, rebote_index)
        if promedio_siguiente and promedio_intermedias:
            rebote_close = df.iloc[rebote_index]['close']
            return self.evaluate_success(promedio_siguiente, rebote_close, inicial_price, signo)
        return None
