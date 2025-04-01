# freak_stage.py
# Coordina el flujo y evoluciona el sistema

import os
import yaml
import logging
from datetime import datetime
import sys

# Agregar directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Importar módulos necesarios
from actions.evolve.freak_optimizer import FreakOptimizer
from actions.evolve.freak_incubator import FreakIncubator
from actions.evolve.freak_evolver import FreakEvolver
from actions.evolve.version_manager import VersionManager
from actions.evolve.config_loader import ConfigLoader

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("freak_stage.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FreakStage:
    """
    Clase principal que coordina el flujo de evolución del sistema.
    Gestiona la comunicación entre los diferentes componentes y
    supervisa el proceso de evolución de las estrategias.
    """
    
    def __init__(self, config_path=None):
        """
        Inicializa el coordinador de freaks con la configuración especificada.
        
        Args:
            config_path (str): Ruta al archivo de configuración YAML (opcional)
        """
        # Inicializar componentes
        self.config_loader = ConfigLoader(config_path)
        self.version_manager = VersionManager()
        self.optimizer = FreakOptimizer()
        self.incubator = FreakIncubator()
        self.evolver = FreakEvolver()
        
        # Cargar configuración
        self.config = self.config_loader.get_all()
        
        logger.info("FreakStage inicializado con configuración cargada")
    
    def coordinate_evolution(self, strategy_id):
        """
        Coordina el proceso de evolución para una estrategia específica.
        
        Args:
            strategy_id (str): ID de la estrategia a evolucionar
            
        Returns:
            dict: Resultado del proceso de evolución
        """
        logger.info("Iniciando proceso de evolución para estrategia %s", strategy_id)
        
        try:
            # 1. Obtener estrategia actual
            strategy_yaml = self._get_strategy_yaml(strategy_id)
            if not strategy_yaml:
                return {"status": "error", "message": "Estrategia no encontrada"}
            
            # 2. Guardar versión actual
            version_id = self.version_manager.save_version(
                "strategy", 
                strategy_id, 
                strategy_yaml, 
                {"stage": "pre_evolution"}
            )
            logger.info("Guardada versión %s antes de evolución", version_id)
            
            # 3. Monitorear rendimiento para decidir el tipo de evolución
            performance_metrics = self.monitor_performance(strategy_id)
            
            # 4. Determinar el tipo de evolución necesaria
            evolution_type = self._determine_evolution_type(performance_metrics)
            logger.info("Tipo de evolución determinado: %s", evolution_type)
            
            # 5. Ejecutar el tipo de evolución apropiado
            evolved_strategy = None
            
            if evolution_type == "optimization":
                # Optimización rápida de parámetros
                evolved_strategy = self.optimizer.optimize_strategy(
                    strategy_yaml, 
                    optimization_level=self.config.get("evolution", {}).get("optimization_levels", 2)
                )
                
            elif evolution_type == "incubation":
                # Incubación de nuevas ideas
                evolved_strategy = self.incubator.generate_strategy_proposal(
                    market_type=self._extract_market_type(strategy_yaml),
                    timeframe=self._extract_timeframe(strategy_yaml)
                )
                
            elif evolution_type == "evolution":
                # Evolución genética completa
                evolved_strategy = self.evolver.evolve_strategy(
                    strategy_yaml,
                    generations=self.config.get("evolution", {}).get("generations", 5)
                )
            
            # 6. Guardar la estrategia evolucionada
            if evolved_strategy:
                # Guardar nueva versión
                new_version_id = self.version_manager.save_version(
                    "strategy", 
                    strategy_id, 
                    evolved_strategy, 
                    {"stage": "post_evolution", "type": evolution_type}
                )
                
                # Aplicar la estrategia evolucionada
                self.apply_updates(strategy_id, evolved_strategy)
                
                logger.info("Evolución completada. Nueva versión: %s", new_version_id)
                
                return {
                    "status": "success", 
                    "message": "Evolución completada",
                    "evolution_type": evolution_type,
                    "version_id": new_version_id
                }
            else:
                logger.warning("No se pudo evolucionar la estrategia")
                return {"status": "warning", "message": "No se pudo evolucionar la estrategia"}
                
        except Exception as e:
            logger.error("Error durante la evolución: %s", str(e))
            return {"status": "error", "message": str(e)}
    
    def _get_strategy_yaml(self, strategy_id):
        """
        Obtiene el YAML de una estrategia desde la base de datos.
        
        Args:
            strategy_id (str): ID de la estrategia
            
        Returns:
            str: Contenido YAML de la estrategia o None si no se encuentra
        """
        # Aquí iría la lógica para obtener la estrategia desde la base de datos
        # Por ahora, devolvemos un ejemplo
        
        # En una implementación real, se consultaría la base de datos
        return """
        name: Example Strategy
        description: Esta es una estrategia de ejemplo
        market_type: crypto
        timeframe: 1h
        indicators:
          - RSI
          - MACD
        parameters:
          rsi_period: 14
          macd_fast: 12
          macd_slow: 26
        entry_conditions:
          - RSI < 30
          - MACD < 0
        exit_conditions:
          - RSI > 70
          - MACD > 0
        risk_management:
          stop_loss: 2%
          take_profit: 5%
        """
    
    def _extract_market_type(self, strategy_yaml):
        """
        Extrae el tipo de mercado de una estrategia.
        
        Args:
            strategy_yaml (str): Contenido YAML de la estrategia
            
        Returns:
            str: Tipo de mercado o 'crypto' por defecto
        """
        try:
            strategy = yaml.safe_load(strategy_yaml)
            return strategy.get("market_type", "crypto")
        except:
            return "crypto"
    
    def _extract_timeframe(self, strategy_yaml):
        """
        Extrae el timeframe de una estrategia.
        
        Args:
            strategy_yaml (str): Contenido YAML de la estrategia
            
        Returns:
            str: Timeframe o '1h' por defecto
        """
        try:
            strategy = yaml.safe_load(strategy_yaml)
            return strategy.get("timeframe", "1h")
        except:
            return "1h"
    
    def _determine_evolution_type(self, performance_metrics):
        """
        Determina el tipo de evolución necesaria basado en métricas de rendimiento.
        
        Args:
            performance_metrics (dict): Métricas de rendimiento
            
        Returns:
            str: Tipo de evolución ('optimization', 'incubation', 'evolution')
        """
        # Lógica para determinar el tipo de evolución
        
        # Si el rendimiento es bueno pero podría mejorar, optimizar
        if performance_metrics.get("profit_factor", 0) > 1.2:
            return "optimization"
        
        # Si el rendimiento es malo, incubar nueva estrategia
        if performance_metrics.get("profit_factor", 0) < 0.8:
            return "incubation"
        
        # En otros casos, evolución completa
        return "evolution"
    
    def monitor_performance(self, strategy_id):
        """
        Monitorea el rendimiento de una estrategia para determinar
        si necesita evolucionar.
        
        Args:
            strategy_id (str): ID de la estrategia a monitorear
            
        Returns:
            dict: Métricas de rendimiento
        """
        logger.info("Monitoreando rendimiento de estrategia %s", strategy_id)
        
        # Aquí iría la lógica de monitoreo de rendimiento
        # Por ahora, devolvemos métricas de ejemplo
        
        return {
            "profit_factor": 1.1,
            "win_rate": 0.52,
            "drawdown": 8.5,
            "sharpe_ratio": 1.3,
            "trades": 120,
            "duration_days": 30
        }
    
    def apply_updates(self, strategy_id, strategy_yaml):
        """
        Aplica actualizaciones a una estrategia existente.
        
        Args:
            strategy_id (str): ID de la estrategia a actualizar
            strategy_yaml (str): Nuevo contenido YAML de la estrategia
            
        Returns:
            bool: True si se aplicaron correctamente, False en caso contrario
        """
        logger.info("Aplicando actualizaciones a estrategia %s", strategy_id)
        
        try:
            # Aquí iría la lógica para aplicar las actualizaciones
            # Por ejemplo, guardar en la base de datos
            
            # Simular éxito
            return True
            
        except Exception as e:
            logger.error("Error al aplicar actualizaciones: %s", str(e))
            return False
    
    def rollback_to_version(self, strategy_id, version_id):
        """
        Revierte una estrategia a una versión anterior.
        
        Args:
            strategy_id (str): ID de la estrategia
            version_id (str): ID de la versión a la que revertir
            
        Returns:
            bool: True si se revirtió correctamente, False en caso contrario
        """
        logger.info("Revirtiendo estrategia %s a versión %s", strategy_id, version_id)
        
        try:
            # Usar el gestor de versiones para hacer rollback
            rollback_success = self.version_manager.rollback(
                "strategy", strategy_id, version_id
            )
            
            if rollback_success:
                # Obtener la versión restaurada
                content, _ = self.version_manager.get_version(
                    "strategy", strategy_id
                )
                
                # Aplicar la versión restaurada
                if content:
                    self.apply_updates(strategy_id, content)
                    logger.info("Rollback completado con éxito")
                    return True
            
            logger.warning("No se pudo completar el rollback")
            return False
            
        except Exception as e:
            logger.error("Error durante rollback: %s", str(e))
            return False
    
    def schedule_evolution(self, strategy_ids=None, schedule_time=None):
        """
        Programa la evolución de una o varias estrategias.
        
        Args:
            strategy_ids (list): Lista de IDs de estrategias (None = todas)
            schedule_time (datetime): Momento programado (None = inmediato)
            
        Returns:
            dict: Resultado de la programación
        """
        if strategy_ids is None:
            # Obtener todas las estrategias activas
            strategy_ids = self._get_active_strategy_ids()
        
        if schedule_time is None:
            schedule_time = datetime.now()
        
        logger.info("Programando evolución para %d estrategias a las %s", 
                   len(strategy_ids), schedule_time.strftime("%Y-%m-%d %H:%M:%S"))
        
        # Aquí iría la lógica para programar la evolución
        # Por ejemplo, crear tareas en un sistema de colas
        
        return {
            "status": "success",
            "scheduled_strategies": len(strategy_ids),
            "schedule_time": schedule_time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _get_active_strategy_ids(self):
        """
        Obtiene los IDs de todas las estrategias activas.
        
        Returns:
            list: Lista de IDs de estrategias
        """
        # Aquí iría la lógica para obtener las estrategias activas
        # Por ahora, devolvemos ejemplos
        return ["strategy_001", "strategy_002", "strategy_003"]

# Función principal para ejecutar desde línea de comandos
def main():
    """Punto de entrada principal para ejecución desde línea de comandos"""
    stage = FreakStage()
    
    # Ejemplo de uso
    print("Iniciando coordinación de evolución...")
    result = stage.coordinate_evolution("example_strategy_123")
    print(f"Resultado: {result}")
    
    # Ejemplo de programación
    print("\nProgramando evolución para todas las estrategias...")
    schedule_result = stage.schedule_evolution()
    print(f"Resultado de programación: {schedule_result}")

if __name__ == "__main__":
    main()
