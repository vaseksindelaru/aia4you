# Guía de Solución de Problemas para A_Optimizer

## Problemas Comunes y Soluciones

### 1. Problemas de Conexión a la Base de Datos

Si tienes problemas para conectarte a la base de datos MySQL, sigue estos pasos:

1. **Verifica las credenciales en el archivo `.env`**:
   ```
   MYSQL_HOST=localhost
   MYSQL_USER=tu_usuario
   MYSQL_PASSWORD=tu_contraseña
   MYSQL_DATABASE=binance_lob
   ```

2. **Comprueba que el servidor MySQL esté en funcionamiento**:
   - En Windows, verifica que el servicio MySQL esté activo en el Administrador de Servicios.
   - Puedes intentar conectarte manualmente usando MySQL Workbench o la línea de comandos.

3. **Verifica que la base de datos exista**:
   - Conéctate a MySQL y ejecuta: `SHOW DATABASES;`
   - Si `binance_lob` no aparece, créala con: `CREATE DATABASE binance_lob;`

4. **Ejecuta el script de prueba de conexión**:
   ```
   python test_db_connection.py
   ```

### 2. Problemas con las Tablas

Si las tablas necesarias no existen o tienen una estructura incorrecta:

1. **Crea las tablas necesarias**:
   ```
   python create_A_optimizer_tables.py
   ```

2. **Verifica la estructura de las tablas**:
   Conéctate a MySQL y ejecuta:
   ```sql
   DESCRIBE A_detection_params;
   DESCRIBE A_detection_data;
   DESCRIBE A_range_params;
   DESCRIBE A_range_data;
   DESCRIBE A_breakout_params;
   DESCRIBE A_breakout_data;
   ```

### 3. Problemas de Codificación de Caracteres

Si ves caracteres extraños en la salida de la consola:

1. **Ejecuta los scripts con el parámetro `-u`**:
   ```
   python -u execute_A_optimizer_manual.py
   ```

2. **Configura la codificación de la consola**:
   ```
   chcp 65001
   ```

### 4. Problemas de Importación de Módulos

Si tienes problemas para importar los módulos:

1. **Verifica que todos los archivos `__init__.py` existan**:
   - `actions/__init__.py`
   - `actions/evolve/__init__.py`
   - `actions/evolve/A_optimizer/__init__.py`

2. **Comprueba los nombres de las clases**:
   - Las clases deben llamarse `A_Detection`, `A_Range` y `A_Breakout`.

### 5. Alternativas para Ejecutar el Sistema

Si continúas teniendo problemas, puedes usar versiones alternativas del script:

1. **Versión sin base de datos**:
   ```
   python execute_A_optimizer_simple.py
   ```

2. **Versión final simplificada**:
   ```
   python execute_A_optimizer_final.py
   ```

## Guardado de Resultados en la Base de Datos

Para guardar correctamente los resultados en la base de datos, sigue estos pasos:

1. **Asegúrate de que las tablas existan**:
   ```
   python create_A_optimizer_tables.py
   ```

2. **Verifica la conexión a la base de datos**:
   ```
   python test_db_connection.py
   ```

3. **Ejecuta el script con guardado en base de datos**:
   ```
   python execute_A_optimizer_db.py
   ```

4. **Verifica los resultados en la base de datos**:
   ```sql
   SELECT * FROM A_detection_params ORDER BY id DESC LIMIT 1;
   SELECT * FROM A_detection_data WHERE param_id = [ID_del_param];
   SELECT * FROM A_range_params ORDER BY id DESC LIMIT 1;
   SELECT * FROM A_range_data WHERE param_id = [ID_del_param];
   SELECT * FROM A_breakout_params ORDER BY id DESC LIMIT 1;
   SELECT * FROM A_breakout_data WHERE param_id = [ID_del_param];
   ```

## Estructura de las Tablas

### A_detection_params
- `id`: ID único del parámetro
- `volume_percentile_threshold`: Umbral de percentil de volumen
- `body_percentage_threshold`: Umbral de porcentaje del cuerpo
- `lookback_candles`: Número de velas para mirar hacia atrás
- `created_at`: Fecha y hora de creación

### A_detection_data
- `id`: ID único del dato
- `timestamp`: Marca de tiempo de la vela
- `is_key_candle`: Si es una vela clave (1) o no (0)
- `volume`: Volumen de la vela
- `body_percentage`: Porcentaje del cuerpo de la vela
- `param_id`: ID del parámetro relacionado
- `created_at`: Fecha y hora de creación

### A_range_params
- `id`: ID único del parámetro
- `atr_period`: Período ATR
- `atr_multiplier`: Multiplicador ATR
- `created_at`: Fecha y hora de creación

### A_range_data
- `id`: ID único del dato
- `timestamp`: Marca de tiempo del rango
- `reference_price`: Precio de referencia
- `upper_limit`: Límite superior
- `lower_limit`: Límite inferior
- `atr_value`: Valor ATR
- `param_id`: ID del parámetro relacionado
- `detection_id`: ID de la detección relacionada
- `created_at`: Fecha y hora de creación

### A_breakout_params
- `id`: ID único del parámetro
- `breakout_threshold_percentage`: Porcentaje umbral de breakout
- `max_candles_to_return`: Máximo número de velas a devolver
- `created_at`: Fecha y hora de creación

### A_breakout_data
- `id`: ID único del dato
- `timestamp`: Marca de tiempo del breakout
- `direction`: Dirección del breakout (bullish/bearish)
- `breakout_percentage`: Porcentaje de breakout
- `is_valid`: Si es un breakout válido (1) o no (0)
- `param_id`: ID del parámetro relacionado
- `range_id`: ID del rango relacionado
- `created_at`: Fecha y hora de creación
