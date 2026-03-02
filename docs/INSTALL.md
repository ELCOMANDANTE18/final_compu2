
---

# INSTALL - Guía de Instalación y Despliegue 🛠️

Este documento describe los pasos exactos para clonar, configurar y ejecutar el ecosistema de **SCEE Mendoza**.

## 1. Clonar y Acceder al Proyecto

Obtené el código fuente y accedé al directorio del proyecto:

```bash
git clone https://github.com/ELCOMANDANTE18/final_compu2
cd final_compu2/SCEE
```

## 2. Configuración de Variables de Entorno (.env)

Para que los servicios se comuniquen, debés crear un archivo `.env` en la raíz de la carpeta `SCEE`. **No lo muevas a la carpeta `src/**`, ya que Docker lo busca en la raíz para configurar los contenedores.

Copiá el ejemplo o creá el archivo manualmente:

```bash
cp .env-example .env
```

Asegurate de que el contenido sea el siguiente para la **Sede Mendoza 🍇**:

```ini
# Configuración para Sede Mendoza 🍇
DB_HOST=db
DB_NAME=scee_db
DB_USER=root
DB_PASSWORD=1234

REDIS_HOST=redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# El puerto del servidor sigue siendo el mismo
SERVER_PORT=5001
```

## 3. Despliegue del Backend (Docker)

Antes de ejecutar el cliente, es necesario levantar el servidor y los servicios de soporte (MariaDB, Redis, Celery).

Desde la carpeta `SCEE`, ejecutá:

```bash
sudo docker-compose up --build
```

*Este comando dejará el servidor operativo y listo para recibir conexiones en segundo plano.*

## 4. Configuración del Cliente (Entorno Virtual)

Para el cliente, utilizaremos un entorno virtual para no instalar librerías de forma global en el sistema.

1. **Crear el entorno virtual:**

```bash
python3 -m venv env
```

2. **Activar el entorno:**

```bash
source env/bin/activate
```

3. **Instalar dependencias necesarias:**

```bash
pip install -r requirements.txt
```

## 5. Secuencia de Uso del Cliente

Con el entorno activo y los archivos en su nueva ubicación, ejecutá el cliente desde la raíz de `SCEE`:

* **Conexión estándar (Alumno):**

```bash
python3 src/client.py -u benja -p 1234
```

* **Conexión con otros usuarios:**

```bash
python3 src/client.py -u messi -p 10
python3 src/client.py -u abel -p 1234
```

* **Registro de nuevo Profesor:**

```bash
python3 src/client.py --register -u Juan -p 1234 -r profesor
```

* **Conexión mediante IPv6 (Dual Stack):**

```bash
python3 src/client.py -u benja -p 1234 --host ::1 --port 5001
```

---

> [!TIP]
> Si realizás cambios en el archivo `init.sql`, recordá limpiar los volúmenes de Docker antes de reiniciar para que MariaDB tome los nuevos datos: `sudo docker-compose down -v`.

---
