from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
import os
from dotenv import load_dotenv
import yaml
from typing import Dict, List
import uuid
import sys
import logging
from datetime import datetime

# Ruta absoluta para el archivo de log
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strategy_log.txt")

# Configurar logging a archivo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("strategy_generator")
logger.info("="*50)
logger.info("INICIANDO SERVIDOR DE ESTRATEGIAS")
logger.info("="*50)

# Modelos de datos
class StrategyRequest(BaseModel):
    prompt: str

class SaveStrategyRequest(BaseModel):
    yaml_content: str

# Cargar variables de entorno
load_dotenv()

# Configuración de FastAPI
app = FastAPI()

# Configurar CORS para permitir solicitudes desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos
    allow_headers=["*"],  # Permitir todos los headers
)

@app.get("/")
def root():
    logger.info("="*50)
    logger.info("ACCESO A RAIZ")
    logger.info("="*50)
    return {"message": "API de generación de estrategias"}

@app.get("/test")
def test():
    logger.info("="*50)
    logger.info("TEST DE PRINTS")
    logger.info("="*50)
    return {"message": "Test de prints"}

# Configuración de la base de datos MySQL
db_config = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "21blackjack"),
    "database": os.getenv("MYSQL_DATABASE", "sql1")
}

# Diccionario de indicadores disponibles con sus abreviaturas
AVAILABLE_INDICATORS: Dict[str, str] = {
    "Moving Average": "MA",
    "Relative Strength Index": "RSI",
    "Moving Average Convergence Divergence": "MACD",
    "Momentum": "MOM",
    "Bollinger Bands": "BB",
    "Average Directional Index": "ADX",
    "Stochastic Oscillator": "STOCH",
    "Volume": "VOL"
}

def get_available_indicators() -> List[str]:
    """Obtiene los indicadores disponibles de la base de datos"""
    logger.info("="*50)
    logger.info("BUSCANDO INDICADORES")
    logger.info("="*50)
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT name FROM indicators")
        results = cursor.fetchall()
        indicators = [row['name'] for row in results]
        logger.info(f"INDICADORES ENCONTRADOS: {indicators}")
        return indicators
    except Exception as e:
        logger.error(f"ERROR EN INDICADORES: {e}")
        return []
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def generate_strategy_yaml(prompt: str) -> str:
    """
    Genera una configuración YAML para una estrategia basada en el prompt del usuario.
    """
    logger.info(f"GENERANDO ESTRATEGIA PARA: {prompt}")
    
    # Obtener indicadores disponibles
    available = get_available_indicators()
    
    # Si no hay indicadores disponibles, usar los predefinidos
    if not available:
        available = list(AVAILABLE_INDICATORS.keys())
    
    # Seleccionar indicadores apropiados basados en el prompt
    selected_indicators = []
    
    # Análisis simple del prompt para seleccionar indicadores
    prompt_lower = prompt.lower()
    
    if "momentum" in prompt_lower:
        selected_indicators.append("Momentum")
    
    if "rsi" in prompt_lower or "fuerza" in prompt_lower or "strength" in prompt_lower:
        selected_indicators.append("Relative Strength Index")
    
    if "macd" in prompt_lower or "convergencia" in prompt_lower or "divergencia" in prompt_lower:
        selected_indicators.append("Moving Average Convergence Divergence")
    
    if "media" in prompt_lower or "moving" in prompt_lower or "average" in prompt_lower:
        selected_indicators.append("Moving Average")
    
    if "bollinger" in prompt_lower or "bandas" in prompt_lower:
        selected_indicators.append("Bollinger Bands")
    
    if "volumen" in prompt_lower or "volume" in prompt_lower:
        selected_indicators.append("Volume")
    
    # Si no se seleccionó ningún indicador, incluir algunos por defecto
    if not selected_indicators:
        selected_indicators = ["Moving Average", "Relative Strength Index", "Momentum"]
    
    # Asegurarse de que solo se incluyan indicadores disponibles
    selected_indicators = [ind for ind in selected_indicators if ind in available or ind in AVAILABLE_INDICATORS.keys()]
    
    # Generar el YAML
    strategy_yaml = f"""indicators:
{chr(10).join([f"  - {ind} ({AVAILABLE_INDICATORS.get(ind, 'N/A')})" for ind in selected_indicators])}
inputs:
  - price_close  # Precios de cierre para los indicadores
  - volume_data  # Volumen opcional para sinergia
conditions:"""

    # Agregar condiciones específicas para cada indicador
    if "Momentum" in selected_indicators:
        strategy_yaml += """
  momentum:
    period: 14
    signal: "MOM > 0 (alcista), MOM < 0 (bajista)" """
    
    if "Relative Strength Index" in selected_indicators:
        strategy_yaml += """
  rsi:
    period: 14
    signal: "50 < RSI < 70 (alcista), 30 < RSI < 50 (bajista)" """
    
    if "Moving Average Convergence Divergence" in selected_indicators:
        strategy_yaml += """
  macd:
    settings: [12, 26, 9]
    signal: "MACD > Signal Line (alcista), MACD < Signal Line (bajista)" """
    
    if "Moving Average" in selected_indicators:
        strategy_yaml += """
  ma:
    period: 20
    signal: "Precio > MA (alcista), Precio < MA (bajista)" """
    
    if "Bollinger Bands" in selected_indicators:
        strategy_yaml += """
  bollinger:
    period: 20
    deviations: 2
    signal: "Precio cerca de banda superior (sobrecompra), Precio cerca de banda inferior (sobreventa)" """
    
    strategy_yaml += """
correlations:
  orderFlow: "Confirmar volumen alto en la dirección del movimiento"
"""
    
    logger.info("YAML GENERADO EXITOSAMENTE")
    return strategy_yaml

