import asyncio
import os
import argparse
import json
from multiprocessing import Process, Pipe
from dotenv import load_dotenv
from processes.auth import start_auth_process

load_dotenv()

# --- GESTIÓN DE ESTADO GLOBAL ---
# pending_auths: { "username": writer_object }
pending_auths = {}
# active_sessions: { writer_object: {"user_id": int, "username": str, "rol": str, "auth": bool} }
active_sessions = {}

def get_args():
    """Configuración de argumentos para flexibilidad en el laboratorio."""
    parser = argparse.ArgumentParser(description="SCEE - Servidor Central de Coordinación")
    parser.add_argument("-p", "--port", type=int, default=os.getenv("SERVER_PORT", 5000))
    parser.add_argument("-b", "--host", default=os.getenv("SERVER_HOST", "127.0.0.1"))
    return parser.parse_args()

def handle_auth_response(pipe_conn):
    """Callback asíncrono que reacciona a las respuestas del proceso Auth."""
    if pipe_conn.poll():
        response = pipe_conn.recv()
        username = response.get("user_requested")
        status = response.get("status")
        writer = pending_auths.pop(username, None)
        
        if writer:
            if status == "OK":
                # Creamos la sesión persistente en el servidor
                active_sessions[writer] = {
                    "user_id": response.get("user_id"),
                    "username": username,
                    "rol": response.get("role"),
                    "auth": True
                }
                print(f"--- [SESIÓN CREADA] User: {username} | Rol: {response.get('role')} ---")
                msg = f"AUTH_RES|200|Bienvenido {username}\n"
            else:
                print(f"--- [AUTH RECHAZADA] User: {username} | Razón: {response.get('message')} ---")
                msg = f"AUTH_RES|401|Error: {response.get('message')}\n"
            
            writer.write(msg.encode())
            asyncio.create_task(writer.drain())

async def handle_client(reader, writer, pipe_conn):
    """Maneja el ciclo de vida de cada conexión individual."""
    addr = writer.get_extra_info('peername')
    # Print de entrada solicitado
    print(f"[+] CONEXIÓN ENTRANTE: {addr}")

    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break # El cliente cerró la conexión
            
            message = data.decode().strip()
            session = active_sessions.get(writer)

            if not session:
                # FLUJO DE ACCESO: LOGIN O REGISTER
                if message.startswith("LOGIN|") or message.startswith("REGISTER|"):
                    parts = message.split("|")
                    if len(parts) >= 3:
                        cmd, user = parts[0], parts[1]
                        pending_auths[user] = writer
                        print(f"[*] Solicitud de {cmd} para el usuario: {user}")
                        
                        if cmd == "LOGIN":
                            pipe_conn.send({"type": "LOGIN", "user": user, "pass": parts[2]})
                        elif cmd == "REGISTER" and len(parts) == 4:
                            pipe_conn.send({"type": "REGISTER", "user": user, "pass": parts[2], "rol": parts[3]})
                    else:
                        writer.write(b"ERROR|400|Formato de comando incorrecto\n")
                else:
                    writer.write(b"ERROR|403|Acceso denegado. Identificate primero.\n")
            else:
                # FLUJO DE NEGOCIO: USUARIO YA AUTENTICADO
                print(f"[MSG] {session['username']} ({session['rol']}): {message}")
                
                if message == "INFO_SESION":
                    res = f"OK|200|ID: {session['user_id']}, User: {session['username']}, Rol: {session['rol']}\n"
                    writer.write(res.encode())
                elif message.startswith("CREATE_SALA|"):
                    # Pendiente implementar lógica de salas en auth.py
                    writer.write(b"OK|200|Comando de sala recibido (En desarrollo)\n")
                else:
                    writer.write(b"OK|200|Mensaje procesado por el servidor\n")

            await writer.drain()

    except Exception as e:
        print(f"[!] ERROR en la conexión {addr}: {e}")
    finally:
        # Lógica de salida del cliente
        user_info = active_sessions.pop(writer, None)
        username = user_info['username'] if user_info else "Anónimo"
        
        # Print de salida solicitado
        print(f"[-] CLIENTE DESCONECTADO: {username} ({addr})")
        
        writer.close()
        await writer.wait_closed()

async def main():
    args = get_args()
    loop = asyncio.get_running_loop()
    
    # Configuración de IPC
    parent_conn, child_conn = Pipe()
    auth_proc = Process(target=start_auth_process, args=(child_conn,))
    auth_proc.start()

    # Multiplexación: Escuchar el Pipe sin bloquear
    loop.add_reader(parent_conn.fileno(), handle_auth_response, parent_conn)

    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, parent_conn), 
        args.host, args.port
    )

    print("-" * 50)
    print(f"   SISTEMA DE COORDINACIÓN (SCEE) INICIADO")
    print(f"   Escuchando en: {args.host}:{args.port}")
    print(f"   Modo: Desarrollo (Linux Mint)")
    print("-" * 50)

    async with server:
        try:
            await server.serve_forever()
        finally:
            auth_proc.terminate()
            auth_proc.join()

if __name__ == "__main__":
    asyncio.run(main())