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

# Prompt para generar estrategias de trading con Chain of Thought y one-shot
STRATEGY_PROMPT = """
Genera una estrategia de trading basada en el siguiente prompt: "{prompt}"

Sigue este proceso paso a paso (Chain of Thought):

1. Analiza el prompt para identificar el tipo de estrategia solicitada.
2. Determina qué indicadores técnicos serían más adecuados para esta estrategia.
3. Define las condiciones de entrada y salida para la estrategia.
4. Establece los parámetros de gestión de riesgo.
5. Crea un nombre descriptivo y una descripción clara para la estrategia.

Ejemplo (one-shot) para una estrategia de Momentum Trading:

Análisis del prompt:
- Se solicita una estrategia de momentum trading
- Este tipo de estrategia se basa en la continuación de tendencias
- Necesitamos indicadores que midan la fuerza de la tendencia

Indicadores seleccionados:
- RSI (Relative Strength Index): Mide la velocidad y cambio de los movimientos de precio
- MACD (Moving Average Convergence Divergence): Identifica cambios en la fuerza, dirección y momentum
- ADX (Average Directional Index): Mide la fuerza de la tendencia

Condiciones de entrada:
- RSI > 50 y en aumento (para tendencias alcistas)
- MACD cruza por encima de su línea de señal
- ADX > 25 (indica tendencia fuerte)

Condiciones de salida:
- RSI < 50 y en descenso
- MACD cruza por debajo de su línea de señal
- Trailing stop del 2%

Gestión de riesgo:
- Stop loss del 3%
- Tamaño de posición del 2% del capital
- Ratio riesgo/recompensa mínimo de 1:2

Nombre: "Triple Momentum Strategy"
Descripción: "Estrategia de trading basada en la convergencia de tres indicadores de momentum (RSI, MACD y ADX) para identificar tendencias fuertes y sostenibles."

La respuesta debe estar en formato de tabla como se muestra a continuación:

| Campo | Valor |
|-------|-------|
| Nombre | Triple Momentum Strategy |
| Descripción | Estrategia de trading basada en la convergencia de tres indicadores de momentum (RSI, MACD y ADX) para identificar tendencias fuertes y sostenibles. |
| Indicadores | RSI, MACD, ADX |
| Condiciones de entrada | RSI > 50 y en aumento, MACD cruza por encima de su línea de señal, ADX > 25 |
| Condiciones de salida | RSI < 50 y en descenso, MACD cruza por debajo de su línea de señal, Trailing stop del 2% |
| Gestión de riesgo | Stop loss del 3%, Tamaño de posición del 2% del capital, Ratio riesgo/recompensa mínimo de 1:2 |
"""

def generate_strategy_yaml(prompt: str) -> dict:
    """
    Genera una configuración YAML para una estrategia basada en el prompt del usuario.
    Devuelve un diccionario con nombre, descripción y YAML.
    """
    logger.info(f"GENERANDO ESTRATEGIA PARA: {prompt}")
    
    # Aquí se implementaría la lógica para generar la estrategia basada en el prompt
    # Por ahora, usamos un ejemplo simplificado para Momentum Trading
    
    strategy_name = "Triple Momentum Strategy"
    strategy_description = "Estrategia de trading basada en la convergencia de tres indicadores de momentum (RSI, MACD y ADX) para identificar tendencias fuertes y sostenibles."
    
    # Generar el YAML
    strategy_yaml = """indicators:
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - ADX (Average Directional Index)
inputs:
  - price_close
  - volume_data
conditions:
  entry:
    - RSI > 50 y en aumento
    - MACD cruza por encima de su línea de señal
    - ADX > 25
  exit:
    - RSI < 50 y en descenso
    - MACD cruza por debajo de su línea de señal
    - Trailing stop del 2%
risk_management:
  - Stop loss del 3%
  - Tamaño de posición del 2% del capital
  - Ratio riesgo/recompensa mínimo de 1:2
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