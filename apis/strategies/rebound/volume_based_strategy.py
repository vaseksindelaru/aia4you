# volume_based_strategy.py
# Estrategia de rebote basada en volumen

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
        logging.FileHandler("volume_strategy.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VolumeBased:
    """
    Estrategia de trading basada en rebotes con confirmación de volumen.
    Detecta rebotes en niveles de soporte/resistencia y confirma con patrones de volumen.
    """
    
    def __init__(self, config=None):
        """
        Inicializa la estrategia basada en volumen.
        
        Args:
            config (dict): Configuración para la estrategia (opcional)
        """
        self.config = config or {}
        self.data_fetcher = DataFetcher()
        self.rebound_detector = DetectRebound()
        
        # Parámetros por defecto
        self.params = {
            'volume_threshold': 1.5,  # Multiplicador de volumen promedio
            'lookback_periods': 20,   # Períodos para calcular promedios
            'confirmation_periods': 3, # Períodos para confirmar rebote
            'rsi_oversold': 30,       # Nivel de sobreventa RSI
            'rsi_overbought': 70      # Nivel de sobrecompra RSI
        }
        
        # Actualizar con configuración proporcionada
        if 'parameters' in self.config:
            self.params.update(self.config['parameters'])
        
        logger.info("Estrategia VolumeBased inicializada")
    
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
        
        logger.info("Analizando datos para señales de volumen (%d barras)", len(data))
        
        try:
            # Preparar datos
            self._prepare_data(data)
            
            # Detectar rebotes
            rebounds = self.rebound_detector.detect(data)
            
            # Filtrar rebotes por volumen
            volume_confirmed = self._filter_by_volume(data, rebounds)
            
            # Generar señales
            signals = self._generate_signals(data, volume_confirmed)
            
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
        # Calcular promedio de volumen
        data['volume_sma'] = data['volume'].rolling(window=self.params['lookback_periods']).mean()
        
        # Calcular ratio de volumen
        data['volume_ratio'] = data['volume'] / data['volume_sma']
        
        # Calcular RSI si no existe
        if 'rsi' not in data.columns:
            self._calculate_rsi(data)
    
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
    
    def _filter_by_volume(self, data, rebounds):
        """
        Filtra rebotes basados en confirmación de volumen.
        
        Args:
            data (pd.DataFrame): Datos históricos
            rebounds (list): Lista de rebotes detectados
            
        Returns:
            list: Rebotes confirmados por volumen
        """
        confirmed_rebounds = []
        
        for rebound in rebounds:
            if 'index' not in rebound:
                continue
            
            idx = rebound['index']
            
            # Verificar si hay suficientes datos
            if idx >= len(data) or idx < 0:
                continue
            
            # Verificar volumen significativo
            if data['volume_ratio'].iloc[idx] >= self.params['volume_threshold']:
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
            
            # Verificar RSI
            if 'rsi' in data.columns and data['rsi'].iloc[index] < self.params['rsi_oversold']:
                return True
            
            return True
        
        # Para rebotes en resistencia (bajistas)
        elif rebound_type == 'resistance':
            # Verificar que el precio baje en los períodos siguientes
            for i in range(1, self.params['confirmation_periods'] + 1):
                if index + i < len(data):
                    if data['close'].iloc[index + i] > data['close'].iloc[index]:
                        return False
            
            # Verificar RSI
            if 'rsi' in data.columns and data['rsi'].iloc[index] > self.params['rsi_overbought']:
                return True
            
            return True
        
        return False
    
    def _generate_signals(self, data, rebounds):
        """
        Genera señales de trading basadas en rebotes confirmados.
        
        Args:
            data (pd.DataFrame): Datos históricos
            rebounds (list): Rebotes confirmados
            
        Returns:
            list: Señales de trading
        """
        signals = []
        
        for rebound in rebounds:
            if 'index' not in rebound or 'type' not in rebound:
                continue
            
            idx = rebound['index']
            
            # Verificar si hay suficientes datos
            if idx >= len(data) or idx < 0:
                continue
            
            # Crear señal
            signal = {
                'timestamp': data.index[idx] if hasattr(data, 'index') else None,
                'price': data['close'].iloc[idx],
                'type': 'BUY' if rebound['type'] == 'support' else 'SELL',
                'volume_ratio': data['volume_ratio'].iloc[idx],
                'rsi': data['rsi'].iloc[idx] if 'rsi' in data.columns else None,
                'confidence': self._calculate_confidence(data, idx, rebound)
            }
            
            # Calcular niveles de stop loss y take profit
            signal['stop_loss'] = self._calculate_stop_loss(data, idx, rebound)
            signal['take_profit'] = self._calculate_take_profit(data, idx, signal['price'], signal['stop_loss'])
            
            signals.append(signal)
        
        return signals
    
    def _calculate_confidence(self, data, index, rebound):
        """
        Calcula el nivel de confianza de una señal.
        
        Args:
            data (pd.DataFrame): Datos históricos
            index (int): Índice del rebote
            rebound (dict): Información del rebote
            
        Returns:
            float: Nivel de confianza (0-1)
        """
        confidence = 0.5  # Base
        
        # Factores que aumentan la confianza
        
        # 1. Volumen alto
        volume_factor = min(data['volume_ratio'].iloc[index] / self.params['volume_threshold'], 2) / 2
        confidence += volume_factor * 0.2  # Max 20%
        
        # 2. RSI en zona extrema
        if 'rsi' in data.columns:
            rsi = data['rsi'].iloc[index]
            if rebound['type'] == 'support' and rsi < self.params['rsi_oversold']:
                rsi_factor = (self.params['rsi_oversold'] - rsi) / self.params['rsi_oversold']
                confidence += rsi_factor * 0.15  # Max 15%
            elif rebound['type'] == 'resistance' and rsi > self.params['rsi_overbought']:
                rsi_factor = (rsi - self.params['rsi_overbought']) / (100 - self.params['rsi_overbought'])
                confidence += rsi_factor * 0.15  # Max 15%
        
        # 3. Tendencia previa fuerte
        trend_strength = self._calculate_trend_strength(data, index, rebound['type'])
        confidence += trend_strength * 0.15  # Max 15%
        
        return min(confidence, 1.0)
    
    def _calculate_trend_strength(self, data, index, rebound_type):
        """
        Calcula la fuerza de la tendencia previa.
        
        Args:
            data (pd.DataFrame): Datos históricos
            index (int): Índice del rebote
            rebound_type (str): Tipo de rebote
            
        Returns:
            float: Fuerza de la tendencia (0-1)
        """
        if index < self.params['lookback_periods']:
            return 0.5
        
        # Calcular cambio porcentual en el período previo
        start_idx = max(0, index - self.params['lookback_periods'])
        start_price = data['close'].iloc[start_idx]
        end_price = data['close'].iloc[index]
        
        percent_change = abs((end_price - start_price) / start_price)
        
        # Normalizar a 0-1
        strength = min(percent_change / 0.1, 1.0)  # 10% cambio = fuerza máxima
        
        # Verificar dirección
        if rebound_type == 'support' and end_price < start_price:
            return strength  # Tendencia bajista antes de rebote en soporte
        elif rebound_type == 'resistance' and end_price > start_price:
            return strength  # Tendencia alcista antes de rebote en resistencia
        
        return 0.3  # Tendencia en dirección contraria
    
    def _calculate_stop_loss(self, data, index, rebound):
        """
        Calcula el nivel de stop loss para una señal.
        
        Args:
            data (pd.DataFrame): Datos históricos
            index (int): Índice del rebote
            rebound (dict): Información del rebote
            
        Returns:
            float: Nivel de stop loss
        """
        if rebound['type'] == 'support':
            # Para señales de compra, stop loss debajo del mínimo
            return data['low'].iloc[index] * 0.995  # 0.5% debajo
        else:
            # Para señales de venta, stop loss encima del máximo
            return data['high'].iloc[index] * 1.005  # 0.5% encima
    
    def _calculate_take_profit(self, data, index, entry_price, stop_loss):
        """
        Calcula el nivel de take profit para una señal.
        
        Args:
            data (pd.DataFrame): Datos históricos
            index (int): Índice del rebote
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
    strategy = VolumeBased()
    
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
