class ReboteEvaluator:
    def __init__(self, config_loader, evaluation_strategy):
        self.config = config_loader.get_evaluation_params()
        self.strategy = evaluation_strategy

    def evaluate(self, df, index, rebote_index, inicial_price, signo):
        return self.strategy.evaluate(df, index, rebote_index, inicial_price, signo)

    def calculate_next_avg(self, df, index, siguientes_window=2):
        """
        Calcula el promedio de las dos velas siguientes.
        """
        if index + siguientes_window < len(df):
            promedio_siguiente = df['close'].iloc[index + 1:index + siguientes_window + 1].mean()
            return promedio_siguiente
        return None

    def calculate_intermediate_avg(self, df, index_start, index_end):
        """
        Calcula el promedio de velas intermedias.
        """
        if index_start + 1 < index_end:
            velas_intermedias = df.iloc[index_start + 1:index_end]
            return velas_intermedias['close'].mean()
        return None

    def evaluate_success(self, promedio_siguiente, rebote_close, inicial_price, signo):
        """
        Calcula el éxito del rebote.
        """
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
