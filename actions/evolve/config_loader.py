# config_loader.py
# Carga configuraciones desde config.yaml

import os
import yaml
import logging
import json
from datetime import datetime
from dotenv import load_dotenv

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("config_loader.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ConfigLoader:
    """
    Clase para cargar y gestionar configuraciones desde archivos YAML.
    Proporciona funcionalidades para cargar, validar y acceder a configuraciones
    de manera estructurada y segura.
    """
    
    def __init__(self, config_path=None, env_file=None):
        """
        Inicializa el cargador de configuraciones.
        
        Args:
            config_path (str): Ruta al archivo de configuración principal (opcional)
            env_file (str): Ruta al archivo .env para variables de entorno (opcional)
        """
        # Cargar variables de entorno si se especifica
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()  # Cargar .env por defecto
        
        # Configurar ruta de configuración
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), '..', '..', 'config.yaml'
        )
        
        # Inicializar configuración
        self.config = {}
        self.last_loaded = None
        
        # Cargar configuración inicial
        self.reload()
        
        logger.info("ConfigLoader inicializado con archivo %s", self.config_path)
    
    def reload(self):
        """
        Recarga la configuración desde el archivo.
        
        Returns:
            bool: True si se cargó correctamente, False en caso contrario
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as file:
                    self.config = yaml.safe_load(file) or {}
                self.last_loaded = datetime.now()
                logger.info("Configuración recargada correctamente")
                return True
            else:
                logger.warning("Archivo de configuración no encontrado: %s", self.config_path)
                return False
        except Exception as e:
            logger.error("Error al cargar la configuración: %s", str(e))
            return False
    
    def get(self, key, default=None):
        """
        Obtiene un valor de configuración por su clave.
        Soporta notación de punto para acceder a valores anidados.
        
        Args:
            key (str): Clave de configuración (ej: "database.host")
            default: Valor por defecto si la clave no existe
            
        Returns:
            Valor de configuración o el valor por defecto
        """
        # Si la clave contiene puntos, navegar por la estructura anidada
        if '.' in key:
            parts = key.split('.')
            current = self.config
            
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            
            return current
        
        # Clave simple
        return self.config.get(key, default)
    
    def get_all(self):
        """
        Obtiene toda la configuración.
        
        Returns:
            dict: Configuración completa
        """
        return self.config.copy()
    
    def validate_required(self, required_keys):
        """
        Valida que todas las claves requeridas existan en la configuración.
        
        Args:
            required_keys (list): Lista de claves requeridas
            
        Returns:
            tuple: (bool, list) - (válido, lista de claves faltantes)
        """
        missing = []
        
        for key in required_keys:
            if self.get(key) is None:
                missing.append(key)
        
        return len(missing) == 0, missing
    
    def get_section(self, section_name):
        """
        Obtiene una sección completa de la configuración.
        
        Args:
            section_name (str): Nombre de la sección
            
        Returns:
            dict: Sección de configuración o diccionario vacío si no existe
        """
        section = self.get(section_name, {})
        return section if isinstance(section, dict) else {}
    
    def get_database_config(self):
        """
        Obtiene la configuración de base de datos con valores por defecto seguros.
        
        Returns:
            dict: Configuración de base de datos
        """
        db_config = self.get_section("database")
        
        # Aplicar valores por defecto
        defaults = {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "",
            "database": "aia4you",
            "charset": "utf8mb4"
        }
        
        # Combinar con valores por defecto
        for key, value in defaults.items():
            if key not in db_config:
                db_config[key] = value
        
        # Sobrescribir con variables de entorno si existen
        env_mapping = {
            "host": "DB_HOST",
            "port": "DB_PORT",
            "user": "DB_USER",
            "password": "DB_PASSWORD",
            "database": "DB_NAME"
        }
        
        for config_key, env_var in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convertir a entero si es necesario
                if config_key == "port" and env_value.isdigit():
                    db_config[config_key] = int(env_value)
                else:
                    db_config[config_key] = env_value
        
        return db_config
    
    def get_api_config(self):
        """
        Obtiene la configuración de APIs con valores por defecto.
        
        Returns:
            dict: Configuración de APIs
        """
        api_config = self.get_section("apis")
        
        # Aplicar valores por defecto
        defaults = {
            "strategy_generator": {
                "host": "localhost",
                "port": 8505
            },
            "indicator_generator": {
                "host": "localhost",
                "port": 8506
            }
        }
        
        # Combinar con valores por defecto
        for service, service_defaults in defaults.items():
            if service not in api_config:
                api_config[service] = {}
            
            for key, value in service_defaults.items():
                if key not in api_config[service]:
                    api_config[service][key] = value
        
        # Sobrescribir con variables de entorno si existen
        if os.getenv("STRATEGY_API_PORT"):
            api_config["strategy_generator"]["port"] = int(os.getenv("STRATEGY_API_PORT"))
        
        if os.getenv("INDICATOR_API_PORT"):
            api_config["indicator_generator"]["port"] = int(os.getenv("INDICATOR_API_PORT"))
        
        return api_config
    
    def get_evolution_config(self):
        """
        Obtiene la configuración específica para el módulo de evolución.
        
        Returns:
            dict: Configuración de evolución
        """
        evolution_config = self.get_section("evolution")
        
        # Aplicar valores por defecto
        defaults = {
            "optimization_levels": 3,
            "incubation_cycles": 5,
            "version_control": True,
            "auto_rollback_threshold": 0.8,
            "performance_metrics": ["profit", "drawdown", "win_rate", "sharpe_ratio"]
        }
        
        # Combinar con valores por defecto
        for key, value in defaults.items():
            if key not in evolution_config:
                evolution_config[key] = value
        
        return evolution_config
    
    def save_config(self, config_data, backup=True):
        """
        Guarda la configuración en el archivo.
        
        Args:
            config_data (dict): Datos de configuración a guardar
            backup (bool): Si es True, crea una copia de seguridad antes de guardar
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        try:
            # Crear copia de seguridad si se solicita
            if backup and os.path.exists(self.config_path):
                backup_path = f"{self.config_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                shutil.copy2(self.config_path, backup_path)
                logger.info("Creada copia de seguridad en %s", backup_path)
            
            # Guardar nueva configuración
            with open(self.config_path, 'w') as file:
                yaml.dump(config_data, file, default_flow_style=False)
            
            # Actualizar configuración en memoria
            self.config = config_data
            self.last_loaded = datetime.now()
            
            logger.info("Configuración guardada correctamente")
            return True
        
        except Exception as e:
            logger.error("Error al guardar la configuración: %s", str(e))
            return False
    
    def update_config(self, updates, create_if_missing=True):
        """
        Actualiza la configuración con los valores proporcionados.
        
        Args:
            updates (dict): Actualizaciones a aplicar
            create_if_missing (bool): Si es True, crea el archivo si no existe
            
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario
        """
        # Si el archivo no existe y no se debe crear, salir
        if not os.path.exists(self.config_path) and not create_if_missing:
            logger.warning("Archivo de configuración no existe y no se creará")
            return False
        
        # Cargar configuración actual o crear nueva
        current_config = self.config.copy()
        
        # Aplicar actualizaciones recursivamente
        self._update_dict_recursive(current_config, updates)
        
        # Guardar configuración actualizada
        return self.save_config(current_config)
    
    def _update_dict_recursive(self, target, updates):
        """
        Actualiza un diccionario de manera recursiva.
        
        Args:
            target (dict): Diccionario a actualizar
            updates (dict): Actualizaciones a aplicar
        """
        for key, value in updates.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                # Actualizar recursivamente si ambos son diccionarios
                self._update_dict_recursive(target[key], value)
            else:
                # Sobrescribir o añadir valor
                target[key] = value

