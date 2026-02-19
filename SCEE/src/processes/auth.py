import asyncio
import aiomysql
import os
from dotenv import load_dotenv

load_dotenv()

async def auth_process_loop(pipe_conn):
    """Bucle infinito de validación asíncrona."""
    print("[AUTH] Conectando a MariaDB...")
    try:
        conn = await aiomysql.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME")
        )
        print("[AUTH] Conexión establecida con éxito.")

        while True:
            # Usamos un pequeño sleep para no incinerar la CPU en el while True
            await asyncio.sleep(0.01)
            
            if pipe_conn.poll():
                request = pipe_conn.recv()
                user = request.get('user')
                passwd = request.get('pass')

                async with conn.cursor() as cur:
                    sql = "SELECT username, rol FROM usuarios WHERE username=%s AND password_hash=%s"
                    await cur.execute(sql, (user, passwd))
                    result = await cur.fetchone()

                if result:
                    response = {
                        "status": "OK", 
                        "user_requested": user, 
                        "role": result[1]
                    }
                else:
                    response = {
                        "status": "ERROR", 
                        "user_requested": user, 
                        "message": "No existís en la DB"
                    }
                
                # Devolvemos el resultado por el "pasaplatos" (Pipe)
                pipe_conn.send(response)

    except Exception as e:
        print(f"[AUTH] Error fatal: {e}")
    finally:
        if 'conn' in locals(): conn.close()

def start_auth_process(pipe_conn):
    """Punto de entrada síncrono para multiprocessing."""
    try:
        asyncio.run(auth_process_loop(pipe_conn))
    except KeyboardInterrupt:
        pass