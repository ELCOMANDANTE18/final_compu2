-- 1. Crear la tabla de mensajes si no existe
CREATE TABLE IF NOT EXISTS mensajes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_sala INT NOT NULL,
    id_usuario INT NOT NULL,
    contenido TEXT NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Relaciones para mantener la integridad
    FOREIGN KEY (id_sala) REFERENCES salas(id) ON DELETE CASCADE,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- 2. Insertar mensajes semilla (Bienvenida)
-- Usamos subconsultas para encontrar el ID del creador de cada sala
INSERT INTO mensajes (id_sala, id_usuario, contenido)
SELECT id, id_creador, CONCAT('¡Bienvenidos a la sala ', nombre, '! Este es un espacio para compartir apuntes y dudas.')
FROM salas;

-- 3. Mensaje extra de prueba para la sala General
INSERT INTO mensajes (id_sala, id_usuario, contenido)
SELECT id, id_creador, 'Recuerden que el examen final es en febrero. ¡A estudiar!'
FROM salas WHERE nombre LIKE '%General%' LIMIT 1;