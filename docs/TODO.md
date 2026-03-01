
---

# TODO - Roadmap de Mejoras Futuras 🚀

Este documento detalla las funcionalidades, optimizaciones técnicas y nuevas características planificadas para las próximas versiones de **SCEE Mendoza**.

### 🛠️ Mejoras Técnicas y de Arquitectura

* [ ] **Borrado Lógico:** Implementar un sistema de `is_deleted` en MariaDB para evitar la pérdida permanente de datos y permitir la recuperación de registros (Tareas, Entregas, Notas).
* [ ] **Cifrado SSL/TLS:** Añadir una capa de seguridad en la comunicación de sockets para que los mensajes y credenciales viajen cifrados entre el cliente y el servidor.
* [ ] **Optimización de Pipes:** Refinar el protocolo de comunicación IPC entre el servidor asíncrono y el worker de persistencia para reducir la latencia en ráfagas de alta carga.
* [ ] **Logs Centralizados:** Implementar un sistema de registro de eventos (logging) que almacene errores y auditorías en archivos rotativos dentro de los contenedores.

### ✨ Nuevas Funcionalidades para el Usuario

* [ ] **Interfaz Gráfica (GUI):** Desarrollar un cliente visual (utilizando librerías como Tkinter o PyQt) para mejorar la usabilidad frente a la terminal actual.
* [ ] **Notificaciones Push:** Integrar alertas de escritorio nativas para que los alumnos reciban avisos de "Vencimiento" o "Calificación" aunque la aplicación esté en segundo plano.
* [ ] **Gestión de Archivos Pro:** Mejorar el comando `/subir` para permitir el envío de archivos adjuntos pesados mediante *streaming* de bytes, evitando bloqueos de memoria.
* [ ] **Perfiles de Usuario:** Permitir que cada alumno o profesor gestione una descripción, foto de perfil y correo electrónico de contacto.

### 🌐 Infraestructura y Escalabilidad

* [ ] **Orquestación con Kubernetes:** Crear los archivos de configuración (manifiestos) para permitir el despliegue del sistema en clústeres de alta disponibilidad.
* [ ] **Dashboard de Monitoreo:** Integrar una herramienta de visualización (como Grafana) para monitorear el estado de la base de datos y la cola de mensajes en Redis.

---