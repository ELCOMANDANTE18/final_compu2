import time
import datetime
from celery import Celery

# 1. Configuración de la instancia de Celery
# 'redis://localhost:6379/0' indica que usamos la base de datos 0 de Redis como broker.
app = Celery(
    'scee_tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# 2. Definición de la tarea genérica (notify_task)
@app.task(name="task.notify_task")
def notify_task(usuario, detalle):
    """
    Simula el envío de una notificación asincrónica.
    Esta tarea se ejecuta en el Worker, no en el servidor principal.
    """
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    print(f"\n[CELERY WORKER] [{timestamp}] 📬 Iniciando notificación para: {usuario}")
    print(f"[CELERY WORKER] Detalle: {detalle}")
    
    # Simulamos una carga de trabajo (ej: envío de mail o push)
    time.sleep(3) 
    
    print(f"[CELERY WORKER] ✅ Notificación completada con éxito.\n")
    return f"Notificación enviada a {usuario}"