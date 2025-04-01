class FreakOptimizer:
    def __init__(self, config_loader, version_manager):
        self.config_loader = config_loader
        self.version_manager = version_manager
        self.recent_results = []

    def optimize(self, result):
        self.recent_results.append(result)
        if len(self.recent_results) >= 5:  # Evalúa cada 5 operaciones
            wins = sum(1 for r in self.recent_results if r["profit"] > 0)
            win_rate = wins / len(self.recent_results)
            if win_rate < 0.6:  # Si la tasa de éxito es baja, ajusta parámetros
                config = self.config_loader.get_detection_params()
                config["volume_sma_window"] += 1
                config["height_sma_window"] += 1
                self.version_manager.save_version(config, "detection", win_rate)
            self.recent_results = []  # Reinicia los resultados
