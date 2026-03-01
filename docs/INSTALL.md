
---

# INSTALL - Guía de Instalación y Despliegue 🛠️

Este documento describe los pasos exactos para clonar, configurar y ejecutar el ecosistema de **SCEE Mendoza**.

## 1. Clonar y Acceder al Proyecto

Obtené el código fuente y accedé al directorio del proyecto:

```bash
git clone https://github.com/ELCOMANDANTE18/final_compu2
cd SCEE
```

## 2. Despliegue del Backend (Docker)

Antes de ejecutar el cliente, es necesario levantar el servidor y los servicios de soporte (MariaDB, Redis, Celery).

Desde la carpeta `SCEE`, ejecutá:

```bash
docker-compose up --build
```

*Este comando dejará el servidor operativo y listo para recibir conexiones en segundo plano.*

## 3. Configuración del Cliente (Entorno Virtual)

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



## 4. Secuencia de Uso del Cliente

Con el entorno activo, podés probar las distintas funciones de acceso y registro:

* **Conexión estándar (Alumno):**
```bash
python3 client.py -u abel -p 1234
```


* **Conexión con otros usuarios:**
```bash
python3 client.py -u messi -p 10
python3 client.py -u benja -p 1234
```


* **Registro de nuevo Profesor:**
```bash
python3 client.py --register -u Juan -p 1234 -r profesor
```


* **Conexión mediante IPv6:**
```bash
python3 client.py -u abel -p 1234 --host ::1 --port 5001
```



---

> [!TIP]
> Recordá que siempre se debe iniciar primero el comando de **Docker** y, una vez que los servicios estén activos, proceder con el uso del `client.py` dentro del entorno virtual.

---