from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
import os
import uuid
import yaml
import logging
import sys
from datetime import datetime
from dotenv import load_dotenv
import requests

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("generator_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Agregar el directorio raíz al path para poder importar módulos correctamente
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar el módulo fuzzy_check
from actions.check.fuzzy_check import fuzzy_match, get_similarity_ratio

# Definición de modelos
class StrategyRequest(BaseModel):
    prompt: str

class IndicatorRequest(BaseModel):
    prompt: str

class SaveStrategyRequest(BaseModel):
    strategy_data: dict

class SaveIndicatorRequest(BaseModel):
    indicator_data: dict

# Cargar variables de entorno
load_dotenv()

# Configuración de FastAPI
app = FastAPI(title="AIA4You Generator API", 
              description="API unificada para generación de estrategias e indicadores de trading")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """Endpoint raíz"""
    return {"message": "API unificada de generación de estrategias e indicadores"}

@app.get("/health")
def health_check():
    """Endpoint para verificar si el servicio está activo"""
    return {"status": "ok"}

#######################
# FUNCIONES DE INDICADORES
#######################

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
    
    logger.info(f"INDICADOR GENERADO: {indicator_data['name']}")
    return indicator_data

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
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "sql1")
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
        return True
    except Exception as e:
        logger.error(f"ERROR AL GUARDAR INDICADOR: {e}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

#######################
# FUNCIONES DE ESTRATEGIAS
#######################

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
    
    # Devolver un diccionario con todos los campos
    return {
        "name": strategy_name,
        "description": strategy_description,
        "yaml_content": strategy_yaml
    }

def save_strategy_to_db(strategy_data: dict) -> tuple:
    """
    Guarda una estrategia en la base de datos.
    Si ya existe una estrategia con el mismo nombre, la reemplaza.
    Retorna una tupla (bool, str) con el éxito de la operación y el UUID de la estrategia.
    """
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
            'config_yaml': strategy_data.get('config_yaml', '')
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
            logger.info("INSERTANDO NUEVA ESTRATEGIA")
            insert_query = """
            INSERT INTO strategies (uuid, name, description, config_yaml)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (strategy['uuid'], strategy['name'], strategy['description'], strategy['config_yaml']))
        
        connection.commit()
        logger.info(f"ESTRATEGIA GUARDADA CON UUID: {strategy['uuid']}")
        
        return True, strategy['uuid']
    except Exception as e:
        logger.error(f"ERROR AL GUARDAR ESTRATEGIA: {e}")
        return False, None
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def extract_indicators_from_yaml(yaml_content):
    """
    Extrae los nombres de los indicadores mencionados en el YAML de una estrategia.
    
    Args:
        yaml_content (str): Contenido YAML de la estrategia
        
    Returns:
        list: Lista de nombres de indicadores
    """
    try:
        # Cargar el YAML
        strategy_dict = yaml.safe_load(yaml_content)
        
        # Extraer indicadores
        indicators = []
        if isinstance(strategy_dict, dict) and "indicators" in strategy_dict:
            indicators = strategy_dict["indicators"]
        
        return indicators if isinstance(indicators, list) else []
    except Exception as e:
        logger.error(f"ERROR AL EXTRAER INDICADORES DEL YAML: {str(e)}")
        return []

def verify_and_generate_indicators(strategy_yaml):
    """
    Verifica si los indicadores mencionados en la estrategia existen,
    y si no, solicita su generación.
    
    Args:
        strategy_yaml (str): Contenido YAML de la estrategia
        
    Returns:
        list: Lista de indicadores generados
    """
    # Extraer indicadores del YAML
    indicators = extract_indicators_from_yaml(strategy_yaml)
    
    generated_indicators = []
    
    # Verificar cada indicador
    for indicator in indicators:
        logger.info(f"VERIFICANDO EXISTENCIA DEL INDICADOR: {indicator}")
        
        # Verificar si el indicador existe
        exists, _ = check_indicator_exists(indicator)
        
        if not exists:
            logger.info(f"GENERANDO INDICADOR: {indicator}")
            
            # Generar el indicador directamente
            indicator_data = generate_indicator_yaml(f"Crear indicador de trading {indicator}")
            
            # Guardar el indicador en la base de datos
            if save_indicator_to_db(indicator_data):
                generated_indicators.append(indicator)
                logger.info(f"INDICADOR GENERADO Y GUARDADO: {indicator}")
            else:
                logger.error(f"NO SE PUDO GENERAR EL INDICADOR: {indicator}")
    
    return generated_indicators

#######################
# ENDPOINTS DE LA API
#######################

@app.post("/generate_strategy/")
def generate_strategy_endpoint(request: StrategyRequest):
    """Endpoint para generar una estrategia"""
    logger.info("="*50)
    logger.info(f"GENERANDO ESTRATEGIA PARA PROMPT: {request.prompt}")
    logger.info("="*50)
    
    try:
        # Generar la estrategia
        strategy_data = generate_strategy_yaml(request.prompt)
        
        # Verificar y generar indicadores necesarios
        generated_indicators = verify_and_generate_indicators(strategy_data["yaml_content"])
        
        logger.info("ESTRATEGIA GENERADA CON ÉXITO")
        return {
            "status": "success",
            "strategy_name": strategy_data["name"],
            "strategy_description": strategy_data["description"],
            "config_yaml": strategy_data["yaml_content"],
            "generated_indicators": generated_indicators
        }
    except Exception as e:
        logger.error(f"ERROR AL GENERAR ESTRATEGIA: {e}")
        raise HTTPException(status_code=500, detail=f"Error al generar la estrategia: {str(e)}")

@app.post("/save_strategy/")
def save_strategy_endpoint(request: SaveStrategyRequest):
    """Endpoint para guardar una estrategia en la base de datos"""
    try:
        logger.info("="*50)
        logger.info("GUARDANDO ESTRATEGIA")
        logger.info("="*50)
        
        # Guardar la estrategia
        result, strategy_uuid = save_strategy_to_db(request.strategy_data)
        
        if result:
            return {
                "status": "success", 
                "message": "Estrategia guardada correctamente",
                "uuid": strategy_uuid
            }
        else:
            raise HTTPException(status_code=500, detail="Error al guardar la estrategia")
    except Exception as e:
        logger.error(f"ERROR AL GUARDAR ESTRATEGIA: {e}")
        raise HTTPException(status_code=500, detail=f"Error al guardar la estrategia: {str(e)}")

@app.post("/generate_indicator/")
def generate_indicator_endpoint(request: IndicatorRequest):
    """Endpoint para generar un indicador basado en un prompt"""
    try:
        logger.info(f"SOLICITUD DE GENERACIÓN DE INDICADOR: {request.prompt}")
        
        # Generar YAML del indicador
        indicator_data = generate_indicator_yaml(request.prompt)
        
        # Registrar información del indicador generado
        logger.info(f"INDICADOR GENERADO: {indicator_data['name']}")
        
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
def save_indicator_endpoint(request: SaveIndicatorRequest):
    """Endpoint para guardar un indicador en la base de datos"""
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

@app.get("/check_indicator/{indicator_name}")
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
    logger.info("INICIANDO SERVIDOR UNIFICADO DE GENERACIÓN")
    logger.info("="*50)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8510)
