from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
import os
import uuid
import yaml
import logging
from dotenv import load_dotenv
import json
import requests

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("strategy_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Definición de modelos
class StrategyRequest(BaseModel):
    prompt: str

class SaveStrategyRequest(BaseModel):
    strategy_data: dict

# Cargar variables de entorno
load_dotenv()

# Configuración de FastAPI
app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos
    allow_headers=["*"],  # Permitir todos los headers
)

def generate_strategy_yaml(prompt: str) -> dict:
    """
    Genera una configuración YAML para una estrategia basada en el prompt del usuario.
    Devuelve un diccionario con nombre, descripción y YAML.
    """
    logger.info(f"GENERANDO ESTRATEGIA PARA: {prompt}")
    
    # Convertir el prompt a minúsculas para facilitar la búsqueda de palabras clave
    prompt_lower = prompt.lower()
    
    # Detectar el tipo de estrategia solicitada basado en palabras clave
    if "bollinger" in prompt_lower or "bandas" in prompt_lower:
        # Estrategia de Bollinger Bands
        strategy_name = "Bollinger Bands Strategy"
        strategy_description = "Estrategia que utiliza las Bandas de Bollinger para identificar oportunidades de reversión a la media y volatilidad del mercado."
        strategy_yaml = """indicators:
  - Bollinger Bands (BB)
  - Volume
  - RSI (Relative Strength Index)
parameters:
  - BB_period: 20
  - BB_std_dev: 2
  - RSI_period: 14
  - RSI_oversold: 30
  - RSI_overbought: 70
inputs:
  - price_close
  - volume_data
conditions:
  entry:
    - Precio cruza por debajo de la banda inferior (sobreventa)
    - RSI < 30 (confirma condición de sobreventa)
    - Volumen aumenta respecto al promedio
  exit:
    - Precio cruza por encima de la media móvil (SMA)
    - Precio alcanza la banda superior
    - RSI > 70 (condición de sobrecompra)
risk_management:
  - Stop loss del 2% por debajo del punto de entrada
  - Tamaño de posición del 1.5% del capital
  - Ratio riesgo/recompensa mínimo de 1:1.5"""
    
    elif "momentum" in prompt_lower or "impulso" in prompt_lower:
        # Estrategia de Momentum
        strategy_name = "Momentum Strategy"
        strategy_description = "Estrategia de trading basada en la convergencia de indicadores de momentum para identificar tendencias fuertes y sostenibles."
        strategy_yaml = """indicators:
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - ADX (Average Directional Index)
  - Volume
parameters:
  - RSI_period: 14
  - MACD_fast: 12
  - MACD_slow: 26
  - MACD_signal: 9
  - ADX_period: 14
  - ADX_threshold: 25
inputs:
  - price_close
  - price_high
  - price_low
  - volume_data
conditions:
  entry:
    - RSI > 50 y en aumento (momentum positivo)
    - MACD cruza por encima de su línea de señal
    - ADX > 25 (indica tendencia fuerte)
    - Volumen creciente (confirma fuerza de la tendencia)
  exit:
    - RSI < 50 y en descenso (pérdida de momentum)
    - MACD cruza por debajo de su línea de señal
    - ADX < 20 (debilitamiento de la tendencia)
    - Trailing stop del 2%
risk_management:
  - Stop loss del 3% por debajo del punto de entrada
  - Tamaño de posición del 2% del capital
  - Ratio riesgo/recompensa mínimo de 1:2
  - Toma parcial de beneficios al 4% de ganancia"""
    
    elif "media" in prompt_lower or "mean" in prompt_lower or "reversion" in prompt_lower or "reversión" in prompt_lower:
        # Estrategia de Reversión a la Media
        strategy_name = "Mean Reversion Strategy"
        strategy_description = "Estrategia que busca aprovechar las desviaciones temporales del precio respecto a su media histórica, asumiendo que los precios tienden a regresar a su valor promedio."
        strategy_yaml = """indicators:
  - Moving Average (SMA)
  - RSI (Relative Strength Index)
  - Standard Deviation
  - Bollinger Bands
parameters:
  - SMA_period: 20
  - RSI_period: 14
  - RSI_oversold: 30
  - RSI_overbought: 70
  - BB_std_dev: 2
inputs:
  - price_close
  - price_high
  - price_low
conditions:
  entry:
    - Precio se desvía más de 2 desviaciones estándar de la SMA
    - RSI indica condición de sobreventa (<30) o sobrecompra (>70)
    - Precio forma patrón de vela de reversión
  exit:
    - Precio regresa a la SMA
    - RSI cruza el nivel 50
    - Precio alcanza objetivo de beneficio (distancia a la media)
risk_management:
  - Stop loss del 2.5% más allá del extremo
  - Tamaño de posición del 1.5% del capital
  - Trailing stop después de 1% de ganancia
  - Ajuste de posición según volatilidad"""
    
    elif "tendencia" in prompt_lower or "trend" in prompt_lower:
        # Estrategia de Seguimiento de Tendencia
        strategy_name = "Trend Following Strategy"
        strategy_description = "Estrategia que identifica y sigue tendencias de mercado establecidas, aprovechando movimientos direccionales prolongados."
        strategy_yaml = """indicators:
  - Moving Averages (SMA 50, SMA 200)
  - ADX (Average Directional Index)
  - Parabolic SAR
  - Ichimoku Cloud
parameters:
  - SMA_fast_period: 50
  - SMA_slow_period: 200
  - ADX_period: 14
  - ADX_threshold: 20
  - PSAR_step: 0.02
  - PSAR_max: 0.2
inputs:
  - price_close
  - price_high
  - price_low
  - price_open
conditions:
  entry:
    - SMA 50 cruza por encima de SMA 200 (Golden Cross)
    - ADX > 20 (confirma fuerza de tendencia)
    - Precio por encima del Parabolic SAR
    - Precio por encima de la nube Ichimoku
  exit:
    - SMA 50 cruza por debajo de SMA 200 (Death Cross)
    - ADX < 20 (debilitamiento de tendencia)
    - Precio por debajo del Parabolic SAR
    - Precio entra en la nube Ichimoku
risk_management:
  - Stop loss del 4% por debajo del punto de entrada
  - Tamaño de posición del 2% del capital
  - Trailing stop del 3%
  - Incremento de posición en pullbacks"""
    
    elif "volumen" in prompt_lower or "volume" in prompt_lower:
        # Estrategia basada en Volumen
        strategy_name = "Volume-Based Strategy"
        strategy_description = "Estrategia que utiliza patrones de volumen para identificar posibles cambios de tendencia y puntos de entrada y salida."
        strategy_yaml = """indicators:
  - Volume
  - On-Balance Volume (OBV)
  - Volume-Weighted Average Price (VWAP)
  - Chaikin Money Flow (CMF)
  - Accumulation/Distribution Line
parameters:
  - Volume_avg_period: 20
  - Volume_threshold: 1.5
  - CMF_period: 21
  - VWAP_period: 1 (día)
inputs:
  - price_close
  - price_high
  - price_low
  - price_open
  - volume_data
conditions:
  entry:
    - Aumento significativo de volumen (>150% del promedio)
    - OBV confirma dirección del precio (sin divergencia)
    - Precio cruza por encima del VWAP
    - CMF positivo y creciente
  exit:
    - Disminución de volumen en continuación de tendencia
    - OBV diverge del precio
    - Precio cruza por debajo del VWAP
    - CMF cambia a negativo
risk_management:
  - Stop loss del 2.5% por debajo del punto de entrada
  - Tamaño de posición del 1.5% del capital
  - Toma de ganancias parcial al 2%
  - Ajuste de posición según ratio volumen/precio"""
    
    elif "breakout" in prompt_lower or "ruptura" in prompt_lower:
        # Estrategia de Ruptura (Breakout)
        strategy_name = "Breakout Trading Strategy"
        strategy_description = "Estrategia que busca identificar y aprovechar rupturas de niveles clave de soporte y resistencia con confirmación de volumen."
        strategy_yaml = """indicators:
  - Support/Resistance Levels
  - Volume
  - ATR (Average True Range)
  - RSI (Relative Strength Index)
parameters:
  - Lookback_period: 20
  - Volume_threshold: 2.0
  - ATR_period: 14
  - RSI_period: 14
inputs:
  - price_close
  - price_high
  - price_low
  - volume_data
conditions:
  entry:
    - Precio rompe nivel clave de resistencia/soporte
    - Volumen aumenta significativamente (>200% del promedio)
    - ATR aumenta (indica volatilidad creciente)
    - RSI confirma dirección del breakout
  exit:
    - Precio alcanza el objetivo proyectado (altura del patrón)
    - Volumen disminuye significativamente
    - Precio retrocede al nivel de ruptura
    - Formación de patrón de reversión
risk_management:
  - Stop loss en el nivel de ruptura (más un pequeño margen)
  - Tamaño de posición basado en ATR (1x ATR)
  - Ratio riesgo/recompensa mínimo de 1:2
  - Trailing stop después de alcanzar 1:1"""
    
    elif "oscilador" in prompt_lower or "oscillator" in prompt_lower:
        # Estrategia basada en Osciladores
        strategy_name = "Oscillator-Based Strategy"
        strategy_description = "Estrategia que utiliza múltiples osciladores para identificar condiciones de sobrecompra y sobreventa, así como divergencias precio-indicador."
        strategy_yaml = """indicators:
  - RSI (Relative Strength Index)
  - Stochastic Oscillator
  - CCI (Commodity Channel Index)
  - MACD (Moving Average Convergence Divergence)
parameters:
  - RSI_period: 14
  - RSI_oversold: 30
  - RSI_overbought: 70
  - Stochastic_K: 14
  - Stochastic_D: 3
  - CCI_period: 20
  - MACD_fast: 12
  - MACD_slow: 26
  - MACD_signal: 9
inputs:
  - price_close
  - price_high
  - price_low
conditions:
  entry:
    - Múltiples osciladores en zona de sobreventa/sobrecompra
    - Divergencia positiva/negativa entre precio y osciladores
    - Cruce de líneas en Stochastic u otros osciladores
    - Confirmación de cambio de tendencia en múltiples timeframes
  exit:
    - Osciladores alcanzan zonas extremas opuestas
    - Divergencia en dirección contraria
    - Señales de agotamiento de tendencia
    - Pérdida de momentum en indicadores
risk_management:
  - Stop loss basado en swing previo
  - Tamaño de posición del 1.5% del capital
  - Toma de beneficios escalonada
  - Ajuste de posición según volatilidad del mercado"""
    
    else:
        # Estrategia genérica si no se detecta un tipo específico
        strategy_name = "Multi-Indicator Trading Strategy"
        strategy_description = f"Estrategia de trading personalizada generada a partir del prompt: '{prompt}'. Combina múltiples indicadores técnicos para identificar oportunidades de mercado."
        strategy_yaml = """indicators:
  - Moving Average (SMA)
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Volume
parameters:
  - SMA_period: 20
  - RSI_period: 14
  - MACD_fast: 12
  - MACD_slow: 26
  - MACD_signal: 9
inputs:
  - price_close
  - price_high
  - price_low
  - volume_data
conditions:
  entry:
    - Precio cruza por encima de la SMA
    - RSI entre 40 y 60 (zona neutral con momentum)
    - MACD cruza por encima de su línea de señal
    - Volumen confirma el movimiento
  exit:
    - Precio cruza por debajo de la SMA
    - RSI > 70 (sobrecompra) o RSI < 30 (sobreventa)
    - MACD cruza por debajo de su línea de señal
    - Disminución de volumen
risk_management:
  - Stop loss del 3% por debajo del punto de entrada
  - Tamaño de posición del 2% del capital
  - Ratio riesgo/recompensa mínimo de 1:1.5
  - Revisión periódica de la estrategia"""
    
    logger.info(f"ESTRATEGIA GENERADA: {strategy_name}")
    logger.info("YAML GENERADO EXITOSAMENTE")
    
    # Devolver un diccionario con todos los campos
    return {
        "name": strategy_name,
        "description": strategy_description,
        "yaml_content": strategy_yaml
    }

