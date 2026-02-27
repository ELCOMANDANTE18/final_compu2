import os
import asyncio
from celery import Celery
from dotenv import load_dotenv
from datetime import datetime

# Importamos tu lógica de persistencia (Ruta raíz para Docker)
from main_server import DatabaseManager

load_dotenv()

app = Celery('scee_tasks',
             broker=os.getenv("CELERY_BROKER_URL"),
             backend=os.getenv("CELERY_RESULT_BACKEND"))

# --- CONFIGURACIÓN DE LA AGENDA (Faltaba esto) ---
app.conf.beat_schedule = {
    'revisar-vencimientos-cada-minuto': {
        'task': 'tasks.check_task_deadlines',
        'schedule': 60.0, # Se ejecuta cada minuto
    },
}
app.conf.timezone = 'America/Argentina/Mendoza'

db = DatabaseManager()

async def run_check():
    """Lógica de verificación de vencimientos con reintento inicial."""
    # Bucle de espera para que el worker no muera si la DB está arrancando
    while True:
        try:
            await db.connect()
            break
        except Exception:
            print("⏳ [WORKER TAREAS] Esperando a MariaDB para revisar vencimientos...")
            await asyncio.sleep(3)

    try:
        async with db.conn.cursor() as cur:
            # Query para detectar tareas que vencieron en el último minuto
            query = """
                SELECT t.titulo, s.nombre 
                FROM tareas t 
                JOIN salas s ON t.id_sala = s.id
                WHERE t.fecha_entrega <= NOW() 
                AND t.fecha_entrega > DATE_SUB(NOW(), INTERVAL 1 MINUTE)
            """
            await cur.execute(query)
            vencidas = await cur.fetchall()
            
            if vencidas:
                for t, s in vencidas:
                    print(f"⚠️  [ALERTA] La tarea '{t}' de la sala '{s}' ha VENCIDO ahora.")
                return f"Alertas enviadas: {len(vencidas)}"
            else:
                print(f"✅ [CELERY BEAT] {datetime.now().strftime('%H:%M')} - Sincronizado. Sin vencimientos.")
                return "OK"
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