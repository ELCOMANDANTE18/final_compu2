
---

# INFO - Decisiones de Diseño y Arquitectura 🧠

Este documento detalla las justificaciones técnicas y las decisiones de diseño tomadas para el desarrollo de **SCEE Mendoza**. El objetivo principal fue crear un sistema altamente concurrente, resiliente y modular.

## 1. Modelo de Comunicación: Sockets TCP

Se optó por el uso de **Sockets TCP** para toda la comunicación entre cliente y servidor.

* **Justificación:** Al ser un sistema de coordinación académica (donde se envían tareas y notas), la integridad de los datos es innegociable. TCP garantiza que los mensajes lleguen en orden y sin errores (con acuse de recibo), algo vital para evitar la pérdida de información crítica.

## 2. Asincronismo de I/O (Asyncio)

El servidor central (`main_server.py`) utiliza un enfoque **asíncrono**.

* **Eficiencia:** Usamos un solo hilo/proceso para manejar múltiples clientes simultáneamente mediante un *Event Loop*. Esto hace que el sistema sea extremadamente liviano y eficiente en el uso de memoria RAM comparado con un modelo basado exclusivamente en hilos.
* **Delegación Bloqueante:** Para no frenar el chat, las tareas pesadas de base de datos se delegan mediante `loop.run_in_executor`, manteniendo la fluidez de la sala.

## 3. Persistencia y Comunicación IPC (Pipes)

Se implementó un **proceso independiente** (`auth.py`) para gestionar la base de datos MariaDB.

* **Uso de Pipes:** La comunicación entre el servidor y este proceso se realiza mediante tuberías (Pipes). Esto desacopla la lógica de red de la de persistencia.
* **Integridad:** Se programó un **Borrado en Cascada manual** para asegurar que la eliminación de registros superiores (como una Sala) limpie correctamente los datos dependientes (Notas, Entregas, Tareas).

## 4. Escalabilidad y Configuración

El sistema fue diseñado pensando en su despliegue en diferentes entornos:

* **Variables de Entorno (.env):** El uso de archivos de configuración y argumentos de línea de comandos permite mover el servidor a cualquier otra máquina de la red fácilmente, sin necesidad de modificar el código fuente.
* **Dockerización:** La orquestación con `docker-compose` garantiza que las dependencias (MariaDB, Redis) se levanten automáticamente con la configuración correcta.

## 5. Monitoreo y Redes Modernas

* **Celery + Redis:** Un worker independiente fiscaliza la base de datos cada 60 segundos para emitir alertas de vencimiento proactivas.
* **Dual-Stack (IPv4/IPv6):** El cliente utiliza `socket.getaddrinfo`, garantizando compatibilidad total con redes IPv4 convencionales y redes IPv6 modernas.

---