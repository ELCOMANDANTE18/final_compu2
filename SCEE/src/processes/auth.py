import asyncio
import sys
import os

async def auth_process_loop(pipe_conn):
    """Bucle principal que escucha el Pipe y despacha a la DB."""
    
    # IMPORT LOCAL: Esto rompe la dependencia circular
    from src.main_server import DatabaseManager
    
    db = DatabaseManager()
    await db.connect()

    while True:
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

                elif action == "JOIN_SALA":
                    hist = await db.join_room(u_id, req.get("id_sala"))
                    if hist is not None:
                        pipe_conn.send({
                            "status": "OK", "type": "JOIN_RES", 
                            "id_sala": req.get("id_sala"), "history": hist, "user_requested": user
                        })
                    else:
                        pipe_conn.send({"status": "ERROR", "type": "DATA_RES", "message": "No existe", "user_requested": user})

                elif action.startswith("LIST_"):
                    data = await db.list_rooms(u_id, action)
                    pipe_conn.send({"status": "OK", "type": "LISTA", "data": data, "user_requested": user})
                
                elif action == "SAVE_MSG":
                    await db.save_message(req.get("id_sala"), u_id, req.get("msg"))

                elif action == "GET_TASKS":
                    data = await db.get_tasks(req.get("id_sala"))
                    pipe_conn.send({"status": "OK", "type": "TASKS_LIST", "data": data, "user_requested": user})

            except Exception as e:
                print(f"[WORKER ERROR] {e}")
                pipe_conn.send({"status": "ERROR", "type": "DATA_RES", "message": str(e), "user_requested": user})

def start_auth_process(pipe_conn):
    """Punto de entrada para el proceso hijo."""
    try:
        asyncio.run(auth_process_loop(pipe_conn))
    except KeyboardInterrupt:
        pass