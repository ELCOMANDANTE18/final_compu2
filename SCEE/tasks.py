import os
from celery import Celery
from dotenv import load_dotenv
import asyncio

# Importamos tu lógica de persistencia
# En tasks.py (línea 8 aprox), cambialo a esto:
from src.main_server import DatabaseManager

# 1. Cargamos el .env ANTES de cualquier otra cosa
load_dotenv()

# 2. Obtenemos la URL y ponemos un "fallback" por si el .env falla
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# 3. Inicializamos la App con la configuración explícita
app = Celery('scee_tasks', 
             broker=broker_url,
             backend=result_backend)

# ... resto de tu código (configuración de Beat y tareas)

# Configuración del Beat (Programación automática)
app.conf.beat_schedule = {
    'revisar-vencimientos-cada-minuto': {
        'task': 'tasks.check_task_deadlines',
        'schedule': 60.0, # Segundos (podes usar crontab para horas específicas)
    },
}
app.conf.timezone = 'America/Argentina/Mendoza'

@app.task
def check_task_deadlines():
    """Busca tareas próximas a vencer en MariaDB."""
    loop = asyncio.get_event_loop()
    db = DatabaseManager()
    
    async def run_check():
        await db.connect()
        async with db.conn.cursor() as cur:
            # Seleccionamos tareas que vencen en las próximas 24hs
            query = """
                SELECT t.titulo, t.fecha_entrega, s.nombre 
                FROM tareas t
                JOIN salas s ON t.id_sala = s.id
                WHERE t.fecha_entrega BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL 1 DAY)
            """
            await cur.execute(query)
            return await cur.fetchall()

    vencimientos = loop.run_until_complete(run_check())
    
    if vencimientos:
        print(f"\n📢 [CELERY BEAT] Se encontraron {len(vencimientos)} vencimientos próximos:")
        for v in vencimientos:
            print(f"   - Tarea: {v[0]} | Sala: {v[2]} | Vence: {v[1]}")
    else:
        print("✅ [CELERY BEAT] No hay vencimientos próximos.")