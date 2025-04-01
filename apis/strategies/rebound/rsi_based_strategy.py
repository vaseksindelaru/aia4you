# rsi_based_strategy.py
# Estrategia de rebote basada en RSI

import pandas as pd
import numpy as np
import logging
import os
import sys

# Agregar directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# Importar módulos necesarios
from core.data_fetcher import DataFetcher
from apis.freaks.detect_rebound import DetectRebound

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("rsi_strategy.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RsiBased:
    """
    Estrategia de trading basada en rebotes con confirmación de RSI.
    Detecta rebotes en niveles de soporte/resistencia y confirma con divergencias RSI.
    """
    
    def __init__(self, config=None):
        """
        Inicializa la estrategia basada en RSI.
        
        Args:
            config (dict): Configuración para la estrategia (opcional)
        """
        self.config = config or {}
        self.data_fetcher = DataFetcher()
        self.rebound_detector = DetectRebound()
        
        # Parámetros por defecto
        self.params = {
            'rsi_period': 14,         # Período para RSI
            'rsi_oversold': 30,       # Nivel de sobreventa RSI
            'rsi_overbought': 70,     # Nivel de sobrecompra RSI
            'lookback_periods': 20,   # Períodos para calcular promedios
            'divergence_lookback': 5, # Períodos para buscar divergencias
            'confirmation_periods': 2  # Períodos para confirmar rebote
        }
        
        # Actualizar con configuración proporcionada
        if 'parameters' in self.config:
            self.params.update(self.config['parameters'])
        
        logger.info("Estrategia RsiBased inicializada")
    
    def analyze(self, data):
        """
        Analiza los datos para detectar señales de trading.
        
        Args:
            data (pd.DataFrame): Datos históricos con OHLCV
            
        Returns:
            list: Lista de señales detectadas
        """
        if data is None or len(data) < self.params['lookback_periods']:
            logger.warning("Datos insuficientes para análisis")
            return []
        
        logger.info("Analizando datos para señales de RSI (%d barras)", len(data))
        
        try:
            # Preparar datos
            self._prepare_data(data)
            
            # Detectar rebotes
            rebounds = self.rebound_detector.detect(data)
            
            # Filtrar rebotes por RSI
            rsi_confirmed = self._filter_by_rsi(data, rebounds)
            
            # Buscar divergencias RSI
            divergences = self._find_rsi_divergences(data)
            
            # Combinar rebotes confirmados y divergencias
            combined_signals = self._combine_signals(data, rsi_confirmed, divergences)
            
            # Generar señales
            signals = self._generate_signals(data, combined_signals)
            
            logger.info("Análisis completado. Encontradas %d señales", len(signals))
            return signals
            
        except Exception as e:
            logger.error("Error en análisis: %s", str(e))
            return []
    
    def _prepare_data(self, data):
        """
        Prepara los datos para el análisis.
        
        Args:
            data (pd.DataFrame): Datos históricos
        """
        # Calcular RSI si no existe
        if 'rsi' not in data.columns:
            self._calculate_rsi(data, self.params['rsi_period'])
        
        # Calcular medias móviles
        data['sma20'] = data['close'].rolling(window=20).mean()
        data['sma50'] = data['close'].rolling(window=50).mean()
        
        # Calcular tendencia
        data['trend'] = np.where(data['sma20'] > data['sma50'], 1, -1)
    
    def _calculate_rsi(self, data, periods=14):
        """
        Calcula el indicador RSI.
        
        Args:
            data (pd.DataFrame): Datos históricos
            periods (int): Períodos para el cálculo
        """
        # Calcular cambios
        delta = data['close'].diff()
        
        # Separar ganancias y pérdidas
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calcular promedios
        avg_gain = gain.rolling(window=periods).mean()
        avg_loss = loss.rolling(window=periods).mean()
        
        # Calcular RS y RSI
        rs = avg_gain / avg_loss
        data['rsi'] = 100 - (100 / (1 + rs))
    
    def _filter_by_rsi(self, data, rebounds):
        """
        Filtra rebotes basados en confirmación de RSI.
        
        Args:
            data (pd.DataFrame): Datos históricos
            rebounds (list): Lista de rebotes detectados
            
        Returns:
            list: Rebotes confirmados por RSI
        """
        confirmed_rebounds = []
        
        for rebound in rebounds:
            if 'index' not in rebound:
                continue
            
            idx = rebound['index']
            
            # Verificar si hay suficientes datos
            if idx >= len(data) or idx < 0:
                continue
            
            # Verificar RSI en zonas extremas
            if rebound['type'] == 'support' and data['rsi'].iloc[idx] < self.params['rsi_oversold']:
                # Verificar confirmación en períodos siguientes
                if self._check_confirmation(data, idx, rebound['type']):
                    confirmed_rebounds.append(rebound)
            
            elif rebound['type'] == 'resistance' and data['rsi'].iloc[idx] > self.params['rsi_overbought']:
                # Verificar confirmación en períodos siguientes
                if self._check_confirmation(data, idx, rebound['type']):
                    confirmed_rebounds.append(rebound)
        
        return confirmed_rebounds
    
    def _check_confirmation(self, data, index, rebound_type):
        """
        Verifica la confirmación del rebote en los períodos siguientes.
        
        Args:
            data (pd.DataFrame): Datos históricos
            index (int): Índice del rebote
            rebound_type (str): Tipo de rebote ('support' o 'resistance')
            
        Returns:
            bool: True si el rebote está confirmado
        """
        # Verificar si hay suficientes datos para confirmar
        if index + self.params['confirmation_periods'] >= len(data):
            return False
        
        # Para rebotes en soporte (alcistas)
        if rebound_type == 'support':
            # Verificar que el precio suba en los períodos siguientes
            for i in range(1, self.params['confirmation_periods'] + 1):
                if index + i < len(data):
                    if data['close'].iloc[index + i] < data['close'].iloc[index]:
                        return False
            
            # Verificar que RSI suba
            if data['rsi'].iloc[index + self.params['confirmation_periods']] > data['rsi'].iloc[index]:
                return True
        
        # Para rebotes en resistencia (bajistas)
        elif rebound_type == 'resistance':
            # Verificar que el precio baje en los períodos siguientes
            for i in range(1, self.params['confirmation_periods'] + 1):
                if index + i < len(data):
                    if data['close'].iloc[index + i] > data['close'].iloc[index]:
                        return False
            
            # Verificar que RSI baje
            if data['rsi'].iloc[index + self.params['confirmation_periods']] < data['rsi'].iloc[index]:
                return True
        
        return False
    
    def _find_rsi_divergences(self, data):
        """
        Busca divergencias entre precio y RSI.
        
        Args:
            data (pd.DataFrame): Datos históricos
            
        Returns:
            list: Divergencias encontradas
        """
        divergences = []
        
        # Necesitamos al menos lookback_periods + divergence_lookback barras
        min_bars = self.params['lookback_periods'] + self.params['divergence_lookback']
        
        if len(data) < min_bars:
            return divergences
        
        # Buscar divergencias alcistas (precio hace mínimos más bajos, RSI hace mínimos más altos)
        for i in range(min_bars, len(data)):
            # Buscar mínimo local en precio
            if (data['low'].iloc[i] < data['low'].iloc[i-1] and 
                data['low'].iloc[i] < data['low'].iloc[i+1] if i+1 < len(data) else True):
                
                # Buscar mínimo anterior en el rango de lookback
                prev_min_idx = None
                for j in range(i - self.params['divergence_lookback'], i):
                    if (j > 0 and 
                        data['low'].iloc[j] < data['low'].iloc[j-1] and 
                        data['low'].iloc[j] < data['low'].iloc[j+1]):
                        prev_min_idx = j
                        break
                
                if prev_min_idx is not None:
                    # Verificar divergencia alcista
                    if (data['low'].iloc[i] < data['low'].iloc[prev_min_idx] and 
                        data['rsi'].iloc[i] > data['rsi'].iloc[prev_min_idx]):
                        
                        divergences.append({
                            'index': i,
                            'type': 'bullish',
                            'price_low': data['low'].iloc[i],
                            'prev_price_low': data['low'].iloc[prev_min_idx],
                            'rsi_low': data['rsi'].iloc[i],
                            'prev_rsi_low': data['rsi'].iloc[prev_min_idx]
                        })
        
        # Buscar divergencias bajistas (precio hace máximos más altos, RSI hace máximos más bajos)
        for i in range(min_bars, len(data)):
            # Buscar máximo local en precio
            if (data['high'].iloc[i] > data['high'].iloc[i-1] and 
                data['high'].iloc[i] > data['high'].iloc[i+1] if i+1 < len(data) else True):
                
                # Buscar máximo anterior en el rango de lookback
                prev_max_idx = None
                for j in range(i - self.params['divergence_lookback'], i):
                    if (j > 0 and 
                        data['high'].iloc[j] > data['high'].iloc[j-1] and 
                        data['high'].iloc[j] > data['high'].iloc[j+1]):
                        prev_max_idx = j
                        break
                
                if prev_max_idx is not None:
                    # Verificar divergencia bajista
                    if (data['high'].iloc[i] > data['high'].iloc[prev_max_idx] and 
                        data['rsi'].iloc[i] < data['rsi'].iloc[prev_max_idx]):
                        
                        divergences.append({
                            'index': i,
                            'type': 'bearish',
                            'price_high': data['high'].iloc[i],
                            'prev_price_high': data['high'].iloc[prev_max_idx],
                            'rsi_high': data['rsi'].iloc[i],
                            'prev_rsi_high': data['rsi'].iloc[prev_max_idx]
                        })
        
        return divergences
    
    def _combine_signals(self, data, rebounds, divergences):
        """
        Combina rebotes confirmados y divergencias para generar señales.
        
        Args:
            data (pd.DataFrame): Datos históricos
            rebounds (list): Rebotes confirmados
            divergences (list): Divergencias encontradas
            
        Returns:
            list: Señales combinadas
        """
        combined = []
        
        # Añadir rebotes
        for rebound in rebounds:
            combined.append({
                'index': rebound['index'],
                'type': 'BUY' if rebound['type'] == 'support' else 'SELL',
                'source': 'rebound',
                'confidence': 0.7  # Confianza base para rebotes
            })
        
        # Añadir divergencias
        for divergence in divergences:
            combined.append({
                'index': divergence['index'],
                'type': 'BUY' if divergence['type'] == 'bullish' else 'SELL',
                'source': 'divergence',
                'confidence': 0.6  # Confianza base para divergencias
            })
        
        # Buscar coincidencias (rebote + divergencia)
        for i, signal1 in enumerate(combined):
            for j, signal2 in enumerate(combined):
                if i != j and abs(signal1['index'] - signal2['index']) <= 2:
                    if signal1['type'] == signal2['type']:
                        # Aumentar confianza si hay coincidencia
                        signal1['confidence'] = min(signal1['confidence'] + 0.2, 1.0)
                        signal2['confidence'] = min(signal2['confidence'] + 0.2, 1.0)
                        signal1['source'] = 'combined'
                        signal2['source'] = 'combined'
        
        # Eliminar duplicados (señales muy cercanas del mismo tipo)
        filtered = []
        for signal in combined:
            # Verificar si ya existe una señal similar
            exists = False
            for existing in filtered:
                if (abs(signal['index'] - existing['index']) <= 2 and 
                    signal['type'] == existing['type']):
                    # Mantener la de mayor confianza
                    if signal['confidence'] > existing['confidence']:
                        existing.update(signal)
                    exists = True
                    break
            
            if not exists:
                filtered.append(signal)
        
        return filtered
    
    def _generate_signals(self, data, combined_signals):
        """
        Genera señales de trading finales.
        
        Args:
            data (pd.DataFrame): Datos históricos
            combined_signals (list): Señales combinadas
            
        Returns:
            list: Señales de trading
        """
        signals = []
        
        for signal in combined_signals:
            idx = signal['index']
            
            # Verificar si hay suficientes datos
            if idx >= len(data) or idx < 0:
                continue
            
            # Crear señal
            trade_signal = {
                'timestamp': data.index[idx] if hasattr(data, 'index') else None,
                'price': data['close'].iloc[idx],
                'type': signal['type'],
                'source': signal['source'],
                'rsi': data['rsi'].iloc[idx],
                'confidence': signal['confidence']
            }
            
            # Calcular niveles de stop loss y take profit
            trade_signal['stop_loss'] = self._calculate_stop_loss(data, idx, signal)
            trade_signal['take_profit'] = self._calculate_take_profit(data, idx, trade_signal['price'], trade_signal['stop_loss'])
            
            signals.append(trade_signal)
        
        return signals
    
    def _calculate_stop_loss(self, data, index, signal):
        """
        Calcula el nivel de stop loss para una señal.
        
        Args:
            data (pd.DataFrame): Datos históricos
            index (int): Índice de la señal
            signal (dict): Información de la señal
            
        Returns:
            float: Nivel de stop loss
        """
        # Buscar mínimo/máximo reciente
        lookback = min(20, index)
        
        if signal['type'] == 'BUY':
            # Para señales de compra, buscar mínimo reciente
            min_price = data['low'].iloc[index-lookback:index+1].min()
            return min_price * 0.99  # 1% debajo del mínimo
        else:
            # Para señales de venta, buscar máximo reciente
            max_price = data['high'].iloc[index-lookback:index+1].max()
            return max_price * 1.01  # 1% encima del máximo
    
    def _calculate_take_profit(self, data, index, entry_price, stop_loss):
        """
        Calcula el nivel de take profit para una señal.
        
        Args:
            data (pd.DataFrame): Datos históricos
            index (int): Índice de la señal
            entry_price (float): Precio de entrada
            stop_loss (float): Nivel de stop loss
            
        Returns:
            float: Nivel de take profit
        """
        # Calcular risk-to-reward ratio (2:1 por defecto)
        risk = abs(entry_price - stop_loss)
        reward = risk * 2  # Reward:Risk = 2:1
        
        if entry_price > stop_loss:
            # Señal de compra
            return entry_price + reward
        else:
            # Señal de venta
            return entry_price - reward
    
    def backtest(self, symbol, timeframe, start_date, end_date=None):
        """
        Realiza un backtest de la estrategia.
        
        Args:
            symbol (str): Símbolo del mercado
            timeframe (str): Marco temporal
            start_date (str): Fecha de inicio (formato: 'YYYY-MM-DD')
            end_date (str): Fecha de fin (opcional, formato: 'YYYY-MM-DD')
            
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
            
            # Analizar datos completos
            signals = self.analyze(data)
            
            # Simular operaciones
            trades = self._simulate_trades(data, signals)
            
            # Calcular estadísticas
            stats = self._calculate_statistics(trades)
            
            logger.info(f"Backtest completado. {len(trades)} operaciones realizadas")
            
            return {
                "status": "success",
                "symbol": symbol,
                "timeframe": timeframe,
                "start_date": start_date,
                "end_date": end_date,
                "trades": trades,
                "statistics": stats
            }
            
        except Exception as e:
            logger.error(f"Error en backtest: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _simulate_trades(self, data, signals):
        """
        Simula operaciones basadas en señales.
        
        Args:
            data (pd.DataFrame): Datos históricos
            signals (list): Señales de trading
            
        Returns:
            list: Operaciones simuladas
        """
        trades = []
        
        for signal in signals:
            # Encontrar índice de la señal
            if hasattr(data, 'index') and signal['timestamp'] is not None:
                idx = data.index.get_loc(signal['timestamp'])
            else:
                # Buscar por precio
                for i in range(len(data)):
                    if abs(data['close'].iloc[i] - signal['price']) < 0.0001:
                        idx = i
                        break
                else:
                    continue  # No se encontró el índice
            
            # Simular la operación
            trade = self._simulate_trade(data, idx, signal)
            
            if trade:
                trades.append(trade)
        
        return trades
    
    def _simulate_trade(self, data, index, signal):
        """
        Simula una operación individual.
        
        Args:
            data (pd.DataFrame): Datos históricos
            index (int): Índice de la señal
            signal (dict): Señal de trading
            
        Returns:
            dict: Resultado de la operación
        """
        if index >= len(data) - 1:
            return None
        
        entry_price = signal['price']
        stop_loss = signal['stop_loss']
        take_profit = signal['take_profit']
        
        # Inicializar resultado
        trade = {
            'entry_index': index,
            'entry_price': entry_price,
            'entry_time': data.index[index] if hasattr(data, 'index') else None,
            'type': signal['type'],
            'source': signal.get('source', 'unknown'),
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'exit_index': None,
            'exit_price': None,
            'exit_time': None,
            'result': None,
            'profit_loss': None,
            'profit_loss_percent': None,
            'duration': None
        }
        
        # Simular la operación en las barras siguientes
        for i in range(index + 1, len(data)):
            current_bar = data.iloc[i]
            
            if signal['type'] == 'BUY':
                # Verificar stop loss
                if current_bar['low'] <= stop_loss:
                    trade['exit_index'] = i
                    trade['exit_price'] = stop_loss
                    trade['result'] = 'LOSS'
                    break
                
                # Verificar take profit
                if current_bar['high'] >= take_profit:
                    trade['exit_index'] = i
                    trade['exit_price'] = take_profit
                    trade['result'] = 'WIN'
                    break
            else:  # SELL
                # Verificar stop loss
                if current_bar['high'] >= stop_loss:
                    trade['exit_index'] = i
                    trade['exit_price'] = stop_loss
                    trade['result'] = 'LOSS'
                    break
                
                # Verificar take profit
                if current_bar['low'] <= take_profit:
                    trade['exit_index'] = i
                    trade['exit_price'] = take_profit
                    trade['result'] = 'WIN'
                    break
            
            # Si llegamos al final de los datos
            if i == len(data) - 1:
                trade['exit_index'] = i
                trade['exit_price'] = current_bar['close']
                
                if signal['type'] == 'BUY':
                    trade['result'] = 'WIN' if trade['exit_price'] > entry_price else 'LOSS'
                else:  # SELL
                    trade['result'] = 'WIN' if trade['exit_price'] < entry_price else 'LOSS'
        
        # Completar información de salida
        if trade['exit_index'] is not None:
            trade['exit_time'] = data.index[trade['exit_index']] if hasattr(data, 'index') else None
            
            if signal['type'] == 'BUY':
                trade['profit_loss'] = trade['exit_price'] - entry_price
                trade['profit_loss_percent'] = (trade['exit_price'] / entry_price - 1) * 100
            else:  # SELL
                trade['profit_loss'] = entry_price - trade['exit_price']
                trade['profit_loss_percent'] = (entry_price / trade['exit_price'] - 1) * 100
            
            trade['duration'] = trade['exit_index'] - index
        
        return trade
    
    def _calculate_statistics(self, trades):
        """
        Calcula estadísticas de trading.
        
        Args:
            trades (list): Operaciones simuladas
            
        Returns:
            dict: Estadísticas
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

# Función para pruebas
def main():
    """Función principal para pruebas"""
    # Crear instancia de la estrategia
    strategy = RsiBased()
    
    # Ejecutar backtest
    results = strategy.backtest(
        symbol="BTCUSDT",
        timeframe="1h",
        start_date="2025-01-01",
        end_date="2025-03-01"
    )
    
    # Mostrar resultados
    if results["status"] == "success":
        print(f"Backtest completado para {results['symbol']} en {results['timeframe']}")
        print(f"Total de operaciones: {results['statistics']['total_trades']}")
        print(f"Tasa de acierto: {results['statistics']['win_rate']*100:.2f}%")
        print(f"Factor de beneficio: {results['statistics']['profit_factor']:.2f}")
        print(f"Beneficio neto: {results['statistics']['net_profit']:.2f} ({results['statistics']['net_profit_percent']:.2f}%)")
        print(f"Drawdown máximo: {results['statistics']['max_drawdown']:.2f}%")
    else:
        print(f"Error: {results.get('message', 'Desconocido')}")

if __name__ == "__main__":
    main()
