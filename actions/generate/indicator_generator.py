from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
import os
import sys
import uuid
import logging
from datetime import datetime
from dotenv import load_dotenv
import requests
import uvicorn

# Agregar el directorio raíz al path para poder importar módulos correctamente
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Importar el módulo fuzzy_check
from actions.check.fuzzy_check import fuzzy_match, get_similarity_ratio

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("indicator_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Definición de modelos
class IndicatorRequest(BaseModel):
    prompt: str

class SaveIndicatorRequest(BaseModel):
    indicator_data: dict

# Cargar variables de entorno
load_dotenv()

# Configuración de la aplicación FastAPI
app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """
    Endpoint para verificar si el servicio está activo.
    """
    return {"status": "ok"}

def check_indicator_exists(indicator_name, threshold=0.85):
    """
    Verifica si un indicador con nombre similar ya existe en la base de datos
    usando fuzzy matching.
    
    Args:
        indicator_name (str): Nombre del indicador a verificar
        threshold (float): Umbral de similitud (0-1)
        
    Returns:
        tuple: (bool, dict) - (existe, datos_del_indicador_si_existe)
    """
    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE")
        )
        
        cursor = connection.cursor(dictionary=True)
        
        # Obtener todos los indicadores
        query = "SELECT * FROM indicators"
        cursor.execute(query)
        indicators = cursor.fetchall()
        
        # Verificar similitud con cada indicador usando fuzzy_check
        for indicator in indicators:
            # Usar fuzzy_match de fuzzy_check.py para verificar similitud
            if fuzzy_match(indicator_name, indicator['name'], threshold):
                similarity = get_similarity_ratio(indicator_name, indicator['name'])
                logger.info(f"INDICADOR SIMILAR ENCONTRADO: {indicator['name']} (Similitud: {similarity:.2f})")
                return True, indicator
        
        logger.info(f"NO SE ENCONTRÓ INDICADOR SIMILAR A: {indicator_name}")
        return False, None
    
    except Exception as e:
        logger.error(f"ERROR AL VERIFICAR INDICADOR: {e}")
        return False, None
    
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def generate_indicator_yaml(prompt: str) -> dict:
    """
    Genera una configuración YAML para un indicador basado en el prompt del usuario.
    Devuelve un diccionario con nombre, descripción, YAML de configuración y YAML de implementación.
    """
    logger.info(f"GENERANDO INDICADOR PARA: {prompt}")
    
    # Convertir el prompt a minúsculas para facilitar la búsqueda de palabras clave
    prompt_lower = prompt.lower()
    
    # Detectar el tipo de indicador solicitado basado en palabras clave
    if "momentum" in prompt_lower or "impulso" in prompt_lower:
        # Indicador de Momentum
        indicator_name = "Momentum (MOM)"
        indicator_description = "Indicador que mide la tasa de cambio del precio en un período específico, identificando la fuerza de una tendencia."
        
        # YAML de configuración
        config_yaml = """name: momentumIndicator
indicator: momentum
inputs:
  - price_data: "Serie temporal de precios (cierre)"
conditions:
  period: 14
  signal: "MOM > 0 (alcista), MOM < 0 (bajista)"
"""
        
        # YAML de implementación
        implementation_yaml = """implementation:
  formula: "MOM = close[t] - close[t - period]"
  parameters:
    period: 14
  signals:
    buy: "MOM > 0"
    sell: "MOM < 0"
  dependencies:
    - "numpy: para cálculos matemáticos"
"""
    
    elif "rsi" in prompt_lower or "relative strength index" in prompt_lower or "índice de fuerza relativa" in prompt_lower:
        # Indicador RSI
        indicator_name = "Relative Strength Index (RSI)"
        indicator_description = "Indicador de momentum que mide la velocidad y el cambio de los movimientos de precio, identificando condiciones de sobrecompra o sobreventa."
        
        # YAML de configuración
        config_yaml = """name: rsiIndicator
indicator: rsi
inputs:
  - price_data: "Serie temporal de precios (cierre)"
conditions:
  period: 14
  overbought: 70
  oversold: 30
  signal: "RSI < 30 (sobreventa/compra), RSI > 70 (sobrecompra/venta)"
"""
        
        # YAML de implementación
        implementation_yaml = """implementation:
  formula: |
    "U = max(0, close[t] - close[t-1])"
    "D = max(0, close[t-1] - close[t])"
    "RS = SMA(U, period) / SMA(D, period)"
    "RSI = 100 - (100 / (1 + RS))"
  parameters:
    period: 14
    overbought: 70
    oversold: 30
  signals:
    buy: "RSI < 30 (condición de sobreventa)"
    sell: "RSI > 70 (condición de sobrecompra)"
  dependencies:
    - "numpy: para cálculos matemáticos"
    - "pandas: para manejo de series temporales"
"""
    
    elif "macd" in prompt_lower or "moving average convergence divergence" in prompt_lower:
        # Indicador MACD
        indicator_name = "Moving Average Convergence Divergence (MACD)"
        indicator_description = "Indicador de seguimiento de tendencia que muestra la relación entre dos medias móviles exponenciales del precio."
        
        # YAML de configuración
        config_yaml = """name: macdIndicator
indicator: macd
inputs:
  - price_data: "Serie temporal de precios (cierre)"
conditions:
  fast_period: 12
  slow_period: 26
  signal_period: 9
  signal: "MACD cruza por encima de la línea de señal (alcista), MACD cruza por debajo de la línea de señal (bajista)"
"""
        
        # YAML de implementación
        implementation_yaml = """implementation:
  formula: |
    "EMA_fast = EMA(close, fast_period)"
    "EMA_slow = EMA(close, slow_period)"
    "MACD_line = EMA_fast - EMA_slow"
    "Signal_line = EMA(MACD_line, signal_period)"
    "Histogram = MACD_line - Signal_line"
  parameters:
    fast_period: 12
    slow_period: 26
    signal_period: 9
  signals:
    buy: "MACD_line cruza por encima de Signal_line"
    sell: "MACD_line cruza por debajo de Signal_line"
  dependencies:
    - "numpy: para cálculos matemáticos"
    - "pandas: para manejo de series temporales"
    - "ta-lib: para cálculo de indicadores técnicos"
"""
    
    elif "bollinger" in prompt_lower or "bandas" in prompt_lower:
        # Indicador Bollinger Bands
        indicator_name = "Bollinger Bands (BB)"
        indicator_description = "Indicador que utiliza la desviación estándar para determinar la volatilidad del precio y posibles niveles de sobrecompra o sobreventa."
        
        # YAML de configuración
        config_yaml = """name: bollingerBandsIndicator
indicator: bollinger_bands
inputs:
  - price_data: "Serie temporal de precios (cierre)"
conditions:
  period: 20
  std_dev: 2
  signal: "Precio toca la banda inferior (posible sobreventa), Precio toca la banda superior (posible sobrecompra)"
"""
        
        # YAML de implementación
        implementation_yaml = """implementation:
  formula: |
    "SMA = SMA(close, period)"
    "Std_Dev = StdDev(close, period)"
    "Upper_Band = SMA + (Std_Dev * std_dev_multiplier)"
    "Lower_Band = SMA - (Std_Dev * std_dev_multiplier)"
  parameters:
    period: 20
    std_dev_multiplier: 2
  signals:
    buy: "Precio cruza por debajo de la banda inferior"
    sell: "Precio cruza por encima de la banda superior"
  dependencies:
    - "numpy: para cálculos matemáticos"
    - "pandas: para manejo de series temporales"
"""
    
    elif "adx" in prompt_lower or "average directional index" in prompt_lower or "índice direccional promedio" in prompt_lower:
        # Indicador ADX
        indicator_name = "Average Directional Index (ADX)"
        indicator_description = "Indicador que mide la fuerza de una tendencia, independientemente de su dirección."
        
        # YAML de configuración
        config_yaml = """name: adxIndicator
indicator: adx
inputs:
  - price_data: "Serie temporal de precios (cierre, máximo, mínimo)"
conditions:
  period: 14
  threshold: 25
  signal: "ADX > 25 (tendencia fuerte), ADX < 20 (tendencia débil)"
"""
        
        # YAML de implementación
        implementation_yaml = """implementation:
  formula: |
    "TR = max(high[t] - low[t], abs(high[t] - close[t-1]), abs(low[t] - close[t-1]))"
    "+DM = max(0, high[t] - high[t-1])"
    "-DM = max(0, low[t-1] - low[t])"
    "+DI = 100 * SMA(+DM, period) / SMA(TR, period)"
    "-DI = 100 * SMA(-DM, period) / SMA(TR, period)"
    "DX = 100 * abs(+DI - -DI) / (+DI + -DI)"
    "ADX = SMA(DX, period)"
  parameters:
    period: 14
    threshold: 25
  signals:
    strength: "ADX > 25 indica tendencia fuerte"
    direction: "Si +DI > -DI, tendencia alcista; si -DI > +DI, tendencia bajista"
  dependencies:
    - "numpy: para cálculos matemáticos"
    - "pandas: para manejo de series temporales"
    - "ta-lib: para cálculo de indicadores técnicos"
"""
    
    elif "stochastic" in prompt_lower or "estocástico" in prompt_lower:
        # Indicador Stochastic Oscillator
        indicator_name = "Stochastic Oscillator"
        indicator_description = "Oscilador que compara el precio de cierre actual con el rango de precios durante un período determinado, identificando condiciones de sobrecompra o sobreventa."
        
        # YAML de configuración
        config_yaml = """name: stochasticOscillatorIndicator
indicator: stochastic
inputs:
  - price_data: "Serie temporal de precios (cierre, máximo, mínimo)"
conditions:
  k_period: 14
  d_period: 3
  overbought: 80
  oversold: 20
  signal: "K cruza por encima de D (alcista), K cruza por debajo de D (bajista)"
"""
        
        # YAML de implementación
        implementation_yaml = """implementation:
  formula: |
    "Lowest_Low = min(low, k_period)"
    "Highest_High = max(high, k_period)"
    "%K = 100 * (close - Lowest_Low) / (Highest_High - Lowest_Low)"
    "%D = SMA(%K, d_period)"
  parameters:
    k_period: 14
    d_period: 3
    overbought: 80
    oversold: 20
  signals:
    buy: "%K < 20 y %K cruza por encima de %D"
    sell: "%K > 80 y %K cruza por debajo de %D"
  dependencies:
    - "numpy: para cálculos matemáticos"
    - "pandas: para manejo de series temporales"
"""
    
    elif "volumen" in prompt_lower or "volume" in prompt_lower:
        # Indicador de Volumen
        indicator_name = "Volume Indicator"
        indicator_description = "Indicador que analiza el volumen de negociación para confirmar tendencias o identificar posibles reversiones."
        
        # YAML de configuración
        config_yaml = """name: volumeIndicator
indicator: volume
inputs:
  - price_data: "Serie temporal de precios (cierre)"
  - volume_data: "Serie temporal de volumen"
conditions:
  period: 20
  signal: "Volumen aumenta con precio (confirma tendencia), Volumen disminuye con precio (posible reversión)"
"""
        
        # YAML de implementación
        implementation_yaml = """implementation:
  formula: |
    "Volume_SMA = SMA(volume, period)"
    "Volume_Ratio = volume / Volume_SMA"
  parameters:
    period: 20
    threshold: 1.5
  signals:
    confirmation: "Volume_Ratio > 1.5 y precio en la misma dirección"
    divergence: "Volume_Ratio < 0.5 o precio y volumen en direcciones opuestas"
  dependencies:
    - "numpy: para cálculos matemáticos"
    - "pandas: para manejo de series temporales"
"""
    
    elif "obv" in prompt_lower or "on balance volume" in prompt_lower:
        # Indicador On Balance Volume
        indicator_name = "On Balance Volume (OBV)"
        indicator_description = "Indicador que relaciona el volumen con los cambios de precio, acumulando volumen en días alcistas y restándolo en días bajistas."
        
        # YAML de configuración
        config_yaml = """name: obvIndicator
indicator: obv
inputs:
  - price_data: "Serie temporal de precios (cierre)"
  - volume_data: "Serie temporal de volumen"
conditions:
  signal: "OBV aumenta (presión compradora), OBV disminuye (presión vendedora)"
"""
        
        # YAML de implementación
        implementation_yaml = """implementation:
  formula: |
    "Si close[t] > close[t-1], OBV[t] = OBV[t-1] + volume[t]"
    "Si close[t] < close[t-1], OBV[t] = OBV[t-1] - volume[t]"
    "Si close[t] = close[t-1], OBV[t] = OBV[t-1]"
  parameters: {}
  signals:
    buy: "OBV aumenta mientras el precio se mantiene o baja (divergencia alcista)"
    sell: "OBV disminuye mientras el precio se mantiene o sube (divergencia bajista)"
  dependencies:
    - "numpy: para cálculos matemáticos"
    - "pandas: para manejo de series temporales"
"""
    
    else:
        # Indicador genérico si no se detecta un tipo específico
        indicator_name = "Custom Technical Indicator"
        indicator_description = f"Indicador técnico personalizado generado a partir del prompt: '{prompt}'. Combina elementos de análisis técnico para identificar oportunidades de mercado."
        
        # YAML de configuración
        config_yaml = """name: customIndicator
indicator: custom
inputs:
  - price_data: "Serie temporal de precios (cierre, máximo, mínimo)"
  - volume_data: "Serie temporal de volumen (opcional)"
conditions:
  period: 14
  signal: "Señales personalizadas basadas en la lógica del indicador"
"""
        
        # YAML de implementación
        implementation_yaml = """implementation:
  formula: "Fórmula personalizada basada en los requisitos específicos"
  parameters:
    period: 14
    threshold: 1.0
  signals:
    buy: "Condición de compra personalizada"
    sell: "Condición de venta personalizada"
  dependencies:
    - "numpy: para cálculos matemáticos"
    - "pandas: para manejo de series temporales"
"""
    
    # Crear y retornar el diccionario con la información del indicador
    indicator_data = {
        "name": indicator_name,
        "description": indicator_description,
        "config_yaml": config_yaml,
        "implementation_yaml": implementation_yaml
    }
    
    # Verificar que todos los campos estén presentes
    for key in ["name", "description", "config_yaml", "implementation_yaml"]:
        if key not in indicator_data or not indicator_data[key]:
            logger.error(f"CAMPO FALTANTE EN DATOS DEL INDICADOR: {key}")
            # Proporcionar un valor predeterminado para evitar errores
            if key == "name":
                indicator_data[key] = f"Indicator_{str(uuid.uuid4())[:8]}"
            elif key == "description":
                indicator_data[key] = "Indicador técnico generado automáticamente"
            else:
                indicator_data[key] = "# YAML generado automáticamente\nname: defaultIndicator\ntype: technical\n"
    
    logger.info(f"INDICADOR GENERADO: {indicator_data['name']}")
    return indicator_data

