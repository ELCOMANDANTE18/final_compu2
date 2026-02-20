import asyncio
import aiomysql
import os
from dotenv import load_dotenv

load_dotenv()

async def auth_process_loop(pipe_conn):
    conn = await aiomysql.connect(
        host=os.getenv("DB_HOST"), port=3306,
        user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME")
    )

    while True:
        await asyncio.sleep(0.01)
        if pipe_conn.poll():
            req = pipe_conn.recv()
            action = req.get("type")
            user = req.get("user")
            id_user = req.get("id_user")

            async with conn.cursor() as cur:
                # --- AUTENTICACIÓN ---
                if action == "LOGIN":
                    await cur.execute("SELECT id, rol FROM usuarios WHERE username=%s AND password_hash=%s", (user, req.get("pass")))
                    res = await cur.fetchone()
                    if res: pipe_conn.send({"status": "OK", "user_id": res[0], "user_requested": user, "role": res[1]})
                    else: pipe_conn.send({"status": "ERROR", "user_requested": user, "message": "Credenciales incorrectas"})
                
                elif action == "REGISTER":
                    try:
                        rol = req.get("rol", "alumno")
                        await cur.execute("INSERT INTO usuarios (username, password_hash, rol) VALUES (%s, %s, %s)", (user, req.get("pass"), rol))
                        await conn.commit()
                        pipe_conn.send({"status": "OK", "user_requested": user, "role": rol, "user_id": cur.lastrowid})
                    except Exception as e: pipe_conn.send({"status": "ERROR", "user_requested": user, "message": str(e)})

                # --- GESTIÓN DE SALAS FILTRADAS ---
                elif action == "LIST_AVAILABLE":
                    # Salas donde el usuario NO está
                    query = "SELECT id, nombre FROM salas WHERE id NOT IN (SELECT id_sala FROM miembros_sala WHERE id_usuario = %s)"
                    await cur.execute(query, (id_user,))
                    res = await cur.fetchall()
                    data = ",".join([f"{r[0]}:{r[1]}" for r in res]) if res else "VACIO"
                    pipe_conn.send({"status": "OK", "type": "LIST_RES", "data": data, "user_requested": user})

                elif action == "LIST_MY_SALAS":
                    # Salas donde el usuario SÍ está
                    query = "SELECT s.id, s.nombre FROM salas s JOIN miembros_sala ms ON s.id = ms.id_sala WHERE ms.id_usuario = %s"
                    await cur.execute(query, (id_user,))
                    res = await cur.fetchall()
                    data = ",".join([f"{r[0]}:{r[1]}" for r in res]) if res else "VACIO"
                    pipe_conn.send({"status": "OK", "type": "MY_SALAS_RES", "data": data, "user_requested": user})

                elif action == "CREATE_SALA":
                    try:
                        await cur.execute("INSERT INTO salas (nombre, id_creador) VALUES (%s, %s)", (req.get("nombre"), req.get("id_creador")))
                        await conn.commit()
                        pipe_conn.send({"status": "OK", "type": "SALA_CREATED", "user_requested": user})
                    except Exception as e: pipe_conn.send({"status": "ERROR", "message": str(e), "user_requested": user})

                elif action == "JOIN_SALA":
                    try:
                        await cur.execute("INSERT IGNORE INTO miembros_sala (id_usuario, id_sala) VALUES (%s, %s)", (id_user, req.get("id_sala")))
                        await conn.commit()
                        pipe_conn.send({"status": "OK", "type": "JOIN_RES", "id_sala": req.get("id_sala"), "user_requested": user})
                    except Exception as e: pipe_conn.send({"status": "ERROR", "message": str(e), "user_requested": user})

def start_auth_process(pipe_conn):
    try: asyncio.run(auth_process_loop(pipe_conn))
    except KeyboardInterrupt: pass