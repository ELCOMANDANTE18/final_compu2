import asyncio, os, argparse, datetime
from multiprocessing import Process, Pipe
from dotenv import load_dotenv

# Corregimos los imports para que coincidan con la ejecución desde SCEE/
from src.task import notify_task
from src.processes.auth import start_auth_process

load_dotenv()

# Diccionarios globales para gestión de conexiones
pending_auths = {}  # {username: writer}
active_sessions = {} # {writer: {user_id, username, rol, id_sala}}

def log(tag, msg):
    """Función de logging con timestamp para el tribunal de Mendoza."""
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{tag}] {msg}")

async def broadcast(message, room_id, sender_writer, sender_name):
    """Envía un mensaje a todos los miembros de una sala específica."""
    payload = f"CHAT|{sender_name}|{message}\n".encode()
    count = 0
    for writer, sess in active_sessions.items():
        if str(sess.get('id_sala')) == str(room_id) and writer != sender_writer:
            try: 
                writer.write(payload)
                await writer.drain()
                count += 1
            except: continue
    log("BROADCAST", f"Mensaje de {sender_name} enviado a {count} usuarios en Sala {room_id}")

def handle_auth_response(pipe_conn):
    """Maneja las respuestas de la DB que llegan por el Pipe."""
    if pipe_conn.poll():
        res = pipe_conn.recv()
        user, status, tipo = res.get("user_requested"), res.get("status"), res.get("type")
        
        writer = pending_auths.pop(user, None)
        if writer:
            if status == "OK":
                log("DB_RES", f"Operación {tipo} exitosa para usuario: {user}")
                if tipo == "JOIN_RES": 
                    active_sessions[writer]["id_sala"] = res.get("id_sala")
                    msg = f"JOIN_OK|{res.get('id_sala')}|{res.get('history')}\n"
                elif tipo in ["LOGIN_RES", "AUTH_RES"]:
                    active_sessions[writer] = {
                        "user_id": res.get("user_id"), 
                        "username": user, 
                        "rol": res.get("role"), 
                        "id_sala": "Ninguna"
                    }
                    msg = f"AUTH_RES|200|{user}|{res.get('role')}\n"
                else: 
                    msg = f"{tipo}|{res.get('data', 'OK')}\n"
            else:
                log("DB_ERROR", f"Fallo en {tipo} para {user}: {res.get('message')}")
                msg = f"ERROR|400|{res.get('message')}\n"
            
            writer.write(msg.encode())
            asyncio.create_task(writer.drain())

async def handle_client(reader, writer, pipe_conn):
    """Maneja la lógica de cada cliente conectado."""
    addr = writer.get_extra_info('peername')
    log("CONN", f"Nueva conexión desde {addr}")

    try:
        while True:
            data = await reader.read(1024)
            if not data: break
            
            m = data.decode().strip()
            sess = active_sessions.get(writer)
            
            if sess:
                u = sess['username']
                log("CMD", f"[{u}] -> {m}")
                
                if m.startswith("JOIN|"): 
                    pipe_conn.send({"type": "JOIN_SALA", "id_sala": m.split("|")[1], "id_user": sess['user_id'], "user": u})
                
                elif m.startswith("SEND_MSG|"):
                    msg_content = m.split("|")[1]
                    pipe_conn.send({"type": "SAVE_MSG", "id_sala": sess['id_sala'], "id_user": sess['user_id'], "msg": msg_content})
                    await broadcast(msg_content, sess['id_sala'], writer, u)
                    writer.write(b"DATA_RES|OK\n")
                    
                    # --- INTEGRACIÓN CELERY (Issue #13) ---
                    # Disparamos la tarea asincrónica para notificar la actividad
                    notify_task.delay(u, f"Mensaje enviado a sala {sess['id_sala']}")
                    log("CELERY", f"Tarea de notificación delegada para {u}")

                elif m == "GET_TASKS": 
                    pipe_conn.send({"type": "GET_TASKS", "id_sala": sess['id_sala'], "id_user": sess['user_id'], "user": u})
                
                elif m.startswith("LIST_"): 
                    pipe_conn.send({"type": m, "id_user": sess['user_id'], "user": u})
                
                elif m == "LEAVE_ROOM": 
                    log("ROOM", f"{u} salió de la sala {sess['id_sala']}")
                    sess['id_sala'] = "Ninguna"
                    writer.write(b"DATA_RES|LEAVE\n")
                
                pending_auths[u] = writer
            else:
                # Lógica de Login/Registro para clientes no autenticados
                p = m.split("|")
                if len(p) >= 3: 
                    log("AUTH", f"Intento de {p[0]} para usuario: {p[1]}")
                    pending_auths[p[1]] = writer
                    pipe_conn.send({"type": p[0], "user": p[1], "pass": p[2], "rol": p[3] if len(p)>3 else "alumno"})
            
            await writer.drain()
    except Exception as e:
        log("ERROR", f"Error en sesión de cliente: {e}")
    finally:
        sess = active_sessions.pop(writer, None)
        if sess:
            log("DISC", f"Usuario {sess['username']} desconectado.")
        else:
            log("DISC", "Cliente anónimo desconectado.")
        writer.close()
        await writer.wait_closed()

def print_banner():
    """Encabezado artístico del sistema."""
    banner = r"""
      ______   ______  ________  ________ 
     /      \ /      \|        \|        \
    |  $$$$$$|  $$$$$$| $$$$$$$$| $$$$$$$$
    | $$___\$| $$   \$| $$__    | $$__    
     \$$    \| $$     | $$  \   | $$  \   
     _\$$$$$$| $$   __| $$$$$   | $$$$$   
    |  \__| $| $$__/  | $$_____ | $$_____ 
     \$$    $$\$$    $| $$     \| $$     \
      \$$$$$$  \$$$$$$ \$$$$$$$$ \$$$$$$$$
    """
    print(banner)
    print("="*42)
    print(" SCEE - Sistema de Coordinación de Estudios")
    print(" Sede: Mendoza, Argentina 🍇📍")
    print(" Milestone 5: Celery, Redis & Docker")
    print("="*42 + "\n")

async def main():
    os.system('clear') if os.name == 'posix' else os.system('cls')
    print_banner()

    parent_conn, child_conn = Pipe()
    log("SYSTEM", "Iniciando proceso de base de datos (Worker DB)...")
    db_proc = Process(target=start_auth_process, args=(child_conn,), daemon=True)
    db_proc.start()

    loop = asyncio.get_running_loop()
    loop.add_reader(parent_conn.fileno(), handle_auth_response, parent_conn)

    server = await asyncio.start_server(lambda r, w: handle_client(r, w, parent_conn), "127.0.0.1", 5000)
    log("SERVER", f"Escuchando conexiones en 127.0.0.1:5000")

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n")
        log("SYSTEM", "Servidor SCEE finalizado manualmente.")