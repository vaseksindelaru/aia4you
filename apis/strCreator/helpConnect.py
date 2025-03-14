from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
import requests
import yaml
import json
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = FastAPI()

# Modelo Pydantic para validar el payload
class Prompt(BaseModel):
    prompt: str

# Configuración de la base de datos MySQL desde variables de entorno
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE", "sql1")
}

@app.get("/")
def read_root():
    return {"message": "API is running"}

@app.post("/help_connect/")
async def process_prompt(payload: Prompt):
    try:
        # Conectar a la base de datos y obtener datos
        indicators = []
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT config_yaml FROM apis_db WHERE name = 'MomentumTrading' LIMIT 1")
            result = cursor.fetchone()
            
            if result:
                config_yaml = result['config_yaml']
                config = yaml.safe_load(config_yaml)
                indicators = config.get("indicators", [])
                print(f"Indicadores cargados: {indicators}")
            else:
                print("No se encontraron datos en la base de datos")
                
        except Exception as db_error:
            print(f"Error de base de datos: {str(db_error)}")
            raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(db_error)}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

        # Construir el texto combinado
        combined_text = f"""
Genere consulta con expertos para diferentes casos de tareas.
Responda el prompt inicial según tarea correspondiente (A o B).

# Prompt recibido desde streamlitApp/user.py
{payload.prompt}

tarea:
caso A: 
tarea: crea nueva estrategia
consulta:
exp. 1: Identifica la lógica principal de la estrategia y sugiere indicadores 
exp. 2: Busca entre estos indicadores:

# Indicadores recibidos desde apisDb
{', '.join(indicators)}

a los indicadores sugeridos. 
En caso de:
1/ encontrarlos todos:
continúe con otros expertos, 
2/ no encontrar indicador recomendado:
crea tarea para crear nueva api del indicador con el nombre del indicador y la descripción del indicador. 
ejemplo:
 
tarea: 
crea nueva api del indicador Momentum, 
descripción: 
indica fuerza de la tendencia

continue en tarea caso B.

3/ encontrar uno o algunos de los indicadores sugeridos
a/ para indicadores no encontrados:
crea diferentes tareas, igual que en el caso 2.
b/ para indicadores encontrados:
continúe con expertos, igual que en el caso 1.

exp.3: Define ajustes óptimos para señales basados en indicadores y en lógica de la estrategia
exp.4: Busca correlaciones con estrategias existentes, para evitar redundancias o encontrar sinergias
exp.5: Crea un archivo de configuración YAML con:
name: Nombre de la estrategia
indicators: Indicadores necesarios
inputs: Datos requeridos para identificar las señales
conditions: Ajuste óptimo de indicadores, datos y otras herramientas para detectar señales.
correlations: Valores ajustables

caso B: crear nueva api del indicador:
exp.1: Analiza la lógica de la estrategia, confirma correlación con indicador sugerido.
exp.2: Define ajustes de indicador para detectar señales basados en la estrategia
exp.3: Busca correlaciones con indicadores existentes, para evitar redundancias o encontrar sinergias
exp.4: Crea un archivo de configuración YAML con:
name: Nombre de la api
indicator: Indicadores utilizados
inputs: Datos requeridos para identificar las señales
conditions: Ajuste óptimo de indicadores, datos y otras herramientas para detectar señales
correlación: valores ajustables
"""

        # Enviar a la API de Hugging Face
        xai_api_url = "https://api-inference.huggingface.co/models/gpt2-large"  
        headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}"}
        
        try:
            # Primer intento con gpt2-large
            response = requests.post(xai_api_url, headers=headers, json={
                "inputs": combined_text,
                "parameters": {
                    "max_length": 1000,
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "do_sample": True,
                    "return_full_text": False
                }
            }, timeout=60)
            
            if response.status_code == 200:
                response_data = response.json()
                if isinstance(response_data, list) and len(response_data) > 0:
                    generated_text = response_data[0].get('generated_text', '')
                    return {"status": "success", "response": generated_text}
                else:
                    print(f"Respuesta inesperada: {response_data}")
                    raise HTTPException(status_code=500, detail="Formato de respuesta inválido")
            else:
                # Si falla, intentar con un modelo más pequeño
                xai_api_url_backup = "https://api-inference.huggingface.co/models/gpt2"
                response = requests.post(xai_api_url_backup, headers=headers, json={
                    "inputs": combined_text,
                    "parameters": {
                        "max_length": 1000,
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "do_sample": True,
                        "return_full_text": False
                    }
                }, timeout=60)
                
                if response.status_code == 200:
                    response_data = response.json()
                    if isinstance(response_data, list) and len(response_data) > 0:
                        generated_text = response_data[0].get('generated_text', '')
                        return {"status": "success", "response": generated_text}
                
                error_msg = f"Error en la API de Hugging Face (Status {response.status_code})"
                if response.text:
                    try:
                        error_detail = response.json()
                        error_msg += f": {error_detail.get('error', response.text)}"
                    except:
                        error_msg += f": {response.text}"
                print(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)
                
        except requests.Timeout:
            error_msg = "La API está tardando demasiado en responder. Por favor, inténtalo de nuevo en unos momentos."
            print(error_msg)
            raise HTTPException(status_code=503, detail=error_msg)
        except requests.RequestException as e:
            error_msg = f"Error de conexión con la API: {str(e)}"
            print(error_msg)
            raise HTTPException(status_code=503, detail=error_msg)
            
    except Exception as e:
        print(f"Error general: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))