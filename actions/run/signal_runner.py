from actions.evolve.freak_stage import FreakStage
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("signal_runner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SignalRunner:
    """
    Clase que ejecuta el proceso de generación de señales de trading
    utilizando el FreakStage para la detección y evaluación de rebotes.
    """
    
    def __init__(self):
        """
        Inicializa el runner de señales con una instancia de FreakStage.
        """
        logger.info("Inicializando SignalRunner")
        self.freak_stage = FreakStage()
    
    def run(self):
        """
        Ejecuta el proceso de generación de señales y retorna la acción recomendada.
        
        Returns:
            str: Acción recomendada ('buy', 'sell', o 'hold')
        """
        logger.info("Ejecutando proceso de generación de señales")
        
        try:
            # Obtener acción del FreakStage
            action = self.freak_stage.decide()
            
            logger.info(f"Acción generada: {action}")
            print(f"Ejecutando acción: {action}")
            return action
            
        except Exception as e:
            logger.error(f"Error al generar señal: {str(e)}")
            return "hold"  # Por defecto, mantener posición en caso de error