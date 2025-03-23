import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from rsi_indicator import RSIIndicator
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

def generate_sample_data(periods=100):
    """Genera datos de muestra para probar el indicador RSI"""
    np.random.seed(42)  # Para reproducibilidad
    
    # Generar precios con tendencia y algo de ruido
    trend = np.linspace(100, 150, periods)
    noise = np.random.normal(0, 5, periods)
    prices = trend + noise
    
    # Crear DataFrame con fechas
    dates = pd.date_range(start='2023-01-01', periods=periods)
    df = pd.DataFrame({'close': prices}, index=dates)
    
    return df

def test_rsi_indicator():
    """Prueba la funcionalidad del indicador RSI"""
    # Generar datos de muestra
    df = generate_sample_data(periods=100)
    
    # Crear instancia del indicador RSI
    rsi = RSIIndicator(period=14, overbought_threshold=70, oversold_threshold=30)
    
    # Calcular valores del RSI
    df['rsi'] = rsi.calculate(df['close'])
    
    # Generar señales
    df['signals'] = rsi.generate_signals(df['rsi'])
    
    # Imprimir estadísticas
    print(f"Datos generados: {len(df)} puntos")
    print(f"Valores RSI calculados: {df['rsi'].count()}")
    print(f"Señales generadas: {df['signals'].value_counts()}")
    
    # Obtener configuración YAML
    config_yaml = rsi.get_config_yaml()
    print("\nConfiguración YAML:")
    print(config_yaml)
    
    # Obtener implementación YAML
    impl_yaml = rsi.get_implementation_yaml()
    print("\nImplementación YAML:")
    print(impl_yaml)
    
    # Visualizar resultados
    plt.figure(figsize=(12, 8))
    
    # Gráfico de precios
    plt.subplot(2, 1, 1)
    plt.plot(df.index, df['close'])
    plt.title('Precios de cierre')
    plt.grid(True)
    
    # Marcar señales en el gráfico de precios
    buy_signals = df[df['signals'] == 1]
    sell_signals = df[df['signals'] == -1]
    
    plt.scatter(buy_signals.index, buy_signals['close'], marker='^', color='green', s=100, label='Compra')
    plt.scatter(sell_signals.index, sell_signals['close'], marker='v', color='red', s=100, label='Venta')
    plt.legend()
    
    # Gráfico de RSI
    plt.subplot(2, 1, 2)
    plt.plot(df.index, df['rsi'])
    plt.axhline(y=70, color='r', linestyle='--', alpha=0.5)
    plt.axhline(y=30, color='g', linestyle='--', alpha=0.5)
    plt.title('RSI (14)')
    plt.ylim(0, 100)
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig('rsi_test_results.png')
    print("\nGráfico guardado como 'rsi_test_results.png'")

if __name__ == "__main__":
    test_rsi_indicator()