def save_strategy_to_db(yaml_content: str) -> bool:
    """
    Guarda una estrategia en la base de datos
    """
    logger.info("="*50)
    logger.info("GUARDANDO ESTRATEGIA")
    logger.info("="*50)
    try:
        # Parsear el YAML para extraer información
        strategy_data = yaml.safe_load(yaml_content)
        
        # Preparar los datos
        strategy = {
            'uuid': str(uuid.uuid4()),
            'name': 'Strategy_' + str(uuid.uuid4())[:8],  # Nombre temporal
            'description': 'Estrategia generada automáticamente',
            'config_yaml': yaml_content
        }
        
        # Conectar y guardar
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        insert_query = """
        INSERT INTO strategies (uuid, name, description, config_yaml)
        VALUES (%(uuid)s, %(name)s, %(description)s, %(config_yaml)s)
        """
        
        cursor.execute(insert_query, strategy)
        connection.commit()
        
        logger.info(f"ESTRATEGIA GUARDADA CON UUID: {strategy['uuid']}")
        return True
        
    except Exception as e:
        logger.error(f"ERROR AL GUARDAR ESTRATEGIA: {e}")
        return False
        
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

@app.post("/generate_strategy/")
async def generate_strategy(request: StrategyRequest):
    """Endpoint para generar una estrategia"""
    logger.info("="*50)
    logger.info(f"GENERANDO ESTRATEGIA PARA PROMPT: {request.prompt}")
    logger.info("="*50)
    try:
        yaml_config = generate_strategy_yaml(request.prompt)
        logger.info("ESTRATEGIA GENERADA CON ÉXITO")
        return {
            "status": "success",
            "strategy_yaml": yaml_config
        }
    except Exception as e:
        logger.error(f"ERROR AL GENERAR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_strategy/")
async def save_strategy(request: SaveStrategyRequest):
    """Endpoint para guardar una estrategia en la base de datos"""
    logger.info("="*50)
    logger.info("GUARDANDO ESTRATEGIA")
    logger.info("="*50)
    if save_strategy_to_db(request.yaml_content):
        logger.info("ESTRATEGIA GUARDADA EXITOSAMENTE")
        return {"status": "success", "message": "Estrategia guardada exitosamente"}
    else:
        logger.error("ERROR AL GUARDAR ESTRATEGIA")
        raise HTTPException(status_code=500, detail="Error al guardar la estrategia")