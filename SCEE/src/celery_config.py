from celery import Celery

# Configuramos Celery usando Redis como Broker (el cartero)
app = Celery(
    'scee_tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0' # El backend sirve para guardar resultados si los necesitáramos
)

# Configuraciones extra para que sea compatible con tu sistema
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Argentina/Mendoza', # Tu zona horaria
    enable_utc=True,
)