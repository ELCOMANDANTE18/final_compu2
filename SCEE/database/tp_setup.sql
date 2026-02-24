TRUNCATE TABLE tareas;

INSERT INTO tareas (id_sala, titulo, descripcion, fecha_entrega)
SELECT id, 'TP Final - Computación II', 'Implementar Milestone 5: Docker y Celery.', '2026-03-15 23:59:00'
FROM salas WHERE nombre LIKE '%General%' LIMIT 1;