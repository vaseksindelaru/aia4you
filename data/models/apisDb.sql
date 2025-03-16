CREATE TABLE apis_db (
    uuid VARCHAR(36) PRIMARY KEY,  -- UUID como identificador único
    name VARCHAR(255) NOT NULL,    -- Nombre de la estrategia
    description TEXT NOT NULL,     -- Descripción de la estrategia
    config_yaml TEXT NOT NULL      -- Configuración en formato YAML como texto
);

-- Ejemplo de inserción con los datos proporcionados
INSERT INTO apis_db (uuid, name, description, config_yaml) VALUES (
    '550e8400-e29b-41d4-a716-446655440000',  -- Ejemplo de UUID
    'MomentumTrading',
    'La estrategia busca detectar un movimiento sostenido del precio en una dirección (alcista o bajista). Esto implica medir la fuerza y la persistencia del movimiento.',
    'indicators:\n  - momentum\n  - rsi\n  - macd\ninputs:\n  - price_data: "Serie temporal de precios (cierre)"\n  - volume_data: "Volumen (opcional para sinergia)"\nconditions:\n  momentum:\n    period: 14\n    signal: "MOM > 0 (alcista), MOM < 0 (bajista)"\n  rsi:\n    period: 14\n    signal: "50 < RSI < 70 (alcista), 30 < RSI < 50 (bajista)"\n  macd:\n    settings: [12, 26, 9]\n    signal: "MACD > Signal Line (alcista), MACD < Signal Line (bajista)"\ncorrelations:\n  orderFlow: "Confirmar volumen alto en la dirección del movimiento"'
);

-- Crear la tabla de indicadores si no existe
CREATE TABLE IF NOT EXISTS apisIndicators (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

-- Insertar los indicadores básicos
INSERT INTO apisIndicators (name) VALUES 
    ('ma'),      -- Media móvil
    ('rsi'),     -- Relative Strength Index
    ('macd'),    -- Moving Average Convergence Divergence
    ('volume'),  -- Volumen
    ('bollinger'), -- Bandas de Bollinger
    ('adx'),     -- Average Directional Index
    ('stoch'),   -- Estocástico
    ('ema');     -- Media móvil exponencial