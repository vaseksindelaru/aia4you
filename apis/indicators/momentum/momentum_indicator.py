"""
Momentum (MOM) Indicator Implementation

Este indicador mide la tasa de cambio del precio en un período específico,
identificando la fuerza de una tendencia.
"""
import numpy as np
import pandas as pd

class MomentumIndicator:
    """
    Implementación del indicador Momentum (MOM).
    
    Fórmula: MOM = close[t] - close[t - period]
    
    Parámetros:
    - period: Período para el cálculo del momentum (por defecto: 14)
    
    Señales:
    - Compra: MOM > 0 (tendencia alcista)
    - Venta: MOM < 0 (tendencia bajista)
    """
    
    def __init__(self, period=14):
        """
        Inicializa el indicador Momentum con el período especificado.
        
        Args:
            period (int): Número de períodos para calcular el momentum.
        """
        self.period = period
        self.name = "Momentum (MOM)"
        self.description = "Indicador que mide la tasa de cambio del precio en un período específico."
    
    def calculate(self, price_data):
        """
        Calcula el indicador Momentum para una serie de precios.
        
        Args:
            price_data (pd.Series or np.array): Serie temporal de precios de cierre.
            
        Returns:
            pd.Series: Valores del indicador Momentum.
        """
        if isinstance(price_data, np.ndarray):
            price_data = pd.Series(price_data)
        
        # Calcular el Momentum
        momentum = price_data - price_data.shift(self.period)
        
        return momentum
    
    def generate_signals(self, price_data):
        """
        Genera señales de compra/venta basadas en el indicador Momentum.
        
        Args:
            price_data (pd.Series or np.array): Serie temporal de precios de cierre.
            
        Returns:
            pd.DataFrame: DataFrame con columnas para el momentum y las señales.
                - momentum: Valores del indicador
                - signal: 1 para compra, -1 para venta, 0 para mantener
        """
        momentum = self.calculate(price_data)
        
        # Inicializar señales
        signals = pd.DataFrame(index=momentum.index)
        signals['momentum'] = momentum
        signals['signal'] = 0
        
        # Generar señales
        signals.loc[momentum > 0, 'signal'] = 1  # Señal de compra
        signals.loc[momentum < 0, 'signal'] = -1  # Señal de venta
        
        return signals
    
    def get_config(self):
        """
        Retorna la configuración del indicador en formato YAML.
        
        Returns:
            dict: Configuración del indicador.
        """
        config = {
            "name": "momentumIndicator",
            "indicator": "momentum",
            "inputs": [
                {"price_data": "Serie temporal de precios (cierre)"}
            ],
            "conditions": {
                "period": self.period,
                "signal": "MOM > 0 (alcista), MOM < 0 (bajista)"
            }
        }
        
        return config
    
    def get_implementation(self):
        """
        Retorna los detalles de implementación del indicador en formato YAML.
        
        Returns:
            dict: Detalles de implementación.
        """
        implementation = {
            "formula": "MOM = close[t] - close[t - period]",
            "parameters": {
                "period": self.period
            },
            "signals": {
                "buy": "MOM > 0",
                "sell": "MOM < 0"
            },
            "dependencies": [
                "numpy: para cálculos matemáticos",
                "pandas: para manejo de series temporales"
            ]
        }
        
        return implementation

# Ejemplo de uso
if __name__ == "__main__":
    # Crear datos de ejemplo
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    prices = np.random.normal(loc=100, scale=10, size=100)
    prices = np.cumsum(np.random.normal(loc=0, scale=1, size=100)) + 100  # Simular precios
    price_series = pd.Series(prices, index=dates)
    
    # Crear y utilizar el indicador
    mom = MomentumIndicator(period=14)
    signals = mom.generate_signals(price_series)
    
    # Imprimir resultados
    print(f"Indicador: {mom.name}")
    print(f"Descripción: {mom.description}")
    print("\nPrimeras 5 señales:")
    print(signals.head())
    print("\nÚltimas 5 señales:")
    print(signals.tail())
    
    # Imprimir configuración
    print("\nConfiguración:")
    print(mom.get_config())
    
    # Imprimir implementación
    print("\nImplementación:")
    print(mom.get_implementation())