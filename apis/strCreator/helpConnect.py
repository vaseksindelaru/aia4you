from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
import requests
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import yaml

# Cargar variables de entorno
load_dotenv()

# Configuración básica de FastAPI
app = FastAPI()

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo para el prompt
class Prompt(BaseModel):
    prompt: str

# Configuración de la base de datos MySQL desde variables de entorno
db_config = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "21blackjack"),
    "database": os.getenv("MYSQL_DATABASE", "sql1")
}

@app.get("/")
def read_root():
    return {"message": "API is running"}

@app.post("/help_connect")
async def process_prompt(payload: Prompt):
    try:
        print("\n" + "="*50)
        print("INICIANDO PROCESO DE PROMPT")
        print("="*50)
        print(f"Prompt recibido: {payload.prompt}")
        
        # Obtener indicadores de la base de datos
        indicators = []
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT config_yaml FROM apis_db WHERE config_yaml IS NOT NULL")
            results = cursor.fetchall()
            
            # Procesar cada configuración YAML para extraer indicadores
            for row in results:
                if row['config_yaml']:
                    try:
                        config = yaml.safe_load(row['config_yaml'])
                        if config and 'indicators' in config:
                            # Asegurarse de que los indicadores son una lista
                            if isinstance(config['indicators'], list):
                                indicators.extend(config['indicators'])
                            elif isinstance(config['indicators'], str):
                                indicators.append(config['indicators'])
                    except yaml.YAMLError as e:
                        print(f"Error al parsear YAML: {e}")
                        continue
            
            # Eliminar duplicados y None
            indicators = list(set(filter(None, indicators)))
            print("\nIndicadores disponibles:", indicators)
            
        except Exception as e:
            print(f"Error al conectar a la base de datos: {e}")
            return {"status": "error", "response": f"Error al conectar a la base de datos: {str(e)}"}
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

        # Construir el texto combinado
        print("\nConstruyendo prompt para la API...")
        combined_text = f"""
Actúa como un experto en trading que recomienda indicadores técnicos. Analiza el prompt y genera un YAML con indicadores e inputs recomendados.

# Ejemplo de análisis (Chain of Thought + One-Shot):
Prompt de ejemplo: "Quiero una estrategia que detecte cambios de tendencia usando el precio y volumen"

Pensamiento paso a paso:
1. Para detectar cambios de tendencia necesitamos:
   - Indicadores de tendencia (ej: Moving Averages)
   - Indicadores de momentum (ej: RSI)
   - Confirmación por volumen

2. Comparando con indicadores disponibles:
   Disponibles: {indicators}
   Necesarios pero no disponibles: ninguno

3. Generando YAML:
indicators:
  - ma     # Para identificar la tendencia
  - rsi    # Para confirmar cambios
  - volume # Para validar la fuerza del movimiento
inputs:
  - price_close  # Para MA y RSI
  - volume_data  # Para análisis de volumen

# Tu tarea:
Analiza este prompt y genera un YAML similar:
{payload.prompt}

# Indicadores disponibles en la base de datos:
{', '.join(indicators)}

Genera SOLO el archivo YAML con indicators e inputs, siguiendo el ejemplo anterior."""

        print("\nEnviando solicitud a la API de Hugging Face...")
        print("-"*50)
        print("PROMPT ENVIADO:")
        print(combined_text)
        print("-"*50)
        
        try:
            api_key = os.getenv('HUGGINGFACE_API_KEY')
            if not api_key:
                error_msg = "API key no encontrada"
                print(f"Error: {error_msg}")
                return {"status": "error", "response": error_msg}
                
            response = requests.post(
                "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "inputs": combined_text,
                    "parameters": {
                        "max_new_tokens": 500,
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "return_full_text": False
                    }
                },
                timeout=180
            )
            
            print("\nRespuesta recibida!")
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Contenido: {response.text}")
            
            if response.status_code == 503:
                error_msg = "El servicio de Hugging Face está temporalmente no disponible. Por favor, intenta de nuevo en unos minutos."
                print(f"Error: {error_msg}")
                return {"status": "error", "response": error_msg}
                
            if response.status_code == 200:
                response_data = response.json()
                if isinstance(response_data, list) and len(response_data) > 0:
                    generated_text = response_data[0].get('generated_text', '')
                    print("\n" + "="*50)
                    print("RESPUESTA FINAL:")
                    print("="*50)
                    print(generated_text)
                    print("="*50 + "\n")
                    return {"status": "success", "response": generated_text}
                else:
                    error_msg = "Formato de respuesta inesperado"
                    print(f"Error: {error_msg}")
                    return {"status": "error", "response": error_msg}
            else:
                error_msg = f"Error en la API (Status {response.status_code}): {response.text}"
                print(f"Error: {error_msg}")
                return {"status": "error", "response": error_msg}
                
        except requests.exceptions.Timeout:
            error_msg = "Timeout en la API"
            print(f"Error: {error_msg}")
            return {"status": "error", "response": error_msg}
        except Exception as e:
            error_msg = f"Error al procesar la respuesta: {str(e)}"
            print(f"Error: {error_msg}")
            return {"status": "error", "response": error_msg}
            
    except Exception as e:
        error_msg = f"Error general: {str(e)}"
        print(f"Error: {error_msg}")
        return {"status": "error", "response": error_msg}