def save_indicator_to_db(indicator_data: dict) -> bool:
    """
    Guarda un indicador en la base de datos.
    Si ya existe un indicador con el mismo nombre, lo reemplaza.
    Retorna True si se guardó correctamente, False en caso contrario.
    """
    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "sql1")
        )
        
        cursor = connection.cursor(dictionary=True)
        
        # Verificar si ya existe un indicador con nombre similar usando fuzzy_check
        exists, existing_indicator = check_indicator_exists(indicator_data.get('name', ''))
        
        # Crear un diccionario con los datos del indicador
        indicator = {
            'uuid': str(uuid.uuid4()),
            'name': indicator_data.get('name', 'Indicator_' + str(uuid.uuid4())[:8]),
            'description': indicator_data.get('description', 'Indicador generado automáticamente'),
            'config_yaml': indicator_data.get('config_yaml', ''),
            'implementation_yaml': indicator_data.get('implementation_yaml', '')
        }
        
        if exists:
            # Si existe, actualizar en lugar de insertar
            logger.info(f"ACTUALIZANDO INDICADOR EXISTENTE: {existing_indicator['name']}")
            update_query = """
            UPDATE indicators 
            SET description = %s, config_yaml = %s, implementation_yaml = %s 
            WHERE id = %s
            """
            cursor.execute(update_query, (
                indicator['description'], 
                indicator['config_yaml'],
                indicator['implementation_yaml'],
                existing_indicator['id']
            ))
            indicator['uuid'] = existing_indicator['uuid']  # Mantener el UUID original
        else:
            # Si no existe, insertar nuevo
            insert_query = """
            INSERT INTO indicators (uuid, name, description, config_yaml, implementation_yaml)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                indicator['uuid'], 
                indicator['name'], 
                indicator['description'], 
                indicator['config_yaml'],
                indicator['implementation_yaml']
            ))
        
        connection.commit()
        
        logger.info(f"INDICADOR GUARDADO CON UUID: {indicator['uuid']}")
        logger.info("INDICADOR GUARDADO EXITOSAMENTE")
        
        return True
    except Exception as e:
        logger.error(f"ERROR AL GUARDAR INDICADOR: {e}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

@app.get("/")
def read_root():
    """Endpoint raíz"""
    logger.info("="*50)
    logger.info("ACCESO A RAIZ")
    logger.info("="*50)
    return {"message": "API de Generación de Indicadores"}

@app.post("/generate_indicator/")
async def generate_indicator(request: IndicatorRequest):
    """
    Endpoint para generar un indicador basado en un prompt.
    """
    try:
        logger.info(f"SOLICITUD DE GENERACIÓN DE INDICADOR: {request.prompt}")
        
        # Generar YAML del indicador
        indicator_data = generate_indicator_yaml(request.prompt)
        
        # Verificar que todos los campos necesarios estén presentes
        if not all(key in indicator_data for key in ["name", "description", "config_yaml", "implementation_yaml"]):
            logger.error(f"DATOS DE INDICADOR INCOMPLETOS: {indicator_data}")
            return {"status": "error", "message": "Datos de indicador incompletos"}
        
        # Registrar información del indicador generado
        logger.info(f"INDICADOR GENERADO: {indicator_data['name']}")
        logger.debug(f"CONFIGURACIÓN YAML: {indicator_data['config_yaml']}")
        logger.debug(f"IMPLEMENTACIÓN YAML: {indicator_data['implementation_yaml']}")
        
        # Devolver la respuesta con la estructura correcta
        return {
            "status": "success",
            "message": "Indicador generado correctamente",
            "indicator_data": {
                "name": indicator_data["name"],
                "description": indicator_data["description"],
                "config_yaml": indicator_data["config_yaml"],
                "implementation_yaml": indicator_data["implementation_yaml"]
            }
        }
    except Exception as e:
        logger.error(f"ERROR AL GENERAR INDICADOR: {str(e)}")
        return {"status": "error", "message": f"Error al generar indicador: {str(e)}"}

@app.post("/save_indicator/")
async def save_indicator(request: SaveIndicatorRequest):
    """
    Endpoint para guardar un indicador en la base de datos.
    """
    try:
        logger.info(f"SOLICITUD DE GUARDADO DE INDICADOR: {request.indicator_data.get('name', 'Sin nombre')}")
        
        # Verificar que todos los campos necesarios estén presentes
        if not all(key in request.indicator_data for key in ["name", "description", "config_yaml", "implementation_yaml"]):
            logger.error(f"DATOS DE INDICADOR INCOMPLETOS: {request.indicator_data}")
            return {"status": "error", "message": "Datos de indicador incompletos"}
        
        # Guardar el indicador en la base de datos
        if save_indicator_to_db(request.indicator_data):
            logger.info(f"INDICADOR GUARDADO CORRECTAMENTE: {request.indicator_data.get('name')}")
            return {"status": "success", "message": "Indicador guardado correctamente"}
        else:
            logger.error(f"ERROR AL GUARDAR INDICADOR: {request.indicator_data.get('name')}")
            return {"status": "error", "message": "Error al guardar indicador en la base de datos"}
    except Exception as e:
        logger.error(f"ERROR AL GUARDAR INDICADOR: {str(e)}")
        return {"status": "error", "message": f"Error al guardar indicador: {str(e)}"}

@app.get("/check_indicator_exists/{indicator_name}")
def check_indicator_endpoint(indicator_name: str):
    """Endpoint para verificar si un indicador existe"""
    exists, indicator = check_indicator_exists(indicator_name)
    return {
        "exists": exists,
        "indicator": indicator
    }

# Punto de entrada para ejecutar la aplicación
if __name__ == "__main__":
    logger.info("="*50)
    logger.info("INICIANDO SERVIDOR DE INDICADORES")
    logger.info("="*50)
    uvicorn.run(app, host="0.0.0.0", port=8506)