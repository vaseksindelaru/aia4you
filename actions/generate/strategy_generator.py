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
import sys

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

# Añadir el directorio raíz al path para poder importar módulos personalizados
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from actions.check.fuzzy_check import fuzzy_match, get_similarity_ratio

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

def request_indicator_generation(indicator_name):
    """
    Solicita la generación de un nuevo indicador al servicio de generación de indicadores.
    
    Args:
        indicator_name (str): Nombre del indicador a generar
        
    Returns:
        bool: True si se generó correctamente, False en caso contrario
    """
    try:
        # URL del servicio de generación de indicadores
        indicator_service_url = "http://localhost:8506/generate_indicator/"
        
        # Preparar el prompt para la generación del indicador
        prompt = f"Crear indicador de trading {indicator_name}"
        
        # Enviar solicitud al servicio de generación de indicadores
        logger.info(f"SOLICITANDO GENERACIÓN DEL INDICADOR: {indicator_name}")
        response = requests.post(
            indicator_service_url,
            json={"prompt": prompt}
        )
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("status") == "success":
                logger.info(f"INDICADOR GENERADO EXITOSAMENTE: {indicator_name}")
                
                # Verificar que todos los datos necesarios estén presentes
                indicator_data = response_data.get("indicator_data", {})
                if not all(key in indicator_data for key in ["name", "description", "config_yaml", "implementation_yaml"]):
                    logger.error(f"DATOS DE INDICADOR INCOMPLETOS: {indicator_data}")
                    return False
                
                # Guardar el indicador generado
                save_url = "http://localhost:8506/save_indicator/"
                logger.info(f"GUARDANDO INDICADOR: {indicator_name}")
                logger.debug(f"DATOS DEL INDICADOR: {indicator_data}")
                
                save_response = requests.post(
                    save_url,
                    json={"indicator_data": indicator_data}
                )
                
                if save_response.status_code == 200:
                    save_result = save_response.json()
                    if save_result.get("status") == "success":
                        logger.info(f"INDICADOR GUARDADO EXITOSAMENTE: {indicator_name}")
                        logger.info(f"INDICADOR GENERADO Y GUARDADO: {indicator_name}")
                        return True
                    else:
                        logger.error(f"ERROR AL GUARDAR INDICADOR: {save_result.get('message', 'Error desconocido')}")
                else:
                    logger.error(f"ERROR AL GUARDAR INDICADOR: {save_response.text}")
            else:
                logger.error(f"ERROR EN LA RESPUESTA DEL SERVICIO DE INDICADORES: {response_data}")
        else:
            logger.error(f"ERROR AL SOLICITAR GENERACIÓN DE INDICADOR: {response.text}")
        
        return False
    except Exception as e:
        logger.error(f"ERROR AL SOLICITAR GENERACIÓN DE INDICADOR: {str(e)}")
        return False

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
            logger.info(f"SOLICITANDO GENERACIÓN DEL INDICADOR: {indicator}")
            
            # Solicitar generación del indicador
            if request_indicator_generation(indicator):
                generated_indicators.append(indicator)
                logger.info(f"INDICADOR GENERADO Y GUARDADO: {indicator}")
            else:
                logger.error(f"NO SE PUDO GENERAR EL INDICADOR: {indicator}")
    
    return generated_indicators

@app.post("/generate_strategy/")
def generate_strategy(request: StrategyRequest):
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
            "strategy_yaml": strategy_data["yaml_content"],
            "generated_indicators": generated_indicators
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