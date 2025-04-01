# version_manager.py
# Maneja el versionado y retroceso

import os
import yaml
import logging
import json
import shutil
from datetime import datetime
import uuid

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("version_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VersionManager:
    """
    Clase para gestionar el versionado y retroceso de estrategias y configuraciones.
    Permite mantener un historial de cambios y volver a versiones anteriores si es necesario.
    """
    
    def __init__(self, storage_dir=None):
        """
        Inicializa el gestor de versiones con un directorio de almacenamiento.
        
        Args:
            storage_dir (str): Directorio para almacenar las versiones (opcional)
        """
        self.storage_dir = storage_dir or os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'versions')
        self._ensure_storage_dir()
        logger.info("VersionManager inicializado con almacenamiento en %s", self.storage_dir)
    
    def _ensure_storage_dir(self):
        """Asegura que el directorio de almacenamiento existe"""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
            logger.info("Creado directorio de almacenamiento %s", self.storage_dir)
    
    def save_version(self, entity_type, entity_id, content, metadata=None):
        """
        Guarda una nueva versión de una entidad.
        
        Args:
            entity_type (str): Tipo de entidad (strategy, indicator, config)
            entity_id (str): ID de la entidad
            content (str): Contenido a versionar (YAML, JSON, etc.)
            metadata (dict): Metadatos adicionales (opcional)
            
        Returns:
            str: ID de la versión creada
        """
        # Crear directorio para la entidad si no existe
        entity_dir = os.path.join(self.storage_dir, entity_type, entity_id)
        if not os.path.exists(entity_dir):
            os.makedirs(entity_dir)
        
        # Generar ID de versión y timestamp
        version_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Preparar metadatos
        version_metadata = {
            "version_id": version_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "created_at": timestamp,
            "user_metadata": metadata or {}
        }
        
        # Guardar contenido y metadatos
        content_path = os.path.join(entity_dir, f"{version_id}.content")
        metadata_path = os.path.join(entity_dir, f"{version_id}.metadata")
        
        with open(content_path, 'w') as f:
            f.write(content)
        
        with open(metadata_path, 'w') as f:
            json.dump(version_metadata, f, indent=2)
        
        # Actualizar índice de versiones
        self._update_version_index(entity_type, entity_id, version_id, timestamp)
        
        logger.info("Guardada versión %s para %s:%s", version_id, entity_type, entity_id)
        return version_id
    
    def _update_version_index(self, entity_type, entity_id, version_id, timestamp):
        """
        Actualiza el índice de versiones para una entidad.
        
        Args:
            entity_type (str): Tipo de entidad
            entity_id (str): ID de la entidad
            version_id (str): ID de la versión
            timestamp (str): Timestamp de creación
        """
        index_path = os.path.join(self.storage_dir, entity_type, entity_id, "index.json")
        
        # Cargar índice existente o crear uno nuevo
        if os.path.exists(index_path):
            with open(index_path, 'r') as f:
                index = json.load(f)
        else:
            index = {"versions": []}
        
        # Añadir nueva versión al índice
        index["versions"].append({
            "version_id": version_id,
            "timestamp": timestamp,
            "active": True  # La última versión es la activa
        })
        
        # Marcar versiones anteriores como inactivas
        for v in index["versions"][:-1]:
            v["active"] = False
        
        # Guardar índice actualizado
        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2)
    
    def get_version(self, entity_type, entity_id, version_id=None):
        """
        Obtiene una versión específica o la última versión si no se especifica.
        
        Args:
            entity_type (str): Tipo de entidad
            entity_id (str): ID de la entidad
            version_id (str): ID de la versión (opcional, última por defecto)
            
        Returns:
            tuple: (contenido, metadatos) o (None, None) si no existe
        """
        # Si no se especifica versión, obtener la última
        if version_id is None:
            version_id = self.get_latest_version_id(entity_type, entity_id)
            if version_id is None:
                logger.warning("No hay versiones para %s:%s", entity_type, entity_id)
                return None, None
        
        # Construir rutas
        entity_dir = os.path.join(self.storage_dir, entity_type, entity_id)
        content_path = os.path.join(entity_dir, f"{version_id}.content")
        metadata_path = os.path.join(entity_dir, f"{version_id}.metadata")
        
        # Verificar que existan los archivos
        if not os.path.exists(content_path) or not os.path.exists(metadata_path):
            logger.warning("Versión %s no encontrada para %s:%s", version_id, entity_type, entity_id)
            return None, None
        
        # Cargar contenido y metadatos
        with open(content_path, 'r') as f:
            content = f.read()
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        logger.info("Obtenida versión %s para %s:%s", version_id, entity_type, entity_id)
        return content, metadata
    
    def get_latest_version_id(self, entity_type, entity_id):
        """
        Obtiene el ID de la última versión de una entidad.
        
        Args:
            entity_type (str): Tipo de entidad
            entity_id (str): ID de la entidad
            
        Returns:
            str: ID de la última versión o None si no hay versiones
        """
        index_path = os.path.join(self.storage_dir, entity_type, entity_id, "index.json")
        
        if not os.path.exists(index_path):
            return None
        
        with open(index_path, 'r') as f:
            index = json.load(f)
        
        if not index["versions"]:
            return None
        
        return index["versions"][-1]["version_id"]
    
    def rollback(self, entity_type, entity_id, version_id):
        """
        Retrocede a una versión anterior.
        
        Args:
            entity_type (str): Tipo de entidad
            entity_id (str): ID de la entidad
            version_id (str): ID de la versión a la que retroceder
            
        Returns:
            bool: True si se realizó el rollback, False en caso contrario
        """
        # Obtener contenido y metadatos de la versión
        content, metadata = self.get_version(entity_type, entity_id, version_id)
        
        if content is None or metadata is None:
            logger.error("No se puede hacer rollback a versión inexistente %s", version_id)
            return False
        
        # Guardar como nueva versión con referencia a la original
        rollback_metadata = {
            "rollback_from": version_id,
            "rollback_timestamp": datetime.now().isoformat(),
            "original_metadata": metadata.get("user_metadata", {})
        }
        
        new_version_id = self.save_version(entity_type, entity_id, content, rollback_metadata)
        
        logger.info("Rollback realizado de %s:%s a versión %s, creada nueva versión %s", 
                   entity_type, entity_id, version_id, new_version_id)
        
        return True
    
    def list_versions(self, entity_type, entity_id):
        """
        Lista todas las versiones disponibles para una entidad.
        
        Args:
            entity_type (str): Tipo de entidad
            entity_id (str): ID de la entidad
            
        Returns:
            list: Lista de versiones con sus metadatos
        """
        index_path = os.path.join(self.storage_dir, entity_type, entity_id, "index.json")
        
        if not os.path.exists(index_path):
            logger.warning("No hay versiones para %s:%s", entity_type, entity_id)
            return []
        
        with open(index_path, 'r') as f:
            index = json.load(f)
        
        logger.info("Listadas %d versiones para %s:%s", 
                   len(index["versions"]), entity_type, entity_id)
        
        return index["versions"]
    
    def compare_versions(self, entity_type, entity_id, version_id1, version_id2):
        """
        Compara dos versiones de una entidad.
        
        Args:
            entity_type (str): Tipo de entidad
            entity_id (str): ID de la entidad
            version_id1 (str): ID de la primera versión
            version_id2 (str): ID de la segunda versión
            
        Returns:
            dict: Diferencias entre las versiones
        """
        # Obtener contenidos
        content1, _ = self.get_version(entity_type, entity_id, version_id1)
        content2, _ = self.get_version(entity_type, entity_id, version_id2)
        
        if content1 is None or content2 is None:
            logger.error("No se pueden comparar versiones inexistentes")
            return {"error": "Una o ambas versiones no existen"}
        
        # Implementación simple de comparación
        # En una implementación real, se usaría una biblioteca de diff más sofisticada
        
        # Convertir a diccionarios si son YAML/JSON
        try:
            dict1 = yaml.safe_load(content1)
            dict2 = yaml.safe_load(content2)
            
            # Comparar diccionarios
            differences = self._compare_dicts(dict1, dict2)
            return differences
        except:
            # Si no son YAML/JSON válidos, comparar como texto
            return {
                "text_comparison": "Implementación de comparación de texto no disponible en esta versión"
            }
    
    def _compare_dicts(self, dict1, dict2, path=""):
        """
        Compara recursivamente dos diccionarios.
        
        Args:
            dict1 (dict): Primer diccionario
            dict2 (dict): Segundo diccionario
            path (str): Ruta actual en la comparación
            
        Returns:
            dict: Diferencias encontradas
        """
        differences = {}
        
        # Comparar claves en dict1
        for key in dict1:
            current_path = f"{path}.{key}" if path else key
            
            if key not in dict2:
                differences[current_path] = {"type": "removed", "value": dict1[key]}
            elif isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                nested_diff = self._compare_dicts(dict1[key], dict2[key], current_path)
                if nested_diff:
                    differences.update(nested_diff)
            elif dict1[key] != dict2[key]:
                differences[current_path] = {
                    "type": "changed",
                    "old_value": dict1[key],
                    "new_value": dict2[key]
                }
        
        # Buscar claves añadidas en dict2
        for key in dict2:
            current_path = f"{path}.{key}" if path else key
            if key not in dict1:
                differences[current_path] = {"type": "added", "value": dict2[key]}
        
        return differences

# Función principal para ejecutar desde línea de comandos
def main():
    """Punto de entrada principal para ejecución desde línea de comandos"""
    version_manager = VersionManager()
    
    # Ejemplo de uso
    entity_type = "strategy"
    entity_id = "example_strategy_123"
    
    # Contenido de ejemplo
    content1 = """
    name: Example Strategy v1
    description: Primera versión de la estrategia
    indicators:
      - RSI
      - MACD
    parameters:
      rsi_period: 14
      macd_fast: 12
      macd_slow: 26
    """
    
    # Guardar primera versión
    version1 = version_manager.save_version(
        entity_type, 
        entity_id, 
        content1, 
        {"author": "system", "notes": "Versión inicial"}
    )
    
    # Contenido modificado
    content2 = """
    name: Example Strategy v2
    description: Segunda versión mejorada
    indicators:
      - RSI
      - MACD
      - Bollinger Bands
    parameters:
      rsi_period: 10
      macd_fast: 8
      macd_slow: 21
      bb_period: 20
    """
    
    # Guardar segunda versión
    version2 = version_manager.save_version(
        entity_type, 
        entity_id, 
        content2, 
        {"author": "system", "notes": "Añadido Bollinger Bands y optimizados parámetros"}
    )
    
    # Listar versiones
    versions = version_manager.list_versions(entity_type, entity_id)
    print(f"Versiones disponibles: {len(versions)}")
    for v in versions:
        print(f"  - {v['version_id']} ({v['timestamp']})")
    
    # Comparar versiones
    diff = version_manager.compare_versions(entity_type, entity_id, version1, version2)
    print("\nDiferencias entre versiones:")
    for path, change in diff.items():
        print(f"  - {path}: {change['type']}")
    
    # Hacer rollback
    rollback_success = version_manager.rollback(entity_type, entity_id, version1)
    print(f"\nRollback a versión {version1}: {'Exitoso' if rollback_success else 'Fallido'}")
    
    # Listar versiones después del rollback
    versions = version_manager.list_versions(entity_type, entity_id)
    print(f"\nVersiones después del rollback: {len(versions)}")
    for v in versions:
        print(f"  - {v['version_id']} ({v['timestamp']})")

if __name__ == "__main__":
    main()
