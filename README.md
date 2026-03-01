
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

    