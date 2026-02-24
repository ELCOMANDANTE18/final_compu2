import os
import time
import datetime
from celery import Celery

# --- CAMBIO CLAVE: Usar la variable de entorno REDIS_URL ---
redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = Celery(
    'scee_tasks',
    broker=redis_url,
    backend=redis_url
)

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