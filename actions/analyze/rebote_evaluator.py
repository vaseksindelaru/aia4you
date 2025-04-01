# rebote_evaluator.py
# Evalúa rebotes para abrir operaciones

import os
import logging
import pandas as pd
import numpy as np
import sys

# Agregar directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Importar módulos necesarios
from core.data_fetcher import DataFetcher
from apis.freaks.detect_rebound import DetectRebound

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("rebote_evaluator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ReboteEvaluator:
    """
    Clase para evaluar rebotes y determinar oportunidades de trading.
    Analiza patrones de precio y volumen para identificar rebotes potenciales.
    """
    
    def __init__(self, data_fetcher=None, config=None):
        """
        Inicializa el evaluador de rebotes.
        
        Args:
            data_fetcher: Instancia de DataFetcher para obtener datos (opcional)
            config (dict): Configuración para el evaluador (opcional)
        """
        self.data_fetcher = data_fetcher or DataFetcher()
        self.config = config or {}
        self.rebound_detector = DetectRebound()
        logger.info("ReboteEvaluator inicializado")
    
    def evaluate_market_for_rebounds(self, symbol, timeframe, lookback_periods=100):
        """
        Evalúa el mercado en busca de rebotes potenciales.
        
        Args:
            symbol (str): Símbolo del mercado (ej: 'BTCUSDT')
            timeframe (str): Marco temporal (ej: '1h', '4h', '1d')
            lookback_periods (int): Número de períodos a analizar
            
        Returns:
            dict: Resultado de la evaluación con rebotes detectados
        """
        logger.info(f"Evaluando rebotes para {symbol} en timeframe {timeframe}")
        
        try:
            # Obtener datos históricos
            data = self.data_fetcher.get_historical_data(symbol, timeframe, lookback_periods)
            
            if data is None or len(data) < lookback_periods:
                logger.warning(f"Datos insuficientes para {symbol} en {timeframe}")
                return {"status": "error", "message": "Datos insuficientes"}
            
            # Detectar rebotes
            rebounds = self.detect_rebounds(data)
            
            # Evaluar la fuerza de los rebotes
            evaluation = self.evaluate_rebound_strength(data, rebounds)
            
            # Generar señales de trading
            signals = self.generate_trading_signals(data, evaluation)
            
            logger.info(f"Evaluación completada. Encontrados {len(signals)} señales")
            
            return {
                "status": "success",
                "symbol": symbol,
                "timeframe": timeframe,
                "rebounds_detected": len(rebounds),
                "signals": signals
            }
            
        except Exception as e:
            logger.error(f"Error al evaluar rebotes: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def detect_rebounds(self, data):
        """
        Detecta rebotes en los datos proporcionados.
        
        Args:
            data (pd.DataFrame): Datos históricos
            
        Returns:
            list: Lista de rebotes detectados
        """
        # Utilizar el detector de rebotes
        rebounds = self.rebound_detector.detect(data)
        
        # Filtrar rebotes según criterios adicionales
        filtered_rebounds = []
        
        for rebound in rebounds:
            # Aplicar filtros adicionales
            if self._apply_rebound_filters(data, rebound):
                filtered_rebounds.append(rebound)
        
        return filtered_rebounds
    
    def _apply_rebound_filters(self, data, rebound):
        """
        Aplica filtros adicionales a un rebote detectado.
        
        Args:
            data (pd.DataFrame): Datos históricos
            rebound (dict): Información del rebote
            
        Returns:
            bool: True si el rebote pasa los filtros, False en caso contrario
        """
        # Ejemplo de filtros adicionales
        
        # 1. Verificar volumen significativo
        if 'volume' in data.columns and 'index' in rebound:
            idx = rebound['index']
            if idx > 0 and idx < len(data):
                avg_volume = data['volume'].iloc[max(0, idx-5):idx].mean()
                current_volume = data['volume'].iloc[idx]
                
                if current_volume < avg_volume * 1.2:
                    return False  # Volumen insuficiente
        
        # 2. Verificar rango de precio significativo
        if 'high' in data.columns and 'low' in data.columns and 'index' in rebound:
            idx = rebound['index']
            if idx > 0 and idx < len(data):
                price_range = data['high'].iloc[idx] - data['low'].iloc[idx]
                avg_range = (data['high'] - data['low']).iloc[max(0, idx-5):idx].mean()
                
                if price_range < avg_range * 0.8:
                    return False  # Rango de precio insuficiente
        
        return True  # Pasa todos los filtros
    
    def evaluate_rebound_strength(self, data, rebounds):
        """
        Evalúa la fuerza de los rebotes detectados.
        
        Args:
            data (pd.DataFrame): Datos históricos
            rebounds (list): Lista de rebotes detectados
            
        Returns:
            list: Lista de evaluaciones de rebotes
        """
        evaluations = []
        
        for rebound in rebounds:
            if 'index' not in rebound:
                continue
                
            idx = rebound['index']
            
            # Calcular métricas de fuerza
            strength_metrics = {}
            
            # 1. Cambio porcentual después del rebote
            if idx < len(data) - 1:
                price_before = data['close'].iloc[idx]
                price_after = data['close'].iloc[min(len(data)-1, idx+3)]
                percent_change = (price_after - price_before) / price_before * 100
                strength_metrics['percent_change'] = percent_change
            
            # 2. Relación con soportes/resistencias
            support_distance = self._calculate_support_distance(data, idx)
            strength_metrics['support_distance'] = support_distance
            
            # 3. Patrones de velas
            candle_pattern = self._identify_candle_pattern(data, idx)
            strength_metrics['candle_pattern'] = candle_pattern
            
            # Calcular puntuación general
            overall_score = self._calculate_overall_score(strength_metrics)
            
            evaluations.append({
                'rebound': rebound,
                'metrics': strength_metrics,
                'score': overall_score
            })
        
        # Ordenar por puntuación
        evaluations.sort(key=lambda x: x['score'], reverse=True)
        
        return evaluations
    
    def _calculate_support_distance(self, data, index):
        """
        Calcula la distancia a los niveles de soporte cercanos.
        
        Args:
            data (pd.DataFrame): Datos históricos
            index (int): Índice del rebote
            
        Returns:
            float: Distancia normalizada al soporte más cercano
        """
        # Implementación simplificada
        # En una implementación real, se utilizaría un algoritmo más sofisticado
        
        if index < 20 or 'low' not in data.columns:
            return 0.5  # Valor por defecto
        
        # Buscar mínimos locales en las últimas 20 barras
        lows = data['low'].iloc[index-20:index]
        min_lows = []
        
        for i in range(1, len(lows)-1):
            if lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i+1]:
                min_lows.append(lows.iloc[i])
        
        if not min_lows:
            return 0.5  # No se encontraron mínimos locales
        
        # Calcular distancia al soporte más cercano
        current_low = data['low'].iloc[index]
        distances = [abs(current_low - support) / current_low for support in min_lows]
        min_distance = min(distances) if distances else 0.5
        
        # Normalizar: 0 = muy cerca, 1 = muy lejos
        normalized_distance = 1 - min(min_distance * 10, 1)
        
        return normalized_distance
    
    def _identify_candle_pattern(self, data, index):
        """
        Identifica patrones de velas en el índice dado.
        
        Args:
            data (pd.DataFrame): Datos históricos
            index (int): Índice a analizar
            
        Returns:
            dict: Información sobre el patrón de velas
        """
        # Implementación simplificada
        # En una implementación real, se utilizaría un detector de patrones más completo
        
        if index >= len(data) or index < 1:
            return {'pattern': 'unknown', 'strength': 0}
        
        # Extraer datos de la vela actual
        current = data.iloc[index]
        
        # Verificar si es una vela de martillo (hammer)
        if 'open' in current and 'close' in current and 'high' in current and 'low' in current:
            body_size = abs(current['close'] - current['open'])
            total_range = current['high'] - current['low']
            
            if total_range > 0:
                lower_shadow = min(current['open'], current['close']) - current['low']
                upper_shadow = current['high'] - max(current['open'], current['close'])
                
                # Criterios para un martillo
                if (lower_shadow > 2 * body_size and 
                    upper_shadow < 0.2 * total_range and 
                    body_size < 0.3 * total_range):
                    return {'pattern': 'hammer', 'strength': 0.8}
                
                # Criterios para una vela de absorción alcista
                if index > 0:
                    previous = data.iloc[index-1]
                    if ('open' in previous and 'close' in previous and
                        previous['close'] < previous['open'] and  # Vela anterior bajista
                        current['close'] > current['open'] and    # Vela actual alcista
                        current['close'] > previous['open'] and   # Cierre por encima de la apertura anterior
                        current['open'] < previous['close']):     # Apertura por debajo del cierre anterior
                        return {'pattern': 'bullish_engulfing', 'strength': 0.9}
        
        # Patrón no identificado
        return {'pattern': 'unknown', 'strength': 0.2}
    
    def _calculate_overall_score(self, metrics):
        """
        Calcula una puntuación general basada en las métricas de fuerza.
        
        Args:
            metrics (dict): Métricas de fuerza
            
        Returns:
            float: Puntuación general (0-1)
        """
        score = 0.5  # Valor por defecto
        
        # Ponderar cambio porcentual (si existe)
        if 'percent_change' in metrics:
            percent_change = metrics['percent_change']
            percent_score = min(max((percent_change + 5) / 10, 0), 1)  # Normalizar entre 0 y 1
            score += percent_score * 0.4  # 40% de peso
        
        # Ponderar distancia al soporte
        if 'support_distance' in metrics:
            score += metrics['support_distance'] * 0.3  # 30% de peso
        
        # Ponderar patrón de velas
        if 'candle_pattern' in metrics and 'strength' in metrics['candle_pattern']:
            score += metrics['candle_pattern']['strength'] * 0.3  # 30% de peso
        
        # Normalizar puntuación final
        return min(max(score, 0), 1)
    
    def generate_trading_signals(self, data, evaluations, threshold=0.7):
        """
        Genera señales de trading basadas en las evaluaciones de rebotes.
        
        Args:
            data (pd.DataFrame): Datos históricos
            evaluations (list): Lista de evaluaciones de rebotes
            threshold (float): Umbral de puntuación para generar señales
            
        Returns:
            list: Lista de señales de trading
        """
        signals = []
        
        for eval_item in evaluations:
            # Filtrar por puntuación
            if eval_item['score'] < threshold:
                continue
            
            rebound = eval_item['rebound']
            
            if 'index' not in rebound:
                continue
                
            idx = rebound['index']
            
            # Extraer información relevante
            if idx < len(data):
                price = data['close'].iloc[idx]
                timestamp = data.index[idx] if hasattr(data, 'index') else None
                
                # Calcular stop loss y take profit
                stop_loss = self._calculate_stop_loss(data, idx, rebound)
                take_profit = self._calculate_take_profit(data, idx, price, stop_loss)
                
                # Crear señal
                signal = {
                    'type': 'BUY',  # Para rebotes, generalmente son señales de compra
                    'price': price,
                    'timestamp': timestamp,
                    'score': eval_item['score'],
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'metrics': eval_item['metrics'],
                    'rebound_type': rebound.get('type', 'unknown')
                }
                
                signals.append(signal)
        
        return signals
    
    def _calculate_stop_loss(self, data, index, rebound):
        """
        Calcula el nivel de stop loss para una señal de rebote.
        
        Args:
            data (pd.DataFrame): Datos históricos
            index (int): Índice del rebote
            rebound (dict): Información del rebote
            
        Returns:
            float: Nivel de stop loss
        """
        # Estrategia simple: colocar stop loss por debajo del mínimo reciente
        if 'low' in data.columns:
            # Buscar el mínimo en las últimas 3 barras incluyendo la actual
            start_idx = max(0, index - 2)
            min_low = data['low'].iloc[start_idx:index+1].min()
            
            # Añadir un pequeño margen
            stop_loss = min_low * 0.995  # 0.5% por debajo del mínimo
            
            return stop_loss
        
        # Si no hay datos de mínimos, usar un porcentaje fijo
        if 'close' in data.columns and index < len(data):
            return data['close'].iloc[index] * 0.97  # 3% por debajo del precio actual
        
        return None
    
    def _calculate_take_profit(self, data, index, entry_price, stop_loss):
        """
        Calcula el nivel de take profit para una señal de rebote.
        
        Args:
            data (pd.DataFrame): Datos históricos
            index (int): Índice del rebote
            entry_price (float): Precio de entrada
            stop_loss (float): Nivel de stop loss
            
        Returns:
            float: Nivel de take profit
        """
        if entry_price is None or stop_loss is None:
            return None
        
        # Calcular risk-to-reward ratio (2:1 por defecto)
        risk = entry_price - stop_loss
        reward = risk * 2  # Reward:Risk = 2:1
        
        take_profit = entry_price + reward
        
        return take_profit
    
    def backtest_rebound_strategy(self, symbol, timeframe, start_date, end_date=None, threshold=0.7):
        """
        Realiza un backtest de la estrategia de rebotes.
        
        Args:
            symbol (str): Símbolo del mercado
            timeframe (str): Marco temporal
            start_date (str): Fecha de inicio (formato: 'YYYY-MM-DD')
            end_date (str): Fecha de fin (opcional, formato: 'YYYY-MM-DD')
            threshold (float): Umbral de puntuación para generar señales
            
        Returns:
            dict: Resultados del backtest
        """
        logger.info(f"Iniciando backtest para {symbol} desde {start_date}")
        
        try:
            # Obtener datos históricos
            data = self.data_fetcher.get_historical_data(
                symbol, timeframe, start_date=start_date, end_date=end_date
            )
            
            if data is None or len(data) < 30:
                logger.warning(f"Datos insuficientes para backtest")
                return {"status": "error", "message": "Datos insuficientes"}
            
            # Resultados del backtest
            results = {
                "symbol": symbol,
                "timeframe": timeframe,
                "start_date": start_date,
                "end_date": end_date,
                "trades": [],
                "summary": {}
            }
            
            # Iterar por los datos para simular trading en tiempo real
            for i in range(30, len(data) - 10):  # Dejar margen para evaluar resultados
                # Usar solo datos hasta el índice actual
                current_data = data.iloc[:i+1]
                
                # Detectar rebotes en los datos actuales
                rebounds = self.detect_rebounds(current_data)
                
                # Verificar si hay un rebote en la barra actual
                current_rebounds = [r for r in rebounds if r.get('index') == i]
                
                if current_rebounds:
                    # Evaluar rebotes
                    evaluations = self.evaluate_rebound_strength(current_data, current_rebounds)
                    
                    # Generar señales
                    signals = self.generate_trading_signals(current_data, evaluations, threshold)
                    
                    # Procesar señales
                    for signal in signals:
                        # Simular trade
                        trade_result = self._simulate_trade(data, i, signal)
                        
                        if trade_result:
                            results["trades"].append(trade_result)
            
            # Calcular estadísticas
            results["summary"] = self._calculate_backtest_statistics(results["trades"])
            
            logger.info(f"Backtest completado. {len(results['trades'])} operaciones realizadas")
            
            return results
            
        except Exception as e:
            logger.error(f"Error en backtest: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _simulate_trade(self, data, index, signal):
        """
        Simula un trade basado en una señal.
        
        Args:
            data (pd.DataFrame): Datos históricos completos
            index (int): Índice actual
            signal (dict): Señal de trading
            
        Returns:
            dict: Resultado del trade
        """
        if index >= len(data) - 1:
            return None
        
        entry_price = signal['price']
        stop_loss = signal['stop_loss']
        take_profit = signal['take_profit']
        
        if entry_price is None or stop_loss is None or take_profit is None:
            return None
        
        # Inicializar resultado
        trade = {
            'entry_index': index,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'exit_index': None,
            'exit_price': None,
            'result': None,
            'profit_loss': None,
            'profit_loss_percent': None,
            'duration': None
        }
        
        # Simular el trade en las barras siguientes
        for i in range(index + 1, min(len(data), index + 30)):  # Máximo 30 barras
            current_bar = data.iloc[i]
            
            # Verificar stop loss
            if 'low' in current_bar and current_bar['low'] <= stop_loss:
                trade['exit_index'] = i
                trade['exit_price'] = stop_loss
                trade['result'] = 'LOSS'
                break
            
            # Verificar take profit
            if 'high' in current_bar and current_bar['high'] >= take_profit:
                trade['exit_index'] = i
                trade['exit_price'] = take_profit
                trade['result'] = 'WIN'
                break
            
            # Si llegamos al final del período y no se activó ni SL ni TP
            if i == min(len(data), index + 30) - 1:
                trade['exit_index'] = i
                trade['exit_price'] = data['close'].iloc[i]
                
                if trade['exit_price'] > entry_price:
                    trade['result'] = 'WIN'
                else:
                    trade['result'] = 'LOSS'
        
        # Calcular P&L
        if trade['exit_price'] is not None:
            trade['profit_loss'] = trade['exit_price'] - entry_price
            trade['profit_loss_percent'] = (trade['exit_price'] / entry_price - 1) * 100
            trade['duration'] = trade['exit_index'] - index
        
        return trade
    
    def _calculate_backtest_statistics(self, trades):
        """
        Calcula estadísticas de backtest.
        
        Args:
            trades (list): Lista de trades
            
        Returns:
            dict: Estadísticas de backtest
        """
        if not trades:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "profit_factor": 0,
                "average_profit": 0,
                "average_loss": 0,
                "max_drawdown": 0
            }
        
        # Estadísticas básicas
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['result'] == 'WIN']
        losing_trades = [t for t in trades if t['result'] == 'LOSS']
        
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        
        win_rate = win_count / total_trades if total_trades > 0 else 0
        
        # Cálculos de rentabilidad
        total_profit = sum(t['profit_loss'] for t in winning_trades) if winning_trades else 0
        total_loss = abs(sum(t['profit_loss'] for t in losing_trades)) if losing_trades else 0
        
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        average_profit = total_profit / win_count if win_count > 0 else 0
        average_loss = total_loss / loss_count if loss_count > 0 else 0
        
        # Calcular drawdown
        equity_curve = []
        balance = 1000  # Balance inicial
        
        for trade in trades:
            if trade['profit_loss'] is not None:
                balance += trade['profit_loss']
            equity_curve.append(balance)
        
        # Calcular drawdown máximo
        max_balance = equity_curve[0]
        current_drawdown = 0
        max_drawdown = 0
        
        for balance in equity_curve:
            if balance > max_balance:
                max_balance = balance
                current_drawdown = 0
            else:
                current_drawdown = (max_balance - balance) / max_balance * 100
                max_drawdown = max(max_drawdown, current_drawdown)
        
        return {
            "total_trades": total_trades,
            "win_count": win_count,
            "loss_count": loss_count,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "average_profit": average_profit,
            "average_loss": average_loss,
            "max_drawdown": max_drawdown,
            "net_profit": total_profit - total_loss,
            "net_profit_percent": (total_profit - total_loss) / 1000 * 100  # Basado en balance inicial
        }

