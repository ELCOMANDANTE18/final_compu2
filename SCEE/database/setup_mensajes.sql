DROP TABLE IF EXISTS mensajes;

CREATE TABLE mensajes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_sala INT NOT NULL,
    id_usuario INT NOT NULL, -- <--- USAR id_usuario
    contenido TEXT NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_sala) REFERENCES salas(id) ON DELETE CASCADE,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE
);

INSERT INTO mensajes (id_sala, id_usuario, contenido)
SELECT id, id_creador, CONCAT('¡Bienvenidos a la sala ', nombre, '!')
FROM salas;