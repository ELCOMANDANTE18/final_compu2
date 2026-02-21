-- Creamos un par de salas de prueba (asumiendo que los IDs de usuario 1 y 2 existen)
INSERT INTO salas (nombre, descripcion, id_creador) VALUES 
('General - Computación 2', 'Sala para anuncios generales de la cátedra', 2),
('Equipo de Estudio Alpha', 'Sala privada para el proyecto final', 1);

-- Unimos a los usuarios a la sala general
INSERT INTO miembros_sala (id_usuario, id_sala) VALUES 
(1, 1), -- vector a General
(2, 1), -- profe_carlos a General
(4, 1); -- messi a General