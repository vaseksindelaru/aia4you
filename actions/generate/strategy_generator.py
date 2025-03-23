from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
import os
from dotenv import load_dotenv
import yaml
import uuid
import logging
import re

# Configuración del logger
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strategy_log.txt")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Indicadores disponibles (como respaldo)
AVAILABLE_INDICATORS = {
    "Moving Average": "MA",
    "Relative Strength Index": "RSI",
    "Moving Average Convergence Divergence": "MACD",
    "Momentum": "MOM",
    "Bollinger Bands": "BB",
    "Average Directional Index": "ADX",
    "Stochastic Oscillator": "STOCH",
    "Volume": "VOL"
}

# Modelos para las solicitudes
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

@app.get("/")
def root():
    """Endpoint raíz"""
    logger.info("="*50)
    logger.info("ACCESO A RAIZ")
    logger.info("="*50)
    return {"message": "API de generación de estrategias"}

@app.get("/test/")
def test():
    """Endpoint de prueba"""
    logger.info("="*50)
    logger.info("ACCESO A TEST")
    logger.info("="*50)
    return {"message": "Test exitoso"}

# Configuración de la base de datos MySQL
db_config = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "21blackjack"),
    "database": os.getenv("MYSQL_DATABASE", "sql1")
}

def get_available_indicators() -> list:
    """Obtiene los indicadores disponibles de la base de datos"""
    logger.info("="*50)
    logger.info("BUSCANDO INDICADORES")
    logger.info("="*50)
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        query = "SELECT name FROM indicators"
        cursor.execute(query)
        
        indicators = [row[0] for row in cursor.fetchall()]
        logger.info(f"INDICADORES ENCONTRADOS: {indicators}")
        return indicators
        
    except Exception as e:
        logger.error(f"ERROR EN INDICADORES: {e}")
        return []
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def generate_strategy_yaml(prompt: str) -> dict:
    """
    Genera una configuración YAML para una estrategia basada en el prompt del usuario.
    Devuelve un diccionario con nombre, descripción y YAML.
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
    
    # Generar nombre de la estrategia basado en el prompt
    strategy_name = ""
    if "momentum" in prompt_lower:
        selected_indicators.append("Momentum")
        strategy_name = "Momentum Strategy"
    
    if "rsi" in prompt_lower or "fuerza" in prompt_lower or "strength" in prompt_lower:
        selected_indicators.append("Relative Strength Index")
        if not strategy_name:
            strategy_name = "RSI Strategy"
    
    if "macd" in prompt_lower or "convergencia" in prompt_lower or "divergencia" in prompt_lower:
        selected_indicators.append("Moving Average Convergence Divergence")
        if not strategy_name:
            strategy_name = "MACD Strategy"
    
    if "media" in prompt_lower or "moving" in prompt_lower or "average" in prompt_lower:
        selected_indicators.append("Moving Average")
        if not strategy_name:
            strategy_name = "Moving Average Strategy"
    
    if "bollinger" in prompt_lower or "bandas" in prompt_lower:
        selected_indicators.append("Bollinger Bands")
        if not strategy_name:
            strategy_name = "Bollinger Bands Strategy"
    
    if "volumen" in prompt_lower or "volume" in prompt_lower:
        selected_indicators.append("Volume")
        if not strategy_name:
            strategy_name = "Volume-Based Strategy"
    
    # Si no se seleccionó ningún indicador, incluir algunos por defecto
    if not selected_indicators:
        selected_indicators = ["Moving Average", "Relative Strength Index", "Momentum"]
        strategy_name = "Multi-Indicator Strategy"
    
    # Si no se generó un nombre, usar uno genérico con timestamp
    if not strategy_name:
        strategy_name = f"Trading Strategy {uuid.uuid4()[:8]}"
    
    # Generar descripción basada en los indicadores seleccionados
    strategy_description = f"Estrategia de trading basada en {', '.join(selected_indicators)}. "
    strategy_description += f"Generada a partir del prompt: '{prompt}'"
    
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
    
    # Devolver un diccionario con todos los campos
    return {
        "name": strategy_name,
        "description": strategy_description,
        "yaml_content": strategy_yaml
    }

def save_strategy_to_db(strategy_data: dict) -> bool:
    """
    Guarda una estrategia en la base de datos
    """
    logger.info("="*50)
    logger.info("GUARDANDO ESTRATEGIA")
    logger.info("="*50)
    try:
        # Preparar los datos
        strategy = {
            'uuid': str(uuid.uuid4()),
            'name': strategy_data.get('name', 'Strategy_' + str(uuid.uuid4())[:8]),
            'description': strategy_data.get('description', 'Estrategia generada automáticamente'),
            'config_yaml': strategy_data.get('yaml_content', '')
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