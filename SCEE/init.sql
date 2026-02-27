/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19  Distrib 10.11.14-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: scee_db
-- ------------------------------------------------------
-- Server version	10.11.14-MariaDB-0ubuntu0.24.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `entregas`
--

DROP TABLE IF EXISTS `entregas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `entregas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_tp` int(11) DEFAULT NULL,
  `id_alumno` int(11) DEFAULT NULL,
  `contenido` text DEFAULT NULL,
  `fecha_entrega` timestamp NULL DEFAULT current_timestamp(),
  `estado` enum('entregado','corregido') DEFAULT 'entregado',
  `calificacion` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `id_alumno` (`id_alumno`),
  KEY `fk_entrega_tarea` (`id_tp`),
  CONSTRAINT `entregas_ibfk_2` FOREIGN KEY (`id_alumno`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_entrega_tarea` FOREIGN KEY (`id_tp`) REFERENCES `tareas` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `entregas`
--

LOCK TABLES `entregas` WRITE;
/*!40000 ALTER TABLE `entregas` DISABLE KEYS */;
INSERT INTO `entregas` VALUES
(2,1,5,'Profe, ahora sí con la base de datos bien relacionada desde Mendoza','2026-02-26 14:46:55','corregido',9);
/*!40000 ALTER TABLE `entregas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `mensajes`
--

DROP TABLE IF EXISTS `mensajes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `mensajes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_sala` int(11) NOT NULL,
  `id_usuario` int(11) NOT NULL,
  `contenido` text NOT NULL,
  `fecha` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `id_sala` (`id_sala`),
  KEY `id_usuario` (`id_usuario`),
  CONSTRAINT `mensajes_ibfk_1` FOREIGN KEY (`id_sala`) REFERENCES `salas` (`id`) ON DELETE CASCADE,
  CONSTRAINT `mensajes_ibfk_2` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mensajes`
--

LOCK TABLES `mensajes` WRITE;
/*!40000 ALTER TABLE `mensajes` DISABLE KEYS */;
INSERT INTO `mensajes` VALUES
(8,1,2,'¡Bienvenidos a la sala General - Computación 2! Espacio para compartir apuntes.','2026-02-22 13:39:40'),
(9,2,1,'¡Bienvenidos a la sala Equipo de Estudio Alpha! Espacio para compartir apuntes.','2026-02-22 13:39:40'),
(10,3,4,'¡Bienvenidos a la sala Sistemas Operativos! Espacio para compartir apuntes.','2026-02-22 13:39:40'),
(11,4,4,'¡Bienvenidos a la sala Fisica Cuantica! Espacio para compartir apuntes.','2026-02-22 13:39:40'),
(12,5,2,'¡Bienvenidos a la sala Diseño de Sistemas! Espacio para compartir apuntes.','2026-02-22 13:39:40'),
(13,7,4,'¡Bienvenidos a la sala Programacion! Espacio para compartir apuntes.','2026-02-22 13:39:40'),
(15,1,6,'Hola','2026-02-22 13:57:32'),
(16,1,4,'Buenas Tardes alumno hoy habra examen?','2026-02-22 13:57:52'),
(17,1,4,'Buenas Chicos habra examen vayan estudiando','2026-02-22 14:10:56'),
(18,1,4,'Chicos tienen algunda duda ???','2026-02-22 14:17:23'),
(19,1,5,'Si tengo la duda','2026-02-22 14:18:26'),
(20,1,6,'Yo tambien Profe','2026-02-22 14:27:55'),
(21,1,4,'Cual es la duda ???','2026-02-22 14:28:07'),
(22,1,5,'Cuando es el examen ???','2026-02-22 14:35:57'),
(23,1,4,'EL 10 de Marzo','2026-02-22 14:37:21'),
(24,1,6,'Perfecto Profe.','2026-02-22 14:39:28'),
(25,1,4,'Cualquier pregunten si necesitan alguna consulta.','2026-02-22 14:40:14'),
(26,1,4,'/tarea','2026-02-26 17:37:16');
/*!40000 ALTER TABLE `mensajes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `miembros_sala`
--

DROP TABLE IF EXISTS `miembros_sala`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `miembros_sala` (
  `id_usuario` int(11) NOT NULL,
  `id_sala` int(11) NOT NULL,
  PRIMARY KEY (`id_usuario`,`id_sala`),
  KEY `id_sala` (`id_sala`),
  CONSTRAINT `miembros_sala_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE,
  CONSTRAINT `miembros_sala_ibfk_2` FOREIGN KEY (`id_sala`) REFERENCES `salas` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `miembros_sala`
--

LOCK TABLES `miembros_sala` WRITE;
/*!40000 ALTER TABLE `miembros_sala` DISABLE KEYS */;
INSERT INTO `miembros_sala` VALUES
(1,1),
(2,1),
(4,1),
(4,3),
(4,7),
(5,1),
(5,2),
(5,3),
(5,7),
(5,8),
(6,1),
(6,2),
(6,3),
(6,7),
(8,8);
/*!40000 ALTER TABLE `miembros_sala` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `salas`
--

DROP TABLE IF EXISTS `salas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `salas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `id_creador` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `id_creador` (`id_creador`),
  CONSTRAINT `salas_ibfk_1` FOREIGN KEY (`id_creador`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `salas`
--

LOCK TABLES `salas` WRITE;
/*!40000 ALTER TABLE `salas` DISABLE KEYS */;
INSERT INTO `salas` VALUES
(1,'General - Computación 2','Sala para anuncios generales de la cátedra',2),
(2,'Equipo de Estudio Alpha','Sala privada para el proyecto final',1),
(3,'Sistemas Operativos',NULL,4),
(4,'Fisica Cuantica',NULL,4),
(5,'Diseño de Sistemas',NULL,2),
(7,'Programacion','Sala para comunicar cosas de programacion',4),
(8,'Teleinformatica','Espacio para hablar de redes.',8);
/*!40000 ALTER TABLE `salas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tareas`
--

DROP TABLE IF EXISTS `tareas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tareas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_sala` int(11) NOT NULL,
  `titulo` varchar(100) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `fecha_entrega` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `id_sala` (`id_sala`),
  CONSTRAINT `tareas_ibfk_1` FOREIGN KEY (`id_sala`) REFERENCES `salas` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tareas`
--

LOCK TABLES `tareas` WRITE;
/*!40000 ALTER TABLE `tareas` DISABLE KEYS */;
INSERT INTO `tareas` VALUES
(1,1,'TP Final - Computación II','Implementar Milestone 5: Docker y Celery.','2026-03-15 23:59:00'),
(2,3,'Investigación: Sockets vs WebSockets','Documento comparativo de protocolos.','2026-03-10 18:00:00'),
(3,1,'Implementar IPV6','Tiene que agregar que acepte conexiones ipv6','2026-02-27 08:03:18');
/*!40000 ALTER TABLE `tareas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tps`
--

DROP TABLE IF EXISTS `tps`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tps` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_sala` int(11) DEFAULT NULL,
  `id_profesor` int(11) DEFAULT NULL,
  `titulo` varchar(255) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `fecha_creacion` timestamp NULL DEFAULT current_timestamp(),
  `fecha_vencimiento` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `id_sala` (`id_sala`),
  KEY `id_profesor` (`id_profesor`),
  CONSTRAINT `tps_ibfk_1` FOREIGN KEY (`id_sala`) REFERENCES `salas` (`id`) ON DELETE CASCADE,
  CONSTRAINT `tps_ibfk_2` FOREIGN KEY (`id_profesor`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tps`
--

LOCK TABLES `tps` WRITE;
/*!40000 ALTER TABLE `tps` DISABLE KEYS */;
/*!40000 ALTER TABLE `tps` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `rol` enum('alumno','profesor','admin') NOT NULL DEFAULT 'alumno',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES
(1,'vector','pass123','alumno'),
(2,'profe_carlos','final2026','profesor'),
(3,'admin','root','admin'),
(4,'messi','10','profesor'),
(5,'abel','1234','alumno'),
(6,'benja','1234','alumno'),
(8,'Diego','1234','profesor');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;

-- ---------------------------------------------------------
-- NUEVOS DATOS: Tareas y Flujo de Corrección
-- ---------------------------------------------------------

INSERT INTO `tareas` (`id_sala`, `titulo`, `descripcion`, `fecha_entrega`) VALUES
(8, 'Configuración de VLANs', 'Realizar el diseño de red para una empresa con 3 departamentos.', '2026-03-05 12:00:00'),
(7, 'Algoritmos de Búsqueda', 'Implementar búsqueda binaria y comparar tiempos de ejecución.', '2026-03-02 23:59:00');

INSERT INTO `entregas` (`id_tp`, `id_alumno`, `contenido`, `fecha_entrega`, `estado`, `calificacion`) VALUES
-- Benja entrega el TP Final, queda pendiente para el profesor
(1, 6, 'Profe, acá está mi Dockerfile. Me costó pero levantó el Redis.', NOW(), 'entregado', NULL),
-- Vector entrega IPv6 y ya fue corregido con excelente nota
(3, 1, 'Implementación de sockets con Dual Stack completada.', DATE_SUB(NOW(), INTERVAL 2 DAY), 'corregido', 10),
-- Abel entrega la investigación de Sockets vs WebSockets
(2, 5, 'Informe comparativo. WebSockets es mejor para tiempo real.', DATE_SUB(NOW(), INTERVAL 5 HOUR), 'entregado', NULL);

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;