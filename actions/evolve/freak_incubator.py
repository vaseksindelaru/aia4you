# freak_incubator.py
# Incuba y propone nuevas estrategias

import os
import yaml
import logging
import random
import json
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("freak_incubator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FreakIncubator:
    """
    Clase para incubar y proponer nuevas estrategias basadas en
    patrones exitosos y combinaciones innovadoras de indicadores.
    """
    
    def __init__(self, db_connection=None, template_dir=None):
        """
        Inicializa el incubador con conexión a la base de datos y directorio de plantillas.
        
        Args:
            db_connection: Conexión a la base de datos (opcional)
            template_dir (str): Directorio con plantillas de estrategias (opcional)
        """
        self.db_connection = db_connection
        self.template_dir = template_dir or os.path.join(os.path.dirname(__file__), 'templates')
        logger.info("FreakIncubator inicializado")
    
    def generate_strategy_proposal(self, market_type, timeframe, risk_profile='moderate'):
        """
        Genera una propuesta de nueva estrategia basada en parámetros específicos.
        
        Args:
            market_type (str): Tipo de mercado (trending, ranging, volatile)
            timeframe (str): Marco temporal (1m, 5m, 15m, 1h, 4h, 1d)
            risk_profile (str): Perfil de riesgo (conservative, moderate, aggressive)
            
        Returns:
            dict: Propuesta de estrategia
        """
        logger.info("Generando propuesta para mercado %s en timeframe %s con perfil %s", 
                   market_type, timeframe, risk_profile)
        
        # Seleccionar indicadores apropiados según el tipo de mercado
        indicators = self._select_indicators(market_type)
        
        # Generar condiciones de entrada/salida
        entry_conditions = self._generate_entry_conditions(indicators, market_type, risk_profile)
        exit_conditions = self._generate_exit_conditions(indicators, market_type, risk_profile)
        
        # Generar parámetros
        parameters = self._generate_parameters(indicators, timeframe)
        
        # Construir propuesta de estrategia
        strategy_name = f"{market_type.capitalize()} {self._get_random_strategy_type()} Strategy"
        
        strategy = {
            "name": strategy_name,
            "description": f"Estrategia para mercados {market_type} en timeframe {timeframe} con perfil de riesgo {risk_profile}",
            "market_type": market_type,
            "timeframe": timeframe,
            "risk_profile": risk_profile,
            "indicators": indicators,
            "parameters": parameters,
            "entry_conditions": entry_conditions,
            "exit_conditions": exit_conditions,
            "risk_management": self._generate_risk_management(risk_profile),
            "created_at": datetime.now().isoformat()
        }
        
        logger.info("Propuesta generada: %s", strategy_name)
        return strategy
    
    def _select_indicators(self, market_type):
        """
        Selecciona indicadores apropiados según el tipo de mercado.
        
        Args:
            market_type (str): Tipo de mercado
            
        Returns:
            list: Lista de indicadores seleccionados
        """
        # Indicadores por tipo de mercado
        indicator_sets = {
            "trending": ["Moving Average", "MACD", "ADX", "Bollinger Bands", "Parabolic SAR"],
            "ranging": ["RSI", "Stochastic", "CCI", "Bollinger Bands", "Williams %R"],
            "volatile": ["ATR", "Bollinger Bands", "Keltner Channels", "Momentum", "Volume"]
        }
        
        # Seleccionar un conjunto base de indicadores
        base_set = indicator_sets.get(market_type, indicator_sets["trending"])
        
        # Seleccionar un subconjunto aleatorio (entre 2 y 4 indicadores)
        num_indicators = random.randint(2, 4)
        selected = random.sample(base_set, min(num_indicators, len(base_set)))
        
        return selected
    
    def _generate_entry_conditions(self, indicators, market_type, risk_profile):
        """
        Genera condiciones de entrada basadas en los indicadores seleccionados.
        
        Args:
            indicators (list): Lista de indicadores
            market_type (str): Tipo de mercado
            risk_profile (str): Perfil de riesgo
            
        Returns:
            list: Condiciones de entrada
        """
        conditions = []
        
        # Generar condiciones basadas en los indicadores
        for indicator in indicators:
            if indicator == "Moving Average":
                conditions.append("fast_ma crosses above slow_ma")
            elif indicator == "MACD":
                conditions.append("MACD line crosses above signal line")
            elif indicator == "RSI":
                threshold = 30 if risk_profile == "aggressive" else 35 if risk_profile == "moderate" else 40
                conditions.append(f"RSI crosses above {threshold}")
            elif indicator == "Bollinger Bands":
                if market_type == "ranging":
                    conditions.append("price touches lower Bollinger Band")
                else:
                    conditions.append("price breaks above upper Bollinger Band")
            # Añadir más condiciones para otros indicadores
        
        return conditions
    
    def _generate_exit_conditions(self, indicators, market_type, risk_profile):
        """
        Genera condiciones de salida basadas en los indicadores seleccionados.
        
        Args:
            indicators (list): Lista de indicadores
            market_type (str): Tipo de mercado
            risk_profile (str): Perfil de riesgo
            
        Returns:
            list: Condiciones de salida
        """
        conditions = []
        
        # Generar condiciones basadas en los indicadores
        for indicator in indicators:
            if indicator == "Moving Average":
                conditions.append("fast_ma crosses below slow_ma")
            elif indicator == "MACD":
                conditions.append("MACD line crosses below signal line")
            elif indicator == "RSI":
                threshold = 70 if risk_profile == "aggressive" else 65 if risk_profile == "moderate" else 60
                conditions.append(f"RSI crosses above {threshold}")
            # Añadir más condiciones para otros indicadores
        
        # Añadir condiciones de take profit y stop loss
        conditions.append("take profit reached (defined in risk management)")
        conditions.append("stop loss triggered (defined in risk management)")
        
        return conditions
    
    def _generate_parameters(self, indicators, timeframe):
        """
        Genera parámetros para los indicadores basados en el timeframe.
        
        Args:
            indicators (list): Lista de indicadores
            timeframe (str): Marco temporal
            
        Returns:
            dict: Parámetros para los indicadores
        """
        parameters = {}
        
        # Factor de ajuste según timeframe
        timeframe_factors = {
            "1m": 0.2, "5m": 0.4, "15m": 0.6, "1h": 1.0, "4h": 1.5, "1d": 2.0
        }
        factor = timeframe_factors.get(timeframe, 1.0)
        
        # Generar parámetros para cada indicador
        for indicator in indicators:
            if indicator == "Moving Average":
                parameters["fast_period"] = int(10 * factor)
                parameters["slow_period"] = int(30 * factor)
            elif indicator == "MACD":
                parameters["macd_fast"] = int(12 * factor)
                parameters["macd_slow"] = int(26 * factor)
                parameters["macd_signal"] = int(9 * factor)
            elif indicator == "RSI":
                parameters["rsi_period"] = int(14 * factor)
            elif indicator == "Bollinger Bands":
                parameters["bb_period"] = int(20 * factor)
                parameters["bb_deviation"] = 2.0
            # Añadir más parámetros para otros indicadores
        
        return parameters
    
    def _generate_risk_management(self, risk_profile):
        """
        Genera reglas de gestión de riesgo según el perfil.
        
        Args:
            risk_profile (str): Perfil de riesgo
            
        Returns:
            dict: Reglas de gestión de riesgo
        """
        risk_rules = {}
        
        # Configurar reglas según perfil de riesgo
        if risk_profile == "conservative":
            risk_rules["position_size"] = "1% del capital"
            risk_rules["stop_loss"] = "2% del capital"
            risk_rules["take_profit"] = "3% del capital"
        elif risk_profile == "moderate":
            risk_rules["position_size"] = "2% del capital"
            risk_rules["stop_loss"] = "3% del capital"
            risk_rules["take_profit"] = "5% del capital"
        elif risk_profile == "aggressive":
            risk_rules["position_size"] = "5% del capital"
            risk_rules["stop_loss"] = "5% del capital"
            risk_rules["take_profit"] = "10% del capital"
        
        risk_rules["trailing_stop"] = True if risk_profile != "conservative" else False
        
        return risk_rules
    
    def _get_random_strategy_type(self):
        """
        Devuelve un tipo de estrategia aleatorio para el nombre.
        
        Returns:
            str: Tipo de estrategia
        """
        strategy_types = [
            "Momentum", "Reversal", "Breakout", "Trend Following", 
            "Mean Reversion", "Oscillator", "Divergence", "Volume"
        ]
        return random.choice(strategy_types)
    
    def export_to_yaml(self, strategy):
        """
        Exporta una estrategia a formato YAML.
        
        Args:
            strategy (dict): Estrategia a exportar
            
        Returns:
            str: Contenido YAML de la estrategia
        """
        return yaml.dump(strategy, sort_keys=False)

# Función principal para ejecutar desde línea de comandos
def main():
    """Punto de entrada principal para ejecución desde línea de comandos"""
    incubator = FreakIncubator()
    
    # Generar una estrategia de ejemplo
    strategy = incubator.generate_strategy_proposal(
        market_type="trending",
        timeframe="1h",
        risk_profile="moderate"
    )
    
    # Exportar a YAML y mostrar
    yaml_content = incubator.export_to_yaml(strategy)
    print("Estrategia generada:")
    print(yaml_content)

if __name__ == "__main__":
    main()
