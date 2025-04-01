class FreakIncubator:
    def __init__(self, version_manager):
        self.version_manager = version_manager
        self.historical_results = []

    def incubate(self, result):
        self.historical_results.append(result)
        if len(self.historical_results) >= 50:  # Evalúa cada 50 operaciones
            wins = sum(1 for r in self.historical_results if r["profit"] > 0)
            win_rate = wins / len(self.historical_results)
            if win_rate < 0.6:  # Si la tasa de éxito es baja, propone una nueva estrategia
                new_strategy = "RSIBasedDetectionStrategy"  # Ejemplo
                self.version_manager.save_version({"strategy": new_strategy}, "detection", win_rate)
            self.historical_results = self.historical_results[-50:]  # Mantiene solo los últimos 50
