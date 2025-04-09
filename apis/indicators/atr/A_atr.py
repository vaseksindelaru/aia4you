import pandas as pd
import numpy as np
from fastapi import APIRouter, Query

router = APIRouter()

def calculate_atr(data, period):
    """
    Calculate Average True Range (ATR)
    
    Args:
        data (pd.DataFrame): DataFrame with 'high', 'low', 'close' columns
        period (int): Period for ATR calculation
        
    Returns:
        pd.Series: ATR values
    """
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    
    # Create DataFrame with the three components
    ranges = pd.DataFrame({
        'high_low': high_low,
        'high_close': high_close,
        'low_close': low_close
    })
    
    # True Range is the maximum of the three components
    true_range = ranges.max(axis=1)
    
    # ATR is the moving average of True Range
    atr = true_range.rolling(window=period).mean()
    return atr

@router.get("/atr")
async def get_atr(
    period: int = Query(14, description="Period for ATR calculation"),
    symbol: str = Query("BTCUSDC", description="Trading symbol")
):
    """
    API endpoint to calculate ATR for a given symbol and period
    
    Args:
        period (int): Period for ATR calculation
        symbol (str): Trading symbol
        
    Returns:
        dict: ATR values and metadata
    """
    try:
        # Load data from CSV file
        file_path = f"data/{symbol}-5m-2025-04-08/{symbol}-5m-2025-04-08.csv"
        df = pd.read_csv(file_path)
        
        # Rename columns for clarity
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                      'close_time', 'quote_asset_volume', 'number_of_trades', 
                      'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
        
        # Calculate ATR
        atr_values = calculate_atr(df, period)
        
        # Convert to list and remove NaN values
        atr_list = atr_values.dropna().tolist()
        
        return {
            "symbol": symbol,
            "period": period,
            "atr_values": atr_list[-100:],  # Return last 100 values for efficiency
            "atr_current": atr_list[-1] if len(atr_list) > 0 else None
        }
    except Exception as e:
        return {"error": str(e)}
