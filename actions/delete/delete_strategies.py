import mysql.connector
import os
from dotenv import load_dotenv
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

def delete_all_strategies():
    """
    Elimina todas las estrategias de la base de datos.
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
        
        # Consultar cuántas estrategias hay antes de eliminar
        cursor.execute("SELECT COUNT(*) FROM strategies")
        count_before = cursor.fetchone()[0]
        logger.info(f"Número de estrategias antes de eliminar: {count_before}")
        
        # Eliminar todas las estrategias
        cursor.execute("DELETE FROM strategies")
        connection.commit()
        
        # Verificar que se hayan eliminado todas las estrategias
        cursor.execute("SELECT COUNT(*) FROM strategies")
        count_after = cursor.fetchone()[0]
        logger.info(f"Número de estrategias después de eliminar: {count_after}")
        
        logger.info(f"Se eliminaron {count_before - count_after} estrategias")
        return True
    except Exception as e:
        logger.error(f"ERROR AL ELIMINAR ESTRATEGIAS: {e}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    logger.info("="*50)
    logger.info("ELIMINANDO TODAS LAS ESTRATEGIAS")
    logger.info("="*50)
    
    result = delete_all_strategies()
    
    if result:
        logger.info("TODAS LAS ESTRATEGIAS ELIMINADAS EXITOSAMENTE")
    else:
        logger.error("ERROR AL ELIMINAR ESTRATEGIAS")