# Función principal para ejecutar desde línea de comandos
def main():
    """Punto de entrada principal para ejecución desde línea de comandos"""
    import shutil
    
    # Crear un archivo de configuración de ejemplo si no existe
    example_config = {
        "database": {
            "host": "localhost",
            "port": 3306,
            "user": "aia4you_user",
            "password": "password123",
            "database": "aia4you"
        },
        "apis": {
            "strategy_generator": {
                "host": "localhost",
                "port": 8505
            },
            "indicator_generator": {
                "host": "localhost",
                "port": 8506
            }
        },
        "evolution": {
            "optimization_levels": 3,
            "incubation_cycles": 5,
            "version_control": True,
            "auto_rollback_threshold": 0.8,
            "performance_metrics": ["profit", "drawdown", "win_rate", "sharpe_ratio"]
        },
        "logging": {
            "level": "INFO",
            "file": "evolution.log"
        }
    }
    
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml')
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    # Escribir configuración de ejemplo si no existe
    if not os.path.exists(config_path):
        with open(config_path, 'w') as file:
            yaml.dump(example_config, file, default_flow_style=False)
        print(f"Creado archivo de configuración de ejemplo en {config_path}")
    
    # Usar el cargador de configuraciones
    config_loader = ConfigLoader(config_path)
    
    # Mostrar configuración cargada
    print("\nConfiguración cargada:")
    print(f"Base de datos: {config_loader.get_database_config()}")
    print(f"APIs: {config_loader.get_api_config()}")
    print(f"Evolución: {config_loader.get_evolution_config()}")
    
    # Validar configuración
    required_keys = ["database.host", "database.user", "apis.strategy_generator.port"]
    valid, missing = config_loader.validate_required(required_keys)
    
    print(f"\nValidación de configuración: {'Válida' if valid else 'Inválida'}")
    if not valid:
        print(f"Claves faltantes: {missing}")
    
    # Ejemplo de actualización
    updates = {
        "evolution": {
            "new_feature": True,
            "optimization_levels": 4
        }
    }
    
    if config_loader.update_config(updates):
        print("\nConfiguración actualizada correctamente")
        print(f"Evolución (actualizada): {config_loader.get_evolution_config()}")

if __name__ == "__main__":
    main()
