import os
import asyncio
from celery import Celery
from dotenv import load_dotenv
from datetime import datetime

# Importamos tu lógica de persistencia
from main_server import DatabaseManager

load_dotenv()

# Colores para la consola
YELLOW = "\033[33m"
RED = "\033[91m"
RESET = "\033[0m"

app = Celery('scee_tasks',
             broker=os.getenv("CELERY_BROKER_URL"),
             backend=os.getenv("CELERY_RESULT_BACKEND"))

app.conf.beat_schedule = {
    'revisar-vencimientos-cada-minuto': {
        'task': 'tasks.check_task_deadlines',
        'schedule': float(os.getenv("TASK_CHECK_INTERVAL", 60.0)), 
    },
}
app.conf.timezone = 'America/Argentina/Mendoza'

db = DatabaseManager()

async def run_check():
    """Lógica de verificación de vencimientos y recordatorios de 24hs."""
    while True:
        try:
            await db.connect()
            break
        except Exception:
            print("⏳ [WORKER TAREAS] Esperando a MariaDB...")
            await asyncio.sleep(3)

    try:
        async with db.conn.cursor() as cur:
            # 1. Tareas VENCIDAS (Todas las que ya pasaron la fecha)
            query_vencidas = """
                SELECT t.titulo, s.nombre 
                FROM tareas t 
                JOIN salas s ON t.id_sala = s.id
                WHERE t.fecha_entrega <= NOW()
            """
            await cur.execute(query_vencidas)
            vencidas = await cur.fetchall()
            
            if vencidas:
                for t, s in vencidas:
                    # Alerta en ROJO para tareas que ya expiraron
                    print(f"{RED}❌ [ALERTA] La tarea '{t}' de la sala '{s}' está VENCIDA.{RESET}")

            # 2. Tareas PRÓXIMAS (Las que vencen en las próximas 24hs)
            query_proximas = """
                SELECT titulo, fecha_entrega 
                FROM tareas 
                WHERE fecha_entrega BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL 1 DAY)
            """
            await cur.execute(query_proximas)
            proximas = await cur.fetchall()

            if proximas:
                for t in proximas:
                    # Alerta en AMARILLO para recordatorios
                    print(f"{YELLOW}⚠️  [RECORDATORIO] La tarea '{t[0]}' vence pronto ({t[1]}).{RESET}")

            # Log de control para el administrador del servidor
            if not vencidas and not proximas:
                print(f"✅ [CELERY BEAT] {datetime.now().strftime('%H:%M')} - Sin tareas críticas.")
            
            return f"Vencidas: {len(vencidas)} | Próximas: {len(proximas)}"

    except Exception as e:
        print(f"❌ [WORKER ERROR] {e}")
    finally:
        if db.conn:
            db.conn.close()

@app.task(name="tasks.check_task_deadlines")
def check_task_deadlines():
    """Punto de entrada para Celery."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(run_check())