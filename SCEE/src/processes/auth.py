import multiprocessing
import time

def auth_process_loop(pipe_conn):
    """
    Este es el bucle principal del proceso hijo.
    Se ejecuta de forma independiente al servidor principal.
    """
    print("[AUTH] Proceso de Autenticación iniciado.")
    
    try:
        while True:
            # El proceso se queda esperando que llegue algo por el Pipe (es bloqueante acá)
            if pipe_conn.poll(): # Revisa si hay algo para leer
                request = pipe_conn.recv()
                print(f"[AUTH] Recibido pedido de validación para: {request.get('user')}")
                
                # Simulamos una validación (luego usaremos aiomysql)
                time.sleep(1) # Simula latencia de base de datos
                
                # Respuesta de ejemplo
                response = {"status": "OK", "message": "Bienvenido al sistema"}
                pipe_conn.send(response)
                
    except KeyboardInterrupt:
        print("[AUTH] Proceso de autenticación finalizado.")


#Todo esto no tiene sentido sin db 


        

