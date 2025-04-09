import os
import sys

print("Test simple de Python")
print("====================")
print(f"Python version: {sys.version}")
print(f"Directorio actual: {os.getcwd()}")

try:
    import pandas as pd
    print("Pandas importado correctamente")
except Exception as e:
    print(f"Error al importar pandas: {e}")

try:
    import numpy as np
    print("NumPy importado correctamente")
except Exception as e:
    print(f"Error al importar numpy: {e}")

try:
    import mysql.connector
    print("MySQL Connector importado correctamente")
except Exception as e:
    print(f"Error al importar mysql.connector: {e}")

print("Test completado")
