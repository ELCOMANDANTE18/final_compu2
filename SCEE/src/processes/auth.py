import asyncio
import sys
import os

async def auth_process_loop(pipe_conn):
    """Bucle principal que escucha el Pipe y despacha a la DB."""
    
    # IMPORT LOCAL: Esto rompe la dependencia circular
    # Asegúrate de que 'main_server.py' esté en la misma carpeta o en el PYTHONPATH
    from main_server import DatabaseManager
    
    db = DatabaseManager()

    # --- NUEVO: Bucle de reintento para Mendoza 🍇 ---
    # Esto evita que el contenedor falle si MariaDB aún está arrancando
    while True:
        try:
            await db.connect()
            print("[AUTH] Conexión exitosa con MariaDB.")
            break
        except Exception as e:
            print(f"[AUTH] Esperando a MariaDB... (Reintentando en 2s): {e}")
            await asyncio.sleep(2)
    # ------------------------------------------------

    while True:
        # Pequeña espera para no saturar el CPU
        await asyncio.sleep(0.01)
        
        if pipe_conn.poll():
            req = pipe_conn.recv()
            action = req.get("type")
            user = req.get("user")
            u_id = req.get("id_user") or req.get("user_id")

            try:
                if action == "LOGIN":
                    res = await db.login(user, req.get("pass"))
                    if res:
                        pipe_conn.send({
                            "status": "OK", "type": "LOGIN_RES", 
                            "user_id": res[0], "role": res[1], "user_requested": user
                        })
                    else:
                        pipe_conn.send({
                            "status": "ERROR", "type": "LOGIN_RES", 
                            "message": "Credenciales inválidas", "user_requested": user
                        })

                elif action == "REGISTER":
                    success, msg_or_id = await db.register(user, req.get("pass"), req.get("rol"))
                    if success:
                        pipe_conn.send({
                            "status": "OK", "type": "AUTH_RES", 
                            "user_requested": user, "role": req.get("rol"), "user_id": msg_or_id
                        })
                    else:
                        pipe_conn.send({
                            "status": "ERROR", "type": "AUTH_RES", 
                            "message": msg_or_id, "user_requested": user
                        })

                elif action == "CREATE_SALA":
                    await db.create_room(req.get("nombre"), req.get("descripcion"), u_id)
                    pipe_conn.send({"status": "OK", "type": "DATA_RES", "user_requested": user})

                # --- NUEVAS LÓGICAS DE BORRADO (CRUD COMPLETO) ---
                elif action == "DELETE_TASK":
                    # El DatabaseManager debe tener este método que borra en cascada
                    await db.delete_task(req.get("id_tarea"))
                    pipe_conn.send({"status": "OK", "type": "DATA_RES", "user_requested": user})

                elif action == "DELETE_SUBMISSION":
                    # El worker borra la entrega y su calificación asociada
                    await db.delete_submission(req.get("id_ent"), u_id)
                    pipe_conn.send({"status": "OK", "type": "DATA_RES", "user_requested": user})    

                elif action == "JOIN_SALA":
                    hist = await db.join_room(u_id, req.get("id_sala"))
                    if hist is not None:
                        pipe_conn.send({
                            "status": "OK", "type": "JOIN_RES", 
                            "id_sala": req.get("id_sala"), "history": hist, "user_requested": user
                        })
                    else:
                        pipe_conn.send({"status": "ERROR", "type": "DATA_RES", "message": "No existe", "user_requested": user})

                elif action in ["LIST_AVAILABLE", "LIST_MY_SALAS"]:
                    data = await db.list_rooms(u_id, action)
                    pipe_conn.send({"status": "OK", "type": "LISTA", "data": data, "user_requested": user})
                
                elif action == "SAVE_MSG":
                    await db.save_message(req.get("id_sala"), u_id, req.get("msg"))

                elif action == "CREATE_TASK":
                    async with db.conn.cursor() as cur:
                        await cur.execute(
                            "INSERT INTO tareas (id_sala, titulo, descripcion, fecha_entrega) VALUES (%s, %s, %s, %s)",
                            (int(req.get("id_sala")), req.get("titulo"), req.get("descripcion"), req.get("fecha"))
                        )
                    pipe_conn.send({"status": "OK", "type": "DATA_RES", "user_requested": user})

                elif action == "GET_TASKS":
                    if req.get("rol").lower() == "profesor":
                        async with db.conn.cursor() as cur:
                            await cur.execute("SELECT id, titulo, descripcion, fecha_entrega FROM tareas WHERE id_sala = %s", (int(req.get("id_sala")),))
                            res = await cur.fetchall()
                            data = "|".join([f"{r[0]}§{r[1]}§{r[2]}§{r[3]}" for r in res]) if res else "VACIO"
                    else:
                        data = await db.get_tasks(req.get("id_sala"), req.get("id_user"))
                    
                    pipe_conn.send({"status": "OK", "type": "TASKS_LIST", "data": data, "user_requested": user})
                
                elif action == "SAVE_SUBMISSION":
                    await db.save_submission(
                        req.get("tp_id"), 
                        req.get("id_user"), 
                        req.get("content")
                    )
                    pipe_conn.send({
                        "status": "OK", 
                        "type": "DATA_RES", 
                        "user_requested": req.get("user")
                    })   

                elif action == "LIST_SUBMISSIONS":
                    data = await db.list_submissions(req.get("id_sala"))
                    pipe_conn.send({"status": "OK", "type": "SUBMISSIONS_LIST", "data": data, "user_requested": user})

                elif action == "GRADE_SUBMISSION":
                    await db.grade_submission(req.get("s_id"), req.get("grade"))
                    pipe_conn.send({"status": "OK", "type": "DATA_RES", "user_requested": user})
                
                elif action == "GET_GRADES":
                    data = await db.get_grades(u_id)
                    pipe_conn.send({
                        "status": "OK", "type": "GRADES_LIST", 
                        "data": data, "user_requested": user
                    })        

                elif action == "GET_MY_SUBMISSIONS":
                    data = await db.get_my_submissions(u_id, req.get("id_sala"))
                    pipe_conn.send({"status": "OK", "type": "MY_SUBMISSIONS_LIST", "data": data, "user_requested": user})    

            except Exception as e:
                print(f"[WORKER ERROR] {e}")
                pipe_conn.send({"status": "ERROR", "type": "DATA_RES", "message": str(e), "user_requested": user})

def start_auth_process(pipe_conn):
    """Punto de entrada para el proceso hijo."""
    try:
        asyncio.run(auth_process_loop(pipe_conn))
    except KeyboardInterrupt:
        pass