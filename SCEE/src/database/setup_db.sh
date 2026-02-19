#!/bin/bash

# 1. Cargar variables de entorno
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ Error: Archivo .env no encontrado."
    exit 1
fi

echo "--- 🐘 Configurando Base de Datos SCEE en $DB_HOST ---"

# 2. Verificar si el comando mysql existe
if ! command -v mysql &> /dev/null; then
    echo "❌ Error: El cliente 'mysql' no está instalado. Corre: sudo apt install mariadb-client"
    exit 1
fi

# 3. Ejecutar SQL usando las variables del .env
# Agregamos -h para el host y -P para el puerto por si no son los de defecto
mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASSWORD <<EOF
DROP DATABASE IF EXISTS $DB_NAME;
CREATE DATABASE $DB_NAME;
USE $DB_NAME;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol ENUM('alumno', 'profesor', 'admin') NOT NULL DEFAULT 'alumno'
) ENGINE=InnoDB;

INSERT INTO usuarios (username, password_hash, rol) VALUES 
('vector', 'pass123', 'alumno'),
('profe_carlos', 'final2026', 'profesor'),
('admin', 'root', 'admin');

SHOW TABLES;
EOF

if [ $? -eq 0 ]; then
    echo "--- ✅ Base de Datos '$DB_NAME' lista ---"
else
    echo "--- ❌ Hubo un error al configurar la base de datos ---"
fi