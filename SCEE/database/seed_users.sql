USE scee_db;

-- Limpiamos la tabla para empezar de cero
TRUNCATE TABLE usuarios;

-- Agregamos usuarios con diferentes roles para probar el sistema
INSERT INTO usuarios (username, password_hash, rol) VALUES 
('vector', 'pass123', 'alumno'),        -- Tu usuario de prueba
('profe_carlos', 'final2026', 'profesor'), -- El usuario del Profe
('admin_sistema', 'root_scee', 'admin');  -- El administrador