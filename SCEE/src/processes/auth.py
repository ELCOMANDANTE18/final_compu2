import asyncio, aiomysql, os
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
            act, user, id_u = req.get("type"), req.get("user"), req.get("id_user")

            async with conn.cursor() as cur:
                try:
                    # --- GESTIÓN DE TPs (Issue #12) ---
                    if act == "GET_TASKS":
                        s_id = int(req.get("id_sala"))
                        # Escapamos los % con %% para que Python no los confunda
                        query = "SELECT titulo, descripcion, DATE_FORMAT(fecha_entrega, '%%Y-%%m-%%d %%H:%%i') FROM tareas WHERE id_sala = %s"
                        await cur.execute(query, (s_id,))
                        res = await cur.fetchall()
                        # Usamos § como separador seguro para no rompernos con los :
                        data = "|".join([f"{r[0]}§{r[1]}§{r[2]}" for r in res]) if res else "VACIO"
                        pipe_conn.send({"status": "OK", "type": "TASKS_LIST", "data": data, "user_requested": user})

                    elif act == "SAVE_MSG":
                        await cur.execute("INSERT INTO mensajes (id_sala, id_usuario, contenido) VALUES (%s, %s, %s)", 
                                        (int(req.get("id_sala")), int(id_u), req.get("msg")))
                        await conn.commit()

                    elif act == "JOIN_SALA":
                        s_id = int(req.get("id_sala"))
                        await cur.execute("SELECT id FROM salas WHERE id = %s", (s_id,))
                        if not await cur.fetchone():
                            pipe_conn.send({"status": "ERROR", "type": "DATA_RES", "message": "Sala inexistente", "user_requested": user})
                            continue
                        await cur.execute("INSERT IGNORE INTO miembros_sala (id_usuario, id_sala) VALUES (%s, %s)", (int(id_u), s_id))
                        await conn.commit()
                        await cur.execute("SELECT u.username, m.contenido FROM mensajes m JOIN usuarios u ON m.id_usuario = u.id WHERE m.id_sala = %s ORDER BY m.fecha ASC LIMIT 20", (s_id,))
                        h_res = await cur.fetchall()
                        h_data = "|".join([f"{r[0]}:{r[1]}" for r in h_res]) if h_res else "VACIO"
                        pipe_conn.send({"status": "OK", "type": "JOIN_RES", "id_sala": s_id, "history": h_data, "user_requested": user})

                    elif act == "LOGIN":
                        await cur.execute("SELECT id, rol FROM usuarios WHERE username=%s AND password_hash=%s", (user, req.get("pass")))
                        res = await cur.fetchone()
                        if res: pipe_conn.send({"status": "OK", "type": "LOGIN_RES", "user_id": res[0], "user_requested": user, "role": res[1]})
                        else: pipe_conn.send({"status": "ERROR", "type": "LOGIN_RES", "message": "Credenciales incorrectas", "user_requested": user})

                    elif act in ["LIST_AVAILABLE", "LIST_MY_SALAS"]:
                        cond = "NOT IN" if act == "LIST_AVAILABLE" else "IN"
                        q = f"SELECT id, nombre FROM salas WHERE id {cond} (SELECT id_sala FROM miembros_sala WHERE id_usuario = %s)"
                        await cur.execute(q, (int(id_u),))
                        r_list = await cur.fetchall()
                        pipe_conn.send({"status": "OK", "type": "LISTA", "data": ",".join([f"{r[0]}:{r[1]}" for r in r_list]) if r_list else "VACIO", "user_requested": user})

                except Exception as e:
                    print(f"[AUTH ERROR] Fallo en {act}: {e}")
                    pipe_conn.send({"status": "ERROR", "type": "DATA_RES", "message": "Error en base de datos", "user_requested": user})

def start_auth_process(pipe_conn):
    try: asyncio.run(auth_process_loop(pipe_conn))
    except KeyboardInterrupt: pass