import numpy as np
import pandas as pd
import yaml
import logging
from typing import Dict, List, Tuple, Any, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RSIIndicator:
    """
    Clase para calcular el indicador RSI (Relative Strength Index)
    
    El RSI es un oscilador de momento que mide la velocidad y el cambio de los movimientos de precio.
    Oscila entre 0 y 100 y tradicionalmente se considera que el mercado está sobrecomprado cuando 
    está por encima de 70 y sobrevendido cuando está por debajo de 30.
    """
    
    def __init__(self, period: int = 14, overbought_threshold: float = 70.0, oversold_threshold: float = 30.0):
        """
        Inicializa el indicador RSI con los parámetros especificados.
        
        Args:
            period: Período para el cálculo del RSI (por defecto 14)
            overbought_threshold: Umbral para considerar sobrecompra (por defecto 70)
            oversold_threshold: Umbral para considerar sobreventa (por defecto 30)
        """
        self.period = period
        self.overbought_threshold = overbought_threshold
        self.oversold_threshold = oversold_threshold
        logger.info(f"RSI Indicator initialized with period={period}, overbought={overbought_threshold}, oversold={oversold_threshold}")
    
    def calculate(self, prices: pd.Series) -> pd.Series:
        """
        Calcula el RSI para una serie de precios.
        
        Args:
            prices: Serie de pandas con los precios de cierre
            
        Returns:
            Serie de pandas con los valores del RSI
        """
        # Calcular cambios en los precios
        delta = prices.diff()
        
        # Separar ganancias (positivos) y pérdidas (negativos)
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calcular la media móvil exponencial de ganancias y pérdidas
        avg_gain = gain.rolling(window=self.period).mean()
        avg_loss = loss.rolling(window=self.period).mean()
        
        # Calcular la fuerza relativa (RS)
        rs = avg_gain / avg_loss
        
        # Calcular el RSI
        rsi = 100 - (100 / (1 + rs))
        
        logger.info(f"RSI calculated successfully for {len(prices)} price points")
        return rsi
    
    def generate_signals(self, rsi_values: pd.Series) -> pd.Series:
        """
        Genera señales de trading basadas en los valores del RSI.
        
        Args:
            rsi_values: Serie de pandas con los valores del RSI
            
        Returns:
            Serie de pandas con las señales de trading:
                1: Señal de compra (RSI por debajo del umbral de sobreventa)
                0: Sin señal
                -1: Señal de venta (RSI por encima del umbral de sobrecompra)
        """
        signals = pd.Series(0, index=rsi_values.index)
        
        # Señales de compra (RSI por debajo del umbral de sobreventa)
        signals[rsi_values < self.oversold_threshold] = 1
        
        # Señales de venta (RSI por encima del umbral de sobrecompra)
        signals[rsi_values > self.overbought_threshold] = -1
        
        logger.info(f"Generated {signals.value_counts().get(1, 0)} buy signals and {signals.value_counts().get(-1, 0)} sell signals")
        return signals
    
    def get_config_yaml(self) -> str:
        """
        Devuelve la configuración del indicador en formato YAML.
        
        Returns:
            Cadena con la configuración YAML
        """
        config = {
            "indicator": "RSI",
            "parameters": {
                "period": self.period,
                "overbought_threshold": self.overbought_threshold,
                "oversold_threshold": self.oversold_threshold
            },
            "inputs": {
                "price": "close"
            },
            "conditions": {
                "buy": f"RSI < {self.oversold_threshold}",
                "sell": f"RSI > {self.overbought_threshold}"
            },
            "description": "Relative Strength Index (RSI) measures the magnitude of recent price changes to evaluate overbought or oversold conditions."
        }
        
        return yaml.dump(config, sort_keys=False)
    
    def get_implementation_yaml(self) -> str:
        """
        Devuelve la implementación del indicador en formato YAML.
        
        Returns:
            Cadena con la implementación YAML
        """
        implementation = {
            "name": "RSI",
            "type": "oscillator",
            "function": "calculate_rsi",
            "code": """
def calculate_rsi(prices, period=14, overbought=70, oversold=30):
    # Calcular cambios en los precios
    delta = prices.diff()
    
    # Separar ganancias (positivos) y pérdidas (negativos)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # Calcular la media móvil exponencial de ganancias y pérdidas
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # Calcular la fuerza relativa (RS)
    rs = avg_gain / avg_loss
    
    # Calcular el RSI
    rsi = 100 - (100 / (1 + rs))
    
    # Generar señales
    signals = pd.Series(0, index=rsi.index)
    signals[rsi < oversold] = 1  # Señal de compra
    signals[rsi > overbought] = -1  # Señal de venta
    
    return {
        'rsi': rsi,
        'signals': signals
    }
"""
        }
        
        return yaml.dump(implementation, sort_keys=False)
    
    @staticmethod
    def from_config(config_dict: Dict[str, Any]) -> 'RSIIndicator':
        """
        Crea una instancia de RSIIndicator a partir de un diccionario de configuración.
        
        Args:
            config_dict: Diccionario con la configuración del indicador
            
        Returns:
            Instancia de RSIIndicator
        """
        parameters = config_dict.get('parameters', {})
        period = parameters.get('period', 14)
        overbought_threshold = parameters.get('overbought_threshold', 70.0)
        oversold_threshold = parameters.get('oversold_threshold', 30.0)
        
        return RSIIndicator(period=period, overbought_threshold=overbought_threshold, oversold_threshold=oversold_threshold)
