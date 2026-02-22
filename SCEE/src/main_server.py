import asyncio, os, argparse, datetime
from multiprocessing import Process, Pipe
from dotenv import load_dotenv

from src.processes.auth import start_auth_process

load_dotenv()
pending_auths, active_sessions = {}, {}

def log(tag, msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{tag}] {msg}")

async def broadcast(message, room_id, sender_writer, sender_name):
    payload = f"CHAT|{sender_name}|{message}\n".encode()
    for writer, sess in active_sessions.items():
        if str(sess.get('id_sala')) == str(room_id) and writer != sender_writer:
            try: writer.write(payload); await writer.drain()
            except: continue

def handle_auth_response(pipe_conn):
    if pipe_conn.poll():
        res = pipe_conn.recv()
        user, status, tipo = res.get("user_requested"), res.get("status"), res.get("type")
        writer = pending_auths.pop(user, None)
        if writer:
            if status == "OK":
                if tipo == "JOIN_RES": 
                    active_sessions[writer]["id_sala"] = res.get("id_sala")
                    msg = f"JOIN_OK|{res.get('id_sala')}|{res.get('history')}\n"
                elif tipo in ["LOGIN_RES", "AUTH_RES"]:
                    active_sessions[writer] = {"user_id": res.get("user_id"), "username": user, "rol": res.get("role"), "id_sala": "Ninguna"}
                    msg = f"AUTH_RES|200|{user}|{res.get('role')}\n"
                else: msg = f"{tipo}|{res.get('data', 'OK')}\n"
            else: msg = f"ERROR|400|{res.get('message')}\n"
            writer.write(msg.encode()); asyncio.create_task(writer.drain())

async def handle_client(reader, writer, pipe_conn):
    try:
        while True:
            data = await reader.read(1024)
            if not data: break
            m = data.decode().strip(); sess = active_sessions.get(writer)
            if sess:
                u = sess['username']
                if m.startswith("JOIN|"): pipe_conn.send({"type": "JOIN_SALA", "id_sala": m.split("|")[1], "id_user": sess['user_id'], "user": u})
                elif m.startswith("SEND_MSG|"):
                    pipe_conn.send({"type": "SAVE_MSG", "id_sala": sess['id_sala'], "id_user": sess['user_id'], "msg": m.split("|")[1]})
                    await broadcast(m.split("|")[1], sess['id_sala'], writer, u); writer.write(b"DATA_RES|OK\n")
                elif m == "GET_TASKS": pipe_conn.send({"type": "GET_TASKS", "id_sala": sess['id_sala'], "id_user": sess['user_id'], "user": u})
                elif m.startswith("LIST_"): pipe_conn.send({"type": m, "id_user": sess['user_id'], "user": u})
                elif m == "LEAVE_ROOM": sess['id_sala'] = "Ninguna"; writer.write(b"DATA_RES|LEAVE\n")
                pending_auths[u] = writer
            else:
                p = m.split("|")
                if len(p) >= 3: pending_auths[p[1]] = writer; pipe_conn.send({"type": p[0], "user": p[1], "pass": p[2], "rol": p[3] if len(p)>3 else "alumno"})
            await writer.drain()
    finally:
        u = active_sessions.pop(writer, None); writer.close()

def print_banner():
    """Imprime el encabezado visual del sistema SCEE."""
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
    print("="*42 + "\n")

async def main():
    # Limpieza de terminal y bienvenida
    os.system('clear') if os.name == 'posix' else os.system('cls')
    print_banner()

    # Configuración de IPC (Pipes) y Proceso de Base de Datos
    parent_conn, child_conn = Pipe()
    db_proc = Process(target=start_auth_process, args=(child_conn,), daemon=True)
    db_proc.start()

    # Monitoreo del Pipe dentro del loop de asyncio
    loop = asyncio.get_running_loop()
    loop.add_reader(parent_conn.fileno(), handle_auth_response, parent_conn)

    # Inicio del Servidor de Sockets
    server = await asyncio.start_server(lambda r, w: handle_client(r, w, parent_conn), "127.0.0.1", 5000)
    
    # La línea que necesitabas con el timestamp dinámico:
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [SERVER] Escuchando en 127.0.0.1:5000")

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Servidor SCEE finalizado manualmente.")