# Función principal para ejecutar desde línea de comandos
def main():
    """Punto de entrada principal para ejecución desde línea de comandos"""
    evaluator = ReboteEvaluator()
    
    # Ejemplo de uso
    symbol = "BTCUSDT"
    timeframe = "1h"
    
    # Evaluar rebotes actuales
    print(f"Evaluando rebotes para {symbol} en {timeframe}...")
    results = evaluator.evaluate_market_for_rebounds(symbol, timeframe)
    
    if results["status"] == "success":
        print(f"Encontrados {results['rebounds_detected']} rebotes")
        
        if "signals" in results and results["signals"]:
            print("\nSeñales generadas:")
            for i, signal in enumerate(results["signals"]):
                print(f"Señal {i+1}:")
                print(f"  Tipo: {signal['type']}")
                print(f"  Precio: {signal['price']}")
                print(f"  Puntuación: {signal['score']:.2f}")
                print(f"  Stop Loss: {signal['stop_loss']}")
                print(f"  Take Profit: {signal['take_profit']}")
                print()
    else:
        print(f"Error: {results.get('message', 'Desconocido')}")
    
    # Ejecutar backtest
    print("\nEjecutando backtest...")
    backtest = evaluator.backtest_rebound_strategy(
        symbol, timeframe, start_date="2025-01-01", end_date="2025-03-01"
    )
    
    if "summary" in backtest:
        summary = backtest["summary"]
        print("\nResultados del backtest:")
        print(f"Total de operaciones: {summary.get('total_trades', 0)}")
        print(f"Tasa de acierto: {summary.get('win_rate', 0)*100:.2f}%")
        print(f"Factor de beneficio: {summary.get('profit_factor', 0):.2f}")
        print(f"Beneficio neto: {summary.get('net_profit', 0):.2f} ({summary.get('net_profit_percent', 0):.2f}%)")
        print(f"Drawdown máximo: {summary.get('max_drawdown', 0):.2f}%")

if __name__ == "__main__":
    main()
