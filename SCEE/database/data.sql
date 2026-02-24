-- Limpieza para evitar errores de duplicado
TRUNCATE TABLE miembros_sala;
TRUNCATE TABLE salas;

-- Ahora sí, insertamos las salas
INSERT INTO salas (nombre, descripcion, id_creador) VALUES 
('General - Computación 2', 'Sala para anuncios generales de la cátedra', 2),
('Equipo de Estudio Alpha', 'Sala privada para el proyecto final', 1);

-- Unimos a los usuarios
INSERT INTO miembros_sala (id_usuario, id_sala) VALUES (1, 1), (2, 1), (4, 1);