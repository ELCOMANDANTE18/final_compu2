import asyncio
import aiomysql
import os
from dotenv import load_dotenv

load_dotenv()

async def auth_process_loop(pipe_conn):
    """Proceso hijo dedicado a la seguridad y DB."""
    conn = await aiomysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME")
    )

    while True:
        await asyncio.sleep(0.01) # No saturar CPU
        if pipe_conn.poll():
            req = pipe_conn.recv()
            action = req.get("type")
            user = req.get("user")
            passwd = req.get("pass")

            async with conn.cursor() as cur:
                if action == "LOGIN":
                    await cur.execute("SELECT id, rol FROM usuarios WHERE username=%s AND password_hash=%s", (user, passwd))
                    res = await cur.fetchone()
                    if res:
                        pipe_conn.send({"status": "OK", "user_id": res[0], "user_requested": user, "role": res[1]})
                    else:
                        pipe_conn.send({"status": "ERROR", "user_requested": user, "message": "Credenciales incorrectas"})
                
                elif action == "REGISTER":
                    try:
                        rol = req.get("rol", "alumno")
                        await cur.execute("INSERT INTO usuarios (username, password_hash, rol) VALUES (%s, %s, %s)", (user, passwd, rol))
                        await conn.commit()
                        pipe_conn.send({"status": "OK", "user_requested": user, "role": rol, "message": "Registro exitoso"})
                    except Exception as e:
                        pipe_conn.send({"status": "ERROR", "user_requested": user, "message": str(e)})

def start_auth_process(pipe_conn):
    """Punto de entrada para multiprocessing."""
    try:
        asyncio.run(auth_process_loop(pipe_conn))
    except KeyboardInterrupt:
        pass