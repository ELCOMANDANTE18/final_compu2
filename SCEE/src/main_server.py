import asyncio
import os
import argparse
from multiprocessing import Process, Pipe
from dotenv import load_dotenv
from processes.auth import start_auth_process

load_dotenv()

# --- ESTADO GLOBAL ---
pending_auths = {}   # {username: writer}
active_sessions = {} # {writer: {user_id, username, rol, id_sala}}

def get_args():
    parser = argparse.ArgumentParser(description="SCEE Server - Mendoza")
    parser.add_argument("-p", "--port", type=int, default=os.getenv("SERVER_PORT", 5000))
    parser.add_argument("-b", "--host", default=os.getenv("SERVER_HOST", "127.0.0.1"))
    return parser.parse_args()

def handle_auth_response(pipe_conn): #La Respuesta Sincronica
    """Callback que sincroniza MariaDB con los sockets """
    if pipe_conn.poll(): # EL recepcionista mira el buzón de entrada para ver si llegó una carta
        response = pipe_conn.recv() # Abre la carta y lee los resultados que le mandó el departamento de archivos 
        username = response.get("user_requested")
        status = response.get("status")
        writer = pending_auths.pop(username, None) # Busca en su librera de "Clientes Esperando respuesta", tacha el nombre de la lista y toma el teléfono (el writer) para llamar a ese cliente
        
        if writer:
            tipo = response.get("type")
            if status == "OK":
                if tipo == "LIST_RES":
                    msg = f"SALAS_LIST|{response.get('data')}\n"
                elif tipo == "MY_SALAS_RES":
                    msg = f"MY_SALAS_LIST|{response.get('data')}\n"
                elif tipo == "JOIN_RES":
                    # Actualizamos la sala en la sesión activa en RAM
                    if writer in active_sessions:
                        active_sessions[writer]["id_sala"] = response.get("id_sala")
                    msg = f"JOIN_OK|Te uniste a la sala {response.get('id_sala')}\n"
                    print(f"[DB] {username} entró a la sala {response.get('id_sala')}")
                elif tipo == "SALA_CREATED":
                    msg = "OK|201|Sala creada exitosamente\n"
                    print(f"[DB] {username} creó una nueva sala")
                else: 
                    # LOGIN / REGISTER
                    active_sessions[writer] = {
                        "user_id": response.get("user_id"),
                        "username": username,
                        "rol": response.get("role"),
                        "id_sala": "Ninguna"
                    }
                    msg = f"AUTH_RES|200|{username}|{response.get('role')}\n"
                    print(f"--- [SESIÓN] {username} inició sesión como {response.get('role')} ---")
            else:
                msg = f"ERROR|401|{response.get('message')}\n"
                print(f"[!] Error de Auth para {username}: {response.get('message')}")
            
            writer.write(msg.encode())
            asyncio.create_task(writer.drain())

async def handle_client(reader, writer, pipe_conn): #Recepción 
    addr = writer.get_extra_info('peername')
    print(f"[+] CONEXIÓN ENTRANTE: {addr}")

    try:
        while True:
            data = await reader.read(1024)
            if not data: break
            message = data.decode().strip()
            session = active_sessions.get(writer)

            if not session:
                # --- IDENTIFICACIÓN ---
                parts = message.split("|")
                if len(parts) >= 3:
                    cmd, user = parts[0], parts[1]
                    print(f"[AUTH] Intento de {cmd} para: {user}")
                    pending_auths[user] = writer
                    if cmd == "LOGIN":
                        pipe_conn.send({"type": "LOGIN", "user": user, "pass": parts[2]})
                    elif cmd == "REGISTER":
                        pipe_conn.send({"type": "REGISTER", "user": user, "pass": parts[2], "rol": parts[3]})
            else:
                # --- COMANDOS CON SESIÓN ACTIVA ---
                print(f"[{session['username']}] comando: {message}")
                
                if message == "LIST_AVAILABLE":
                    pipe_conn.send({"type": "LIST_AVAILABLE", "id_user": session['user_id'], "user": session['username']})
                    pending_auths[session['username']] = writer
                
                elif message == "LIST_MY_SALAS":
                    pipe_conn.send({"type": "LIST_MY_SALAS", "id_user": session['user_id'], "user": session['username']})
                    pending_auths[session['username']] = writer
                
                elif message.startswith("CREATE_SALA|"): 
                    if session['rol'].lower() != 'profesor':
                        writer.write(b"ERROR|405|Solo profesores pueden crear salas\n")
                    else:
                        nom = message.split("|")[1]
                        pipe_conn.send({"type": "CREATE_SALA", "nombre": nom, "id_creador": session['user_id'], "user": session['username']})
                        pending_auths[session['username']] = writer

                elif message.startswith("JOIN|"):
                    try:
                        id_s = message.split("|")[1]
                        pipe_conn.send({"type": "JOIN_SALA", "id_sala": id_s, "id_user": session['user_id'], "user": session['username']})
                        pending_auths[session['username']] = writer
                    except IndexError:
                        writer.write(b"ERROR|400|Formato de ID invalido\n")
                
                elif message == "INFO_SESION":
                    res = f"OK|200|👤 Usuario: {session['username']} | 🔑 Rol: {session['rol']} | 🏠 Sala Actual: {session['id_sala']}\n"
                    writer.write(res.encode())
            
            await writer.drain()
    except Exception as e:
        print(f"[!] Error con {addr}: {e}")
    finally:
        session_info = active_sessions.pop(writer, None)
        u_name = session_info['username'] if session_info else "Anónimo"
        print(f"[-] DESCONECTADO: {u_name} ({addr})")
        writer.close()
        await writer.wait_closed()

async def main():
    args = get_args()
    loop = asyncio.get_running_loop()
    parent_conn, child_conn = Pipe()
    Process(target=start_auth_process, args=(child_conn,), daemon=True).start()
    
    loop.add_reader(parent_conn.fileno(), handle_auth_response, parent_conn)
    
    server = await asyncio.start_server(lambda r, w: handle_client(r, w, parent_conn), args.host, args.port)
    
    print("="*50)
    print(f"   SISTEMA SCEE ACTIVO - MENDOZA, ARGENTINA")
    print(f"   Escuchando en: {args.host}:{args.port}")
    print("="*50)
    
    async with server: await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Apagando servidor...")