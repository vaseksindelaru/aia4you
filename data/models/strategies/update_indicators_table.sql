-- Modificar la tabla de indicadores para añadir campos adicionales
ALTER TABLE indicators 
ADD COLUMN IF NOT EXISTS uuid VARCHAR(36) AFTER id,
ADD COLUMN IF NOT EXISTS description TEXT AFTER name,
ADD COLUMN IF NOT EXISTS config_yaml TEXT AFTER description,
ADD COLUMN IF NOT EXISTS implementation_yaml TEXT AFTER config_yaml,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Actualizar registros existentes para asignar UUIDs si no los tienen
UPDATE indicators SET uuid = UUID() WHERE uuid IS NULL;
