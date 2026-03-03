# 🚀 SCEE Mendoza - Roadmap de Ingeniería

### 🛡️ Seguridad y Resiliencia
- [ ] **Cifrado TLS/SSL:** Implementar `ssl.wrap_socket` en el servidor para proteger la comunicación Dual Stack.
- [ ] **Hashing de Contraseñas:** Migrar el almacenamiento de `password_hash` a `bcrypt` o `argon2` en el Worker de Auth, eliminando el texto plano.
- [ ] **Persistencia de Datos (Docker Volumes):** Mapear `/var/lib/mysql` a un volumen del host en `docker-compose.yml` para que los datos sobrevivan al borrado de contenedores.

### ⚡ Optimización de Rendimiento
- [ ] **Refactorización de IPC:** Reemplazar el `poll()` con un `asyncio.Selector` en el Worker para eliminar el `sleep(0.01)` y reducir el uso de CPU al 0% en reposo.
- [ ] **Connection Pooling:** Implementar `aiomysql.create_pool` en el `DatabaseManager` para manejar ráfagas de conexiones concurrentes de forma eficiente.
- [ ] **Broadcast No-Bloqueante:** Envolver el `writer.drain()` en `asyncio.create_task` para que un cliente con lag no retrase el chat del resto de la sala.

### 🎓 Experiencia del Usuario (UX)
- [ ] **Pub/Sub Notifications:** Usar canales de Redis para que el Celery Worker envíe alertas de vencimiento directamente a la terminal del alumno en tiempo real.
- [ ] **Protocolo de Mensajería Robusto:** Implementar **Sequence Numbers** (IDs de mensaje) para que el cliente nunca confunda una respuesta de base de datos con otra.
- [ ] **Sanitización de Inputs:** Implementar un parser que escape el carácter `|` para evitar "inyecciones de protocolo" en los comandos enviados al servidor.

### ☁️ Infraestructura
- [ ] **Healthchecks:** Configurar `healthcheck` en el servicio de MariaDB para que el servidor y los workers esperen automáticamente a que la DB esté lista para recibir consultas.
- [ ] **Multi-stage Builds:** Optimizar el `Dockerfile` para reducir el tamaño de la imagen de 400MB a ~150MB eliminando herramientas de compilación en la capa final.