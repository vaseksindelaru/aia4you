import os
import time
import sys

def monitor_file(file_path):
    """
    Monitorea un archivo y muestra su contenido en tiempo real.
    Similar a 'tail -f' en sistemas Unix.
    """
    try:
        # Verificar si el archivo existe
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write("Archivo de log creado\n")
            print(f"Archivo creado: {file_path}")
        
        # Abrir el archivo y posicionar el puntero al final
        with open(file_path, 'r') as file:
            file.seek(0, os.SEEK_END)
            
            print(f"Monitoreando {file_path}...")
            print("Presiona Ctrl+C para detener.")
            
            while True:
                line = file.readline()
                if line:
                    print(line, end='')
                    sys.stdout.flush()
                else:
                    time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nMonitoreo detenido.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Ruta del archivo de log
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strategy_log.txt")
    
    # Si el archivo no existe, crearlo
    if not os.path.exists(log_file):
        with open(log_file, 'w') as f:
            f.write("Archivo de log creado\n")
    
    # Monitorear el archivo
    monitor_file(log_file)