def save_strategy_to_db(strategy_data: dict) -> bool:
    """
    Guarda una estrategia en la base de datos.
    Si ya existe una estrategia con el mismo nombre, la reemplaza.
    Retorna True si se guardó correctamente, False en caso contrario.
    """
    logger.info("="*50)
    logger.info("GUARDANDO ESTRATEGIA")
    logger.info("="*50)
    
    try:
        # Configurar conexión a la base de datos
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "sql1")
        )
        
        cursor = connection.cursor()
        
        # Crear un diccionario con los datos de la estrategia
        strategy = {
            'uuid': str(uuid.uuid4()),
            'name': strategy_data.get('name', 'Strategy_' + str(uuid.uuid4())[:8]),
            'description': strategy_data.get('description', 'Estrategia generada automáticamente'),
            'config_yaml': strategy_data.get('yaml_content', '')
        }
        
        # Verificar si ya existe una estrategia con el mismo nombre
        check_query = "SELECT id, uuid FROM strategies WHERE name = %s"
        cursor.execute(check_query, (strategy['name'],))
        existing = cursor.fetchone()
        
        if existing:
            # Si existe, actualizar en lugar de insertar
            logger.info(f"ACTUALIZANDO ESTRATEGIA EXISTENTE CON ID: {existing[0]}")
            update_query = """
            UPDATE strategies 
            SET description = %s, config_yaml = %s 
            WHERE id = %s
            """
            cursor.execute(update_query, (strategy['description'], strategy['config_yaml'], existing[0]))
            strategy['uuid'] = existing[1]  # Mantener el UUID original
        else:
            # Si no existe, insertar nueva
            insert_query = """
            INSERT INTO strategies (uuid, name, description, config_yaml)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (strategy['uuid'], strategy['name'], strategy['description'], strategy['config_yaml']))
        
        connection.commit()
        
        logger.info(f"ESTRATEGIA GUARDADA CON UUID: {strategy['uuid']}")
        logger.info("ESTRATEGIA GUARDADA EXITOSAMENTE")
        
        return True
    except Exception as e:
        logger.error(f"ERROR AL GUARDAR ESTRATEGIA: {e}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

@app.post("/generate_strategy/")
def generate_strategy(request: StrategyRequest):
    """Endpoint para generar una estrategia"""
    logger.info("="*50)
    logger.info(f"GENERANDO ESTRATEGIA PARA PROMPT: {request.prompt}")
    logger.info("="*50)
    
    try:
        # Generar la estrategia
        strategy_data = generate_strategy_yaml(request.prompt)
        
        logger.info("ESTRATEGIA GENERADA CON ÉXITO")
        return {
            "status": "success",
            "strategy_name": strategy_data["name"],
            "strategy_description": strategy_data["description"],
            "strategy_yaml": strategy_data["yaml_content"]
        }
    except Exception as e:
        logger.error(f"ERROR AL GENERAR ESTRATEGIA: {e}")
        raise HTTPException(status_code=500, detail=f"Error al generar la estrategia: {str(e)}")

@app.post("/save_strategy/")
def save_strategy(request: SaveStrategyRequest):
    """Endpoint para guardar una estrategia en la base de datos"""
    try:
        # Guardar la estrategia
        if save_strategy_to_db(request.strategy_data):
            return {"status": "success", "message": "Estrategia guardada correctamente"}
        else:
            raise HTTPException(status_code=500, detail="Error al guardar la estrategia")
    except Exception as e:
        logger.error(f"ERROR AL GUARDAR ESTRATEGIA: {e}")
        raise HTTPException(status_code=500, detail=f"Error al guardar la estrategia: {str(e)}")