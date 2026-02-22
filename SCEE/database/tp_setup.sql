-- Tabla para Tareas (Issue #12)
CREATE TABLE IF NOT EXISTS tareas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_sala INT NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    descripcion TEXT,
    fecha_entrega DATETIME,
    FOREIGN KEY (id_sala) REFERENCES salas(id) ON DELETE CASCADE
);

-- Semillas: Tareas para que Abel y Benja tengan qué ver
INSERT INTO tareas (id_sala, titulo, descripcion, fecha_entrega)
SELECT id, 'TP Final - Computación II', 'Implementar Milestone 5: Docker y Celery.', '2026-03-15 23:59:00'
FROM salas WHERE nombre LIKE '%General%' LIMIT 1;

INSERT INTO tareas (id_sala, titulo, descripcion, fecha_entrega)
SELECT id, 'Investigación: Sockets vs WebSockets', 'Documento comparativo de protocolos.', '2026-03-10 18:00:00'
FROM salas WHERE nombre LIKE '%Sistemas Operativos%' LIMIT 1;