"""
Script para configurar el entorno para el sistema A_optimizer
"""
import os
import sys
import importlib
import subprocess
import pkg_resources

def check_and_install_dependencies():
    """Verificar e instalar dependencias necesarias"""
    print("Verificando dependencias...")
    
    required_packages = {
        'pandas': 'pandas',
        'numpy': 'numpy',
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'mysql-connector-python': 'mysql.connector',
        'python-dotenv': 'dotenv',
        'requests': 'requests'
    }
    
    missing_packages = []
    
    for package, import_name in required_packages.items():
        try:
            importlib.import_module(import_name)
            print(f"[OK] {package} ya está instalado")
        except ImportError:
            print(f"[ERROR] {package} no está instalado")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nInstalando paquetes faltantes: {', '.join(missing_packages)}")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"[OK] {package} instalado correctamente")
            except Exception as e:
                print(f"[ERROR] No se pudo instalar {package}: {e}")
    else:
        print("Todas las dependencias están instaladas")

def check_and_create_init_files():
    """Verificar y crear archivos __init__.py faltantes"""
    print("\nVerificando archivos __init__.py...")
    
    directories = [
        'actions',
        'actions/evolve',
        'actions/evolve/A_optimizer',
        'actions/run',
        'actions/check',
        'apis',
        'apis/indicators',
        'apis/indicators/atr'
    ]
    
    for directory in directories:
        dir_path = os.path.join(os.path.dirname(__file__), directory)
        init_file = os.path.join(dir_path, '__init__.py')
        
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
                print(f"[OK] Directorio {directory} creado")
            except Exception as e:
                print(f"[ERROR] No se pudo crear el directorio {directory}: {e}")
                continue
        
        if not os.path.exists(init_file):
            try:
                with open(init_file, 'w') as f:
                    f.write("# Archivo generado automáticamente para permitir importaciones\n")
                print(f"[OK] Archivo {init_file} creado")
            except Exception as e:
                print(f"[ERROR] No se pudo crear el archivo {init_file}: {e}")

def fix_imports():
    """Corregir problemas de importación en los módulos"""
    print("\nCorrigiendo importaciones en los módulos...")
    
    # Corregir __init__.py en actions/evolve/A_optimizer
    optimizer_init = os.path.join(os.path.dirname(__file__), 'actions', 'evolve', 'A_optimizer', '__init__.py')
    try:
        with open(optimizer_init, 'w') as f:
            f.write("""# Archivo de inicialización para el módulo A_optimizer
from .detection import A_Detection
from .range import A_Range
from .breakout import A_Breakout
""")
        print(f"[OK] Archivo {optimizer_init} actualizado")
    except Exception as e:
        print(f"[ERROR] No se pudo actualizar el archivo {optimizer_init}: {e}")

def main():
    """Función principal"""
    print("==============================================")
    print("CONFIGURACIÓN DEL ENTORNO PARA A_OPTIMIZER")
    print("==============================================")
    
    # Verificar e instalar dependencias
    check_and_install_dependencies()
    
    # Verificar y crear archivos __init__.py
    check_and_create_init_files()
    
    # Corregir importaciones
    fix_imports()
    
    print("\n==============================================")
    print("CONFIGURACIÓN DEL ENTORNO COMPLETADA")
    print("==============================================")
    print("Ahora puedes ejecutar las pruebas del sistema A_optimizer")

if __name__ == "__main__":
    main()
