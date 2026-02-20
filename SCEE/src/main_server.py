import asyncio
import os
import argparse
from multiprocessing import Process, Pipe
from dotenv import load_dotenv
from processes.auth import start_auth_process

load_dotenv()

# --- ESTADO GLOBAL DEL SERVIDOR ---
pending_auths = {}   # {username: writer}
active_sessions = {} # {writer: {user_id, username, rol, id_sala, auth}}

def get_args():
    parser = argparse.ArgumentParser(description="SCEE Server - Mendoza")
    parser.add_argument("-p", "--port", type=int, default=os.getenv("SERVER_PORT", 5000))
    parser.add_argument("-b", "--host", default=os.getenv("SERVER_HOST", "127.0.0.1"))
    return parser.parse_args()

def handle_auth_response(pipe_conn):
    """Callback que sincroniza la respuesta de la DB con el socket del cliente."""
    if pipe_conn.poll():
        response = pipe_conn.recv()
        username = response.get("user_requested")
        status = response.get("status")
        writer = pending_auths.pop(username, None)
        
        if writer:
            tipo = response.get("type")
            if status == "OK":
                if tipo == "LIST_RES":
                    msg = f"SALAS_LIST|{response.get('data')}\n"
                elif tipo == "JOIN_RES":
                    if writer in active_sessions:
                        active_sessions[writer]["id_sala"] = response.get("id_sala")
                    msg = f"JOIN_OK|Te uniste a la sala {response.get('id_sala')}\n"
                elif tipo == "SALA_CREATED":
                    msg = "OK|201|Sala creada exitosamente\n"
                else: # LOGIN / REGISTER exitoso
                    active_sessions[writer] = {
                        "user_id": response.get("user_id"),
                        "username": username,
                        "rol": response.get("role"),
                        "auth": True,
                        "id_sala": "Ninguna"
                    }
                    # Formato sincronizado con el cliente: AUTH_RES|200|User|Rol
                    msg = f"AUTH_RES|200|{username}|{response.get('role')}\n"
                    print(f"--- [SESIÓN] {username} inició sesión como {response.get('role')} ---")
            else:
                msg = f"ERROR|401|{response.get('message')}\n"
            
            writer.write(msg.encode())
            asyncio.create_task(writer.drain())

async def handle_client(reader, writer, pipe_conn):
    addr = writer.get_extra_info('peername')
    print(f"[+] CONEXIÓN ENTRANTE: {addr}")

    try:
        while True:
            data = await reader.read(1024)
            if not data: break
            
            message = data.decode().strip()
            session = active_sessions.get(writer)

            if not session:
                # --- FASE DE IDENTIFICACIÓN ---
                parts = message.split("|")
                if len(parts) >= 3:
                    cmd, user = parts[0], parts[1]
                    pending_auths[user] = writer
                    if cmd == "LOGIN":
                        pipe_conn.send({"type": "LOGIN", "user": user, "pass": parts[2]})
                    elif cmd == "REGISTER" and len(parts) == 4:
                        pipe_conn.send({"type": "REGISTER", "user": user, "pass": parts[2], "rol": parts[3]})
                else:
                    writer.write("ERROR|403|Identifícate primero\n".encode())
            else:
                # --- COMANDOS DE NEGOCIO (RBAC) ---
                if message == "LIST_SALAS":
                    pipe_conn.send({"type": "LIST_SALAS", "user": session['username']})
                    pending_auths[session['username']] = writer
                
                elif message.startswith("CREATE_SALA|"):
                    if session['rol'].lower() == 'alumno':
                        print(f"[!] DENEGADO: {session['username']} intentó crear sala.")
                        writer.write("ERROR|405|Solo profesores pueden crear salas\n".encode())
                    else:
                        nom = message.split("|")[1]
                        pipe_conn.send({"type": "CREATE_SALA", "nombre": nom, "id_creador": session['user_id'], "user": session['username']})
                        pending_auths[session['username']] = writer

                elif message.startswith("JOIN|"):
                    id_s = message.split("|")[1]
                    pipe_conn.send({"type": "JOIN_SALA", "id_sala": id_s, "id_user": session['user_id'], "user": session['username']})
                    pending_auths[session['username']] = writer
                
                elif message == "INFO_SESION":
                    info = f"👤 Usuario: {session['username']} | 🔑 Rol: {session['rol']} | 🏠 Sala Actual: {session['id_sala']}"
                    writer.write(f"OK|200|{info}\n".encode())

            await writer.drain()
    except Exception as e:
        print(f"[!] Error con {addr}: {e}")
    finally:
        user_info = active_sessions.pop(writer, None)
        print(f"[-] DESCONECTADO: {user_info['username'] if user_info else 'Anónimo'}")
        writer.close()
        await writer.wait_closed()

async def main():
    args = get_args()
    loop = asyncio.get_running_loop()
    parent_conn, child_conn = Pipe()

    auth_proc = Process(target=start_auth_process, args=(child_conn,), daemon=True)
    auth_proc.start()

    loop.add_reader(parent_conn.fileno(), handle_auth_response, parent_conn)

    server = await asyncio.start_server(lambda r, w: handle_client(r, w, parent_conn), args.host, args.port)
    print(f"--- SERVER SCEE ACTIVO EN {args.host}:{args.port} ---")
    async with server: await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())