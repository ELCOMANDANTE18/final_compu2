import asyncio
import sys
import os
from src.database.database_logic import DatabaseManager

# Agregamos el path para que el proceso encuentre database_logic en la raíz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def auth_process_loop(pipe_conn):
    """Bucle principal que escucha el Pipe y despacha a la DB."""
    db = DatabaseManager()
    await db.connect()

    while True:
        await asyncio.sleep(0.01)
        if pipe_conn.poll():
            req = pipe_conn.recv()
            action = req.get("type")
            user = req.get("user")
            # Unificamos la captura del ID de usuario
            u_id = req.get("id_user") or req.get("user_id")

            try:
                # --- DESPACHO DE ACCIONES A DatabaseManager ---
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

                elif action == "GET_TASKS":
                    # Usamos el nuevo método con delimitador robusto '§'
                    data = await db.get_tasks(req.get("id_sala"))
                    pipe_conn.send({
                        "status": "OK", "type": "TASKS_LIST", 
                        "data": data, "user_requested": user
                    })

                elif action == "SAVE_MSG":
                    # Persistencia delegada
                    await db.save_message(req.get("id_sala"), u_id, req.get("msg"))

                elif action == "JOIN_SALA":
                    # El manager se encarga de validar existencia y traer historial
                    hist = await db.join_room(u_id, req.get("id_sala"))
                    if hist is not None:
                        pipe_conn.send({
                            "status": "OK", "type": "JOIN_RES", 
                            "id_sala": req.get("id_sala"), "history": hist, "user_requested": user
                        })
                    else:
                        pipe_conn.send({
                            "status": "ERROR", "type": "DATA_RES", 
                            "message": "La sala no existe", "user_requested": user
                        })

                elif action in ["LIST_AVAILABLE", "LIST_MY_SALAS"]:
                    data = await db.list_rooms(u_id, action)
                    pipe_conn.send({
                        "status": "OK", "type": "LISTA", 
                        "data": data, "user_requested": user
                    })

                elif action == "REGISTER":
                    # Lógica de registro delegada
                    success, msg_or_id = await db.register(user, req.get("pass"), req.get("rol"))
                    if success:
                        pipe_conn.send({
                            "status": "OK", 
                            "type": "REGISTER_RES", # <--- CAMBIADO PARA EL 201
                            "user_requested": user, 
                            "role": req.get("rol"), 
                            "user_id": msg_or_id
                        })
                    else:
                        pipe_conn.send({
                            "status": "ERROR", 
                            "type": "REGISTER_RES", # <--- CAMBIADO
                            "message": msg_or_id, 
                            "user_requested": user
                        })

                elif action == "CREATE_SALA":
                    await db.create_room(req.get("nombre"), req.get("descripcion"), u_id)
                    pipe_conn.send({"status": "OK", "type": "DATA_RES", "user_requested": user})

            except Exception as e:
                print(f"[DB-WORKER ERROR] Fallo en {action}: {e}")
                pipe_conn.send({
                    "status": "ERROR", "type": "DATA_RES", 
                    "message": "Error interno de base de datos", "user_requested": user
                })

def start_auth_process(pipe_conn):
    """Punto de entrada para el proceso hijo (IPC)."""
    try:
        asyncio.run(auth_process_loop(pipe_conn))
    except KeyboardInterrupt:
        pass