-- Crear la tabla de indicadores
CREATE TABLE IF NOT EXISTS indicators (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

-- Insertar los indicadores básicos
INSERT INTO indicators (name) VALUES 
    ('Moving Average'),
    ('Relative Strength Index'),
    ('Moving Average Convergence Divergence'),
    ('Momentum'),
    ('Bollinger Bands'),
    ('Average Directional Index'),
    ('Stochastic Oscillator'),
    ('Volume');
