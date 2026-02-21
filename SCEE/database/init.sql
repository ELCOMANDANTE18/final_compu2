CREATE DATABASE IF NOT EXISTS scee_db;
USE scee_db;

-- 1. Usuarios (Ya lo teníamos, pero aseguramos los roles)
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol ENUM('alumno', 'profesor', 'admin') NOT NULL DEFAULT 'alumno'
) ENGINE=InnoDB;

-- 2. Salas (Espacios de trabajo)
CREATE TABLE IF NOT EXISTS salas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    id_creador INT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_creador) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 3. Miembros de Sala (Relación Muchos a Muchos)
CREATE TABLE IF NOT EXISTS miembros_sala (
    id_usuario INT,
    id_sala INT,
    fecha_union TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_usuario, id_sala),
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (id_sala) REFERENCES salas(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 4. Mensajes (Persistencia de la comunicación)
CREATE TABLE IF NOT EXISTS mensajes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_sala INT,
    id_emisor INT,
    contenido TEXT NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_sala) REFERENCES salas(id) ON DELETE CASCADE,
    FOREIGN KEY (id_emisor) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5. Tareas/Documentos (Lo que usará Celery)
CREATE TABLE IF NOT EXISTS tareas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_sala INT,
    titulo VARCHAR(150) NOT NULL,
    descripcion TEXT,
    fecha_vencimiento DATETIME,
    estado ENUM('pendiente', 'completada', 'vencida') DEFAULT 'pendiente',
    FOREIGN KEY (id_sala) REFERENCES salas(id) ON DELETE CASCADE
) ENGINE=InnoDB;