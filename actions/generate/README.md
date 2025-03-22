# Strategy Generator

Este módulo proporciona funcionalidades para generar estrategias de trading basadas en prompts de usuario.

## Estructura

- `strategy_generator.py`: Módulo principal que contiene la lógica para generar estrategias
  - `StrategyRequest`: Modelo Pydantic para las solicitudes de estrategia
  - `get_available_indicators()`: Obtiene la lista de indicadores disponibles
  - `generate_strategy_yaml()`: Genera la configuración YAML de la estrategia
  - `process_strategy_request()`: Procesa las solicitudes de generación de estrategias

## Uso

```python
from strategy_generator import process_strategy_request, StrategyRequest

# Crear una solicitud de estrategia
request = StrategyRequest(prompt="Crear una estrategia de Momentum Trading")

# Procesar la solicitud
response = await process_strategy_request(request)

# El response contendrá el YAML de la estrategia
print(response["strategy_yaml"])
```

## Formato del YAML generado

```yaml
indicators:
  - Nombre del Indicador (ABREV)  # Descripción del uso
inputs:
  - input_name                    # Descripción del input
conditions:
  indicator_name:
    period: valor
    signal: "Descripción de la señal"
correlations:
  factor: "Descripción de la correlación"
```
