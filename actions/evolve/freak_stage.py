from core.data_fetcher import DataFetcher
from core.trading_simulator import TradingSimulator
from core.db_manager import DBManager
from actions.analyze.rebote_evaluator import ReboteEvaluator  # Actualizada la importación
from actions.evolve.config_loader import ConfigLoader
from actions.evolve.freak_optimizer import FreakOptimizer
from actions.evolve.freak_incubator import FreakIncubator
from actions.evolve.version_manager import VersionManager
from apis.freaks.detect_rebound import ReboteDetector
from apis.strategies.rebound.volume_based_strategy import VolumeBasedDetectionStrategy
from apis.strategies.rebound.simple_evaluation_strategy import SimpleEvaluationStrategy

class FreakStage:
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.db_manager = DBManager()
        self.data_fetcher = DataFetcher()
        self.trading_simulator = TradingSimulator()
        self.version_manager = VersionManager()
        detection_config = self.config_loader.get_detection_params()
        evaluation_config = self.config_loader.get_evaluation_params()
        self.detector = ReboteDetector(
            self.db_manager,
            self.config_loader,
            VolumeBasedDetectionStrategy(detection_config)
        )
        self.evaluator = ReboteEvaluator(
            self.config_loader,
            SimpleEvaluationStrategy(evaluation_config)
        )
        self.optimizer = FreakOptimizer(self.config_loader, self.version_manager)
        self.incubator = FreakIncubator(self.version_manager)
        self.performance = {"wins": 0, "losses": 0}

    def decide(self):
        df = self.data_fetcher.fetch_data()
        df_filtered = self.detector.find_zones(df)
        if df_filtered.empty:
            return "hold"

        for index in df_filtered.index:
            rebote_index = self.detector.confirm_rebote(df, index)
            if rebote_index:
                inicial_price = (df.iloc[index]['high'] + df.iloc[index]['low']) / 2
                signo = "+" if df.iloc[index]['close'] > df.iloc[index]['open'] else "-"
                exito = self.evaluator.evaluate(df, index, rebote_index, inicial_price, signo)
                if exito in ["+", "++"]:
                    action = "buy" if signo == "+" else "sell"
                    result = self.trading_simulator.execute(action)
                    self.update_from_execution(result)
                    return action
        return "hold"

    def update_from_execution(self, result):
        if result["profit"] > 0:
            self.performance["wins"] += 1
        else:
            self.performance["losses"] += 1
        self.optimizer.optimize(result)
        self.incubator.incubate(result)
