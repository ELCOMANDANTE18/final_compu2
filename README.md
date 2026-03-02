
---

# SCEE - Sistema de Colaboración para Equipos de Estudio 🍇

**SCEE** es una plataforma diseñada para facilitar la interacción entre alumnos y profesores, permitiendo la gestión de salas de estudio, entrega de tareas y comunicación en tiempo real.

Este proyecto es el trabajo final para la cátedra de **Computación II**.

## 👤 Autor

* **Nombre:** Victor Benjamin Gimenez

---

## 🛠️ Requisitos Previos

Para ejecutar esta aplicación de forma sencilla, se recomienda tener instalado:

* **Docker** y **Docker Compose**.
* O en su defecto, **Python 3.10+** y una instancia de **MariaDB** y **Redis**.
## Arquitectura
```
       __________________________________________________________________
      |                                                                 |
      |                      [ CLIENTES MULTI-PROTOCOLO ]               |
      |      (Python Clients: vector, messi, abel, etc.)                |
      |      Conectividad: IPv4 (127.0.0.1) e IPv6 (::1)                |
      |_________________________________________________________________|
                |                      |                       |
                | [ TCP:5001 ]         | [ TCP:5001 ]          | [ TCP:5001 ]
  ______________|______________________|_______________________|__________
 |                                                                        |
 |                 [ DOCKER PROXY / PORT MAPPING ]                        |
 |            (Mapeo de puertos Dual Stack en el Host)                    |
 |________________________________________________________________________|
         |                                           |
         v                                           v
  ________________________________________________________________________
 |                                                                        |
 |                         [ SERVIDOR PRINCIPAL ]                         |
 |                      (main_server.py / Asyncio)                        |
 |   - Dual Stack Socket (host=None) -> Escucha en [::] y [0.0.0.0]       |
 |   - Gestión asíncrona de sesiones concurrentes                         |
 |   - Lógica de Broadcast y ruteo de comandos                            |
 |   - Timezone: America/Argentina/Mendoza (GMT-3)                        |
 |________________________________________________________________________|
         |                                           |
         | [ IPC: Pipe (parent_conn) ]               | [ Broker: Redis ]
         v                                           v
  ___________________________           __________________________________
 |                           |         |                                  |
 |    [ DB WORKER PROCESS ]  |         |        [ CELERY BEAT ]           |
 |  (auth.py)               |         |      (Planificador Tareas)       |
 |   - Aislamiento de DB     |         |    - Ejecuta cada 60 seg.        |
 |___________________________|         |__________________________________|
         |                                           |
         | [ MariaDB Connection ]                    | [ Result Backend ]
         v                                           v
  ___________________________           __________________________________
 |                           |         |                                  |
 |     [ MARIADB (scee_db) ] | <------ |       [ CELERY WORKER ]          |
 |   - Volumen Persistente   |         |        (tasks.py / async)        |
 |   - Tablas: usuarios,     |         |    - Alertas de vencimientos     |
 |     mensajes, tareas      |         |    - Query: NOW() (Hora Mza)     |
 |___________________________|         |__________________________________|

```

## 🚀 Inicio Rápido (Uso Básico)

1. **Despliegue del Sistema:**
Desde la terminal en la raíz del proyecto, ejecutá:
```bash
docker-compose up --build
```


*Esto levantará el servidor, la base de datos y el sistema de notificaciones.*
2. **Conexión del Cliente:**
En una nueva terminal, ejecutá el cliente indicando tu usuario y la dirección del servidor (soporta IPv4 e IPv6):
```bash
python3 src/client.py -u tu_usuario -p tu_password --host 127.0.0.1 --port 5001
```


## ⌨️ Comandos Disponibles

Una vez dentro de la sala, podés interactuar con los siguientes comandos:

| Comando | Acción |
| --- | --- |
| `/tareas` | Lista todas las tareas pendientes y publicadas. |
| `/subir [ID]` | Permite realizar la entrega de un archivo para una tarea específica. |
| `/mis_entregas` | Muestra el estado de tus entregas enviadas. |
| `/notas` | Consulta las calificaciones y devoluciones del profesor. |
| `/borrar [ID]` | (Solo Profesores) Elimina una tarea o registro. |
| `ENTER` | Presioná Enter sin texto para salir de la aplicación de forma segura. |

> [!TIP]
> **Notificaciones:** El sistema te enviará mensajes automáticos identificados como `[📩 SISTEMA]` cuando el profesor califique un TP o cuando falten menos de 24hs para un vencimiento.
---

    