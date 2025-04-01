# freak_evolver.py
# Implementa algoritmos avanzados para evolución

import os
import yaml
import logging
import random
import numpy as np
import json
from datetime import datetime
import uuid
import sys

# Agregar directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Importar módulos necesarios
from actions.check.fuzzy_check import get_similarity_ratio
from core.trading_simulator import TradingSimulator  # Asumiendo que existe esta clase

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("freak_evolver.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FreakEvolver:
    """
    Clase que implementa algoritmos avanzados para la evolución de estrategias.
    Utiliza técnicas de optimización genética y aprendizaje por refuerzo para
    mejorar progresivamente las estrategias de trading.
    """
    
    def __init__(self, db_connection=None, config=None):
        """
        Inicializa el evolucionador con conexión a base de datos y configuración.
        
        Args:
            db_connection: Conexión a la base de datos (opcional)
            config (dict): Configuración para el evolucionador (opcional)
        """
        self.db_connection = db_connection
        self.config = config or {}
        self.simulator = TradingSimulator()
        logger.info("FreakEvolver inicializado")
    
    def evolve_strategy(self, strategy_yaml, generations=5, population_size=20):
        """
        Evoluciona una estrategia utilizando algoritmos genéticos.
        
        Args:
            strategy_yaml (str): Contenido YAML de la estrategia
            generations (int): Número de generaciones a evolucionar
            population_size (int): Tamaño de la población en cada generación
            
        Returns:
            str: YAML de la estrategia evolucionada
        """
        logger.info("Iniciando evolución de estrategia con %d generaciones", generations)
        
        try:
            # Convertir YAML a diccionario
            strategy_dict = yaml.safe_load(strategy_yaml)
            
            # Crear población inicial
            population = self._create_initial_population(strategy_dict, population_size)
            
            # Evolucionar a través de generaciones
            for gen in range(generations):
                logger.info("Generación %d/%d", gen + 1, generations)
                
                # Evaluar fitness de cada individuo
                fitness_scores = self._evaluate_population(population)
                
                # Seleccionar los mejores individuos
                elite, selected = self._selection(population, fitness_scores)
                
                # Crear nueva generación
                new_population = elite.copy()  # Mantener la élite
                
                # Llenar el resto de la población con cruces y mutaciones
                while len(new_population) < population_size:
                    # Seleccionar padres
                    parent1 = random.choice(selected)
                    parent2 = random.choice(selected)
                    
                    # Cruzar y mutar
                    child = self._crossover(parent1, parent2)
                    child = self._mutate(child)
                    
                    new_population.append(child)
                
                # Actualizar población
                population = new_population
                
                # Registrar mejor individuo de esta generación
                best_idx = np.argmax(fitness_scores)
                best_fitness = fitness_scores[best_idx]
                logger.info("Mejor fitness en generación %d: %.4f", gen + 1, best_fitness)
            
            # Seleccionar el mejor individuo de la última generación
            final_fitness = self._evaluate_population(population)
            best_idx = np.argmax(final_fitness)
            best_strategy = population[best_idx]
            
            # Convertir de vuelta a YAML
            evolved_yaml = yaml.dump(best_strategy, sort_keys=False)
            
            logger.info("Evolución completada con éxito")
            return evolved_yaml
            
        except Exception as e:
            logger.error("Error durante la evolución: %s", str(e))
            return strategy_yaml  # Devolver la estrategia original en caso de error
    
    def _create_initial_population(self, base_strategy, size):
        """
        Crea una población inicial basada en la estrategia base.
        
        Args:
            base_strategy (dict): Estrategia base
            size (int): Tamaño de la población
            
        Returns:
            list: Lista de estrategias (diccionarios)
        """
        population = [base_strategy.copy()]  # Incluir la estrategia original
        
        # Generar variantes
        for _ in range(size - 1):
            variant = self._create_variant(base_strategy)
            population.append(variant)
        
        return population
    
    def _create_variant(self, strategy):
        """
        Crea una variante de la estrategia con pequeñas modificaciones.
        
        Args:
            strategy (dict): Estrategia base
            
        Returns:
            dict: Estrategia modificada
        """
        variant = strategy.copy()
        
        # Modificar parámetros
        if 'parameters' in variant:
            params = variant['parameters'].copy()
            
            for key, value in params.items():
                if isinstance(value, (int, float)):
                    # Modificar valor numérico con una variación aleatoria
                    variation = random.uniform(-0.2, 0.2)  # ±20%
                    if isinstance(value, int):
                        params[key] = max(1, int(value * (1 + variation)))
                    else:
                        params[key] = value * (1 + variation)
            
            variant['parameters'] = params
        
        # Modificar condiciones (ejemplo simplificado)
        for condition_type in ['entry_conditions', 'exit_conditions']:
            if condition_type in variant and isinstance(variant[condition_type], list):
                # Posibilidad de añadir o quitar una condición
                if random.random() < 0.3 and len(variant[condition_type]) > 1:
                    # Quitar una condición aleatoria
                    idx = random.randrange(len(variant[condition_type]))
                    variant[condition_type].pop(idx)
                elif random.random() < 0.3 and condition_type == 'entry_conditions':
                    # Añadir una condición genérica
                    variant[condition_type].append("new_indicator > threshold")
        
        return variant
    
    def _evaluate_population(self, population):
        """
        Evalúa el fitness de cada estrategia en la población.
        
        Args:
            population (list): Lista de estrategias
            
        Returns:
            list: Puntuaciones de fitness
        """
        fitness_scores = []
        
        for strategy in population:
            # Convertir estrategia a YAML para simulación
            strategy_yaml = yaml.dump(strategy, sort_keys=False)
            
            # Simular trading con esta estrategia
            results = self._simulate_strategy(strategy_yaml)
            
            # Calcular fitness basado en resultados
            fitness = self._calculate_fitness(results)
            fitness_scores.append(fitness)
        
        return fitness_scores
    
    def _simulate_strategy(self, strategy_yaml):
        """
        Simula el rendimiento de una estrategia.
        
        Args:
            strategy_yaml (str): Contenido YAML de la estrategia
            
        Returns:
            dict: Resultados de la simulación
        """
        # Aquí iría la lógica para simular la estrategia
        # En una implementación real, se utilizaría el simulador de trading
        
        # Simulación simplificada para este ejemplo
        try:
            strategy = yaml.safe_load(strategy_yaml)
            
            # Factores que afectan el rendimiento (simplificado)
            num_indicators = len(strategy.get('indicators', []))
            num_conditions = len(strategy.get('entry_conditions', [])) + len(strategy.get('exit_conditions', []))
            
            # Simular resultados
            profit = random.uniform(-10, 30) + num_indicators * 2 + num_conditions * 1.5
            drawdown = random.uniform(5, 20) - num_conditions * 0.5
            win_rate = random.uniform(40, 60) + num_indicators * 1
            
            return {
                "profit_percent": profit,
                "max_drawdown": drawdown,
                "win_rate": win_rate,
                "trades": random.randint(50, 200)
            }
            
        except Exception as e:
            logger.error("Error en simulación: %s", str(e))
            return {
                "profit_percent": -10,
                "max_drawdown": 20,
                "win_rate": 40,
                "trades": 0
            }
    
    def _calculate_fitness(self, results):
        """
        Calcula el fitness de una estrategia basado en sus resultados.
        
        Args:
            results (dict): Resultados de la simulación
            
        Returns:
            float: Puntuación de fitness
        """
        # Ponderaciones para diferentes métricas
        weights = {
            "profit": 0.5,
            "drawdown": 0.3,
            "win_rate": 0.2
        }
        
        # Normalizar y ponderar métricas
        profit_score = max(0, min(1, (results["profit_percent"] + 10) / 40))
        drawdown_score = max(0, min(1, 1 - results["max_drawdown"] / 20))
        win_rate_score = max(0, min(1, results["win_rate"] / 100))
        
        # Calcular fitness ponderado
        fitness = (
            weights["profit"] * profit_score +
            weights["drawdown"] * drawdown_score +
            weights["win_rate"] * win_rate_score
        )
        
        return fitness
    
    def _selection(self, population, fitness_scores, elite_percent=0.1, selection_percent=0.5):
        """
        Selecciona los mejores individuos para reproducción.
        
        Args:
            population (list): Lista de estrategias
            fitness_scores (list): Puntuaciones de fitness
            elite_percent (float): Porcentaje de élite a mantener sin cambios
            selection_percent (float): Porcentaje a seleccionar para reproducción
            
        Returns:
            tuple: (elite, selected) - Élite y seleccionados para reproducción
        """
        # Ordenar población por fitness
        sorted_indices = np.argsort(fitness_scores)[::-1]  # Orden descendente
        
        # Seleccionar élite
        elite_count = max(1, int(len(population) * elite_percent))
        elite_indices = sorted_indices[:elite_count]
        elite = [population[i] for i in elite_indices]
        
        # Seleccionar para reproducción
        selection_count = max(2, int(len(population) * selection_percent))
        selection_indices = sorted_indices[:selection_count]
        selected = [population[i] for i in selection_indices]
        
        return elite, selected
    
    def _crossover(self, parent1, parent2):
        """
        Realiza un cruce entre dos estrategias padres.
        
        Args:
            parent1 (dict): Primera estrategia padre
            parent2 (dict): Segunda estrategia padre
            
        Returns:
            dict: Estrategia hijo resultante del cruce
        """
        child = {}
        
        # Copiar atributos básicos del primer padre
        for key in ['name', 'description', 'market_type', 'timeframe', 'risk_profile']:
            if key in parent1:
                child[key] = parent1[key]
        
        # Combinar indicadores
        if 'indicators' in parent1 and 'indicators' in parent2:
            # Unir indicadores y eliminar duplicados
            all_indicators = parent1['indicators'] + parent2['indicators']
            child['indicators'] = list(set(all_indicators))
        elif 'indicators' in parent1:
            child['indicators'] = parent1['indicators'].copy()
        elif 'indicators' in parent2:
            child['indicators'] = parent2['indicators'].copy()
        
        # Combinar parámetros
        if 'parameters' in parent1 and 'parameters' in parent2:
            child['parameters'] = {}
            all_params = set(list(parent1['parameters'].keys()) + list(parent2['parameters'].keys()))
            
            for param in all_params:
                # Si ambos padres tienen el parámetro, elegir aleatoriamente o promediar
                if param in parent1['parameters'] and param in parent2['parameters']:
                    if random.random() < 0.5:
                        child['parameters'][param] = parent1['parameters'][param]
                    else:
                        child['parameters'][param] = parent2['parameters'][param]
                elif param in parent1['parameters']:
                    child['parameters'][param] = parent1['parameters'][param]
                else:
                    child['parameters'][param] = parent2['parameters'][param]
        elif 'parameters' in parent1:
            child['parameters'] = parent1['parameters'].copy()
        elif 'parameters' in parent2:
            child['parameters'] = parent2['parameters'].copy()
        
        # Combinar condiciones de entrada/salida
        for condition_type in ['entry_conditions', 'exit_conditions']:
            if condition_type in parent1 and condition_type in parent2:
                # Tomar algunas condiciones de cada padre
                p1_conditions = parent1[condition_type]
                p2_conditions = parent2[condition_type]
                
                # Elegir aleatoriamente cuántas condiciones tomar de cada padre
                p1_count = random.randint(0, len(p1_conditions))
                p2_count = random.randint(0, len(p2_conditions))
                
                # Seleccionar condiciones
                selected_p1 = random.sample(p1_conditions, p1_count) if p1_count > 0 else []
                selected_p2 = random.sample(p2_conditions, p2_count) if p2_count > 0 else []
                
                # Combinar condiciones
                child[condition_type] = selected_p1 + selected_p2
            elif condition_type in parent1:
                child[condition_type] = parent1[condition_type].copy()
            elif condition_type in parent2:
                child[condition_type] = parent2[condition_type].copy()
        
        # Combinar gestión de riesgo
        if 'risk_management' in parent1 and 'risk_management' in parent2:
            # Elegir aleatoriamente de qué padre tomar la gestión de riesgo
            if random.random() < 0.5:
                child['risk_management'] = parent1['risk_management'].copy()
            else:
                child['risk_management'] = parent2['risk_management'].copy()
        elif 'risk_management' in parent1:
            child['risk_management'] = parent1['risk_management'].copy()
        elif 'risk_management' in parent2:
            child['risk_management'] = parent2['risk_management'].copy()
        
        return child
    
    def _mutate(self, strategy, mutation_rate=0.2):
        """
        Aplica mutaciones aleatorias a una estrategia.
        
        Args:
            strategy (dict): Estrategia a mutar
            mutation_rate (float): Tasa de mutación (0-1)
            
        Returns:
            dict: Estrategia mutada
        """
        mutated = strategy.copy()
        
        # Mutar parámetros
        if 'parameters' in mutated and random.random() < mutation_rate:
            params = mutated['parameters'].copy()
            
            # Seleccionar un parámetro aleatorio para mutar
            if params:
                param_key = random.choice(list(params.keys()))
                param_value = params[param_key]
                
                if isinstance(param_value, (int, float)):
                    # Aplicar mutación
                    mutation_factor = random.uniform(0.8, 1.2)  # ±20%
                    
                    if isinstance(param_value, int):
                        params[param_key] = max(1, int(param_value * mutation_factor))
                    else:
                        params[param_key] = param_value * mutation_factor
            
            mutated['parameters'] = params
        
        # Mutar condiciones
        for condition_type in ['entry_conditions', 'exit_conditions']:
            if condition_type in mutated and isinstance(mutated[condition_type], list) and random.random() < mutation_rate:
                conditions = mutated[condition_type].copy()
                
                if conditions:
                    # Posibles mutaciones
                    mutation_type = random.choice(['add', 'remove', 'modify'])
                    
                    if mutation_type == 'add' or len(conditions) == 0:
                        # Añadir condición
                        new_condition = "mutated_indicator > threshold"
                        conditions.append(new_condition)
                    elif mutation_type == 'remove' and len(conditions) > 1:
                        # Eliminar condición
                        idx = random.randrange(len(conditions))
                        conditions.pop(idx)
                    elif mutation_type == 'modify' and len(conditions) > 0:
                        # Modificar condición
                        idx = random.randrange(len(conditions))
                        conditions[idx] = conditions[idx].replace('>', '<') if '>' in conditions[idx] else conditions[idx].replace('<', '>')
                
                mutated[condition_type] = conditions
        
        # Mutar gestión de riesgo
        if 'risk_management' in mutated and random.random() < mutation_rate:
            risk = mutated['risk_management'].copy()
            
            # Modificar algún aspecto de la gestión de riesgo
            if 'stop_loss' in risk and isinstance(risk['stop_loss'], str) and '%' in risk['stop_loss']:
                # Extraer valor numérico
                try:
                    value = float(risk['stop_loss'].split('%')[0])
                    # Mutar valor
                    mutated_value = value * random.uniform(0.8, 1.2)
                    risk['stop_loss'] = f"{mutated_value:.1f}%"
                except:
                    pass
            
            mutated['risk_management'] = risk
        
        return mutated
    
    def apply_reinforcement_learning(self, strategy_yaml, episodes=100):
        """
        Aplica aprendizaje por refuerzo para mejorar la estrategia.
        
        Args:
            strategy_yaml (str): Contenido YAML de la estrategia
            episodes (int): Número de episodios de aprendizaje
            
        Returns:
            str: YAML de la estrategia mejorada
        """
        logger.info("Iniciando aprendizaje por refuerzo con %d episodios", episodes)
        
        try:
            # Convertir YAML a diccionario
            strategy_dict = yaml.safe_load(strategy_yaml)
            
            # Inicializar parámetros
            params = strategy_dict.get('parameters', {}).copy()
            
            # Parámetros de aprendizaje
            learning_rate = 0.1
            exploration_rate = 0.2
            discount_factor = 0.9
            
            # Seguimiento del mejor rendimiento
            best_strategy = strategy_dict.copy()
            best_performance = self._evaluate_strategy_performance(strategy_dict)
            
            # Ejecutar episodios de aprendizaje
            for episode in range(episodes):
                # Reducir exploración gradualmente
                current_exploration = exploration_rate * (1 - episode / episodes)
                
                # Crear variante para este episodio
                current_strategy = best_strategy.copy()
                
                # Explorar o explotar
                if random.random() < current_exploration:
                    # Exploración: modificar parámetros aleatoriamente
                    if 'parameters' in current_strategy:
                        for key, value in current_strategy['parameters'].items():
                            if isinstance(value, (int, float)):
                                # Modificar con variación aleatoria
                                variation = random.uniform(-0.3, 0.3)
                                if isinstance(value, int):
                                    current_strategy['parameters'][key] = max(1, int(value * (1 + variation)))
                                else:
                                    current_strategy['parameters'][key] = value * (1 + variation)
                
                # Evaluar rendimiento
                performance = self._evaluate_strategy_performance(current_strategy)
                
                # Actualizar mejor estrategia si es mejor
                if performance > best_performance:
                    best_strategy = current_strategy.copy()
                    best_performance = performance
                    logger.info("Episodio %d: Encontrada mejor estrategia (rendimiento: %.4f)", 
                               episode + 1, best_performance)
            
            # Convertir mejor estrategia a YAML
            improved_yaml = yaml.dump(best_strategy, sort_keys=False)
            
            logger.info("Aprendizaje por refuerzo completado con éxito")
            return improved_yaml
            
        except Exception as e:
            logger.error("Error durante el aprendizaje por refuerzo: %s", str(e))
            return strategy_yaml
    
    def _evaluate_strategy_performance(self, strategy):
        """
        Evalúa el rendimiento de una estrategia.
        
        Args:
            strategy (dict): Estrategia a evaluar
            
        Returns:
            float: Puntuación de rendimiento
        """
        # Convertir estrategia a YAML
        strategy_yaml = yaml.dump(strategy, sort_keys=False)
        
        # Simular trading
        results = self._simulate_strategy(strategy_yaml)
        
        # Calcular rendimiento
        performance = self._calculate_fitness(results)
        
        return performance
    
    def hybridize_strategies(self, strategy_yaml1, strategy_yaml2):
        """
        Crea una estrategia híbrida combinando dos estrategias existentes.
        
        Args:
            strategy_yaml1 (str): Primera estrategia en formato YAML
            strategy_yaml2 (str): Segunda estrategia en formato YAML
            
        Returns:
            str: YAML de la estrategia híbrida
        """
        logger.info("Creando estrategia híbrida")
        
        try:
            # Convertir YAML a diccionarios
            strategy1 = yaml.safe_load(strategy_yaml1)
            strategy2 = yaml.safe_load(strategy_yaml2)
            
            # Crear nombre para la estrategia híbrida
            hybrid_name = f"Hybrid: {strategy1.get('name', 'Strategy1')} + {strategy2.get('name', 'Strategy2')}"
            
            # Realizar cruce
            hybrid = self._crossover(strategy1, strategy2)
            
            # Establecer nombre y descripción
            hybrid['name'] = hybrid_name
            hybrid['description'] = f"Estrategia híbrida creada a partir de {strategy1.get('name', 'Strategy1')} y {strategy2.get('name', 'Strategy2')}"
            
            # Añadir timestamp
            hybrid['created_at'] = datetime.now().isoformat()
            
            # Convertir a YAML
            hybrid_yaml = yaml.dump(hybrid, sort_keys=False)
            
            logger.info("Estrategia híbrida creada con éxito")
            return hybrid_yaml
            
        except Exception as e:
            logger.error("Error al crear estrategia híbrida: %s", str(e))
            return strategy_yaml1  # Devolver primera estrategia en caso de error
    
    def analyze_strategy_components(self, strategy_yaml):
        """
        Analiza los componentes de una estrategia para identificar fortalezas y debilidades.
        
        Args:
            strategy_yaml (str): Contenido YAML de la estrategia
            
        Returns:
            dict: Análisis de componentes
        """
        logger.info("Analizando componentes de la estrategia")
        
        try:
            # Convertir YAML a diccionario
            strategy = yaml.safe_load(strategy_yaml)
            
            analysis = {
                "name": strategy.get('name', 'Unknown'),
                "components": {},
                "strengths": [],
                "weaknesses": [],
                "improvement_suggestions": []
            }
            
            # Analizar indicadores
            indicators = strategy.get('indicators', [])
            analysis["components"]["indicators"] = {
                "count": len(indicators),
                "list": indicators,
                "diversity": self._calculate_diversity(indicators)
            }
            
            # Analizar condiciones
            entry_conditions = strategy.get('entry_conditions', [])
            exit_conditions = strategy.get('exit_conditions', [])
            
            analysis["components"]["conditions"] = {
                "entry_count": len(entry_conditions),
                "exit_count": len(exit_conditions),
                "entry_conditions": entry_conditions,
                "exit_conditions": exit_conditions
            }
            
            # Analizar parámetros
            parameters = strategy.get('parameters', {})
            analysis["components"]["parameters"] = {
                "count": len(parameters),
                "list": parameters
            }
            
            # Analizar gestión de riesgo
            risk_management = strategy.get('risk_management', {})
            analysis["components"]["risk_management"] = risk_management
            
            # Identificar fortalezas
            if len(indicators) >= 3:
                analysis["strengths"].append("Buena diversidad de indicadores")
            
            if len(entry_conditions) >= 2 and len(exit_conditions) >= 2:
                analysis["strengths"].append("Condiciones de entrada y salida bien definidas")
            
            if 'stop_loss' in risk_management and 'take_profit' in risk_management:
                analysis["strengths"].append("Gestión de riesgo completa con stop loss y take profit")
            
            # Identificar debilidades
            if len(indicators) < 2:
                analysis["weaknesses"].append("Pocos indicadores")
                analysis["improvement_suggestions"].append("Añadir más indicadores para confirmación")
            
            if len(entry_conditions) < 2:
                analysis["weaknesses"].append("Pocas condiciones de entrada")
                analysis["improvement_suggestions"].append("Añadir más condiciones de entrada para filtrar señales")
            
            if len(exit_conditions) < 2:
                analysis["weaknesses"].append("Pocas condiciones de salida")
                analysis["improvement_suggestions"].append("Añadir más condiciones de salida para proteger ganancias")
            
            if 'stop_loss' not in risk_management:
                analysis["weaknesses"].append("Sin stop loss definido")
                analysis["improvement_suggestions"].append("Añadir stop loss para limitar pérdidas")
            
            logger.info("Análisis de componentes completado")
            return analysis
            
        except Exception as e:
            logger.error("Error al analizar componentes: %s", str(e))
            return {"error": str(e)}
    
    def _calculate_diversity(self, items):
        """
        Calcula la diversidad de una lista de elementos.
        
        Args:
            items (list): Lista de elementos
            
        Returns:
            float: Puntuación de diversidad (0-1)
        """
        if not items:
            return 0
        
        # Calcular similitud entre pares
        total_pairs = 0
        total_similarity = 0
        
        for i in range(len(items)):
            for j in range(i+1, len(items)):
                similarity = get_similarity_ratio(str(items[i]), str(items[j]))
                total_similarity += similarity
                total_pairs += 1
        
        # Si no hay pares, la diversidad es máxima
        if total_pairs == 0:
            return 1
        
        # Calcular diversidad como 1 - similitud media
        avg_similarity = total_similarity / total_pairs
        diversity = 1 - avg_similarity
        
        return diversity

# Función principal para ejecutar desde línea de comandos
def main():
    """Punto de entrada principal para ejecución desde línea de comandos"""
    evolver = FreakEvolver()
    
    # Ejemplo de estrategia para evolucionar
    example_strategy = """
    name: Example Trading Strategy
    description: Estrategia de ejemplo para demostrar evolución
    indicators:
      - RSI
      - MACD
      - Bollinger Bands
    parameters:
      rsi_period: 14
      rsi_overbought: 70
      rsi_oversold: 30
      macd_fast: 12
      macd_slow: 26
      macd_signal: 9
      bb_period: 20
      bb_deviation: 2
    entry_conditions:
      - RSI < rsi_oversold
      - price < lower_bb
    exit_conditions:
      - RSI > rsi_overbought
      - price > upper_bb
      - take_profit_reached
      - stop_loss_triggered
    risk_management:
      position_size: 2%
      stop_loss: 3%
      take_profit: 6%
      trailing_stop: true
    """
    
    # Evolucionar estrategia
    print("Evolucionando estrategia...")
    evolved = evolver.evolve_strategy(example_strategy, generations=3, population_size=10)
    
    print("\nEstrategia evolucionada:")
    print(evolved)
    
    # Analizar componentes
    print("\nAnalizando componentes...")
    analysis = evolver.analyze_strategy_components(evolved)
    
    print("\nAnálisis de componentes:")
    print(f"Fortalezas: {analysis['strengths']}")
    print(f"Debilidades: {analysis['weaknesses']}")
    print(f"Sugerencias: {analysis['improvement_suggestions']}")

if __name__ == "__main__":
    main()
