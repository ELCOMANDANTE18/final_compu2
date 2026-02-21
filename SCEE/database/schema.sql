-- Borramos las tablas si existen para evitar conflictos al resetear (OJO: borra datos)
DROP TABLE IF EXISTS entregas;
DROP TABLE IF EXISTS tps;
DROP TABLE IF EXISTS mensajes;
DROP TABLE IF EXISTS miembros_sala;
DROP TABLE IF EXISTS salas;

-- 1. Entidad: salas
CREATE TABLE salas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    id_creador INT,
    FOREIGN KEY (id_creador) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 2. Entidad: miembros_sala (Muchos a Muchos)
CREATE TABLE miembros_sala (
    id_usuario INT,
    id_sala INT,
    PRIMARY KEY (id_usuario, id_sala),
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (id_sala) REFERENCES salas(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 3. Entidad: mensajes (Persistencia del Chat)
CREATE TABLE mensajes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_sala INT,
    id_emisor INT,
    contenido TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_sala) REFERENCES salas(id) ON DELETE CASCADE,
    FOREIGN KEY (id_emisor) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 4. Entidad: TPS (Para Celery)
CREATE TABLE tps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_sala INT,
    id_profesor INT,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_vencimiento DATETIME,
    FOREIGN KEY (id_sala) REFERENCES salas(id) ON DELETE CASCADE,
    FOREIGN KEY (id_profesor) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 5. Entidad: entregas (Estado de los alumnos)
CREATE TABLE entregas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_tp INT,
    id_alumno INT,
    contenido TEXT,
    fecha_entrega TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('entregado', 'corregido') DEFAULT 'entregado',
    calificacion INT DEFAULT NULL,
    FOREIGN KEY (id_tp) REFERENCES tps(id) ON DELETE CASCADE,
    FOREIGN KEY (id_alumno) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB;