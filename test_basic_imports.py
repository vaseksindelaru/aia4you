import os
import sys

# Añadir el directorio raíz al path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

print("Intentando importar módulos de A_optimizer...")

try:
    import actions.evolve.A_optimizer.detection
    print("Módulo detection importado")
except Exception as e:
    print(f"Error al importar detection: {e}")

try:
    import actions.evolve.A_optimizer.range
    print("Módulo range importado")
except Exception as e:
    print(f"Error al importar range: {e}")

try:
    import actions.evolve.A_optimizer.breakout
    print("Módulo breakout importado")
except Exception as e:
    print(f"Error al importar breakout: {e}")

print("Fin de la prueba de importación")
