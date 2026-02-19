import asyncio
import os
import argparse
import json
from multiprocessing import Process, Pipe
from dotenv import load_dotenv
from processes.auth import start_auth_process

load_dotenv()

# Diccionario para rastrear qué cliente está esperando autenticación
# Clave: nombre de usuario, Valor: objeto writer del socket
pending_auths = {}

def get_args():
    """Parseo de argumentos reglamentario."""
    parser = argparse.ArgumentParser(description="Central de Operaciones - SCEE")
    parser.add_argument("-p", "--port", type=int, default=os.getenv("SERVER_PORT", 5000))
    parser.add_argument("-b", "--host", default=os.getenv("SERVER_HOST", "127.0.0.1"))
    return parser.parse_args()

def handle_auth_response(pipe_conn):
    """
    Callback asíncrono: se activa cuando el proceso Auth responde.
    """
    if pipe_conn.poll():
        response = pipe_conn.recv()
        username = response.get("user_requested")
        status = response.get("status")
        
        print(f"[SERVER] Resultado Auth para {username}: {status}")
        
        # Recuperamos el socket del cliente que estaba esperando
        writer = pending_auths.pop(username, None)
        if writer:
            msg = f"AUTH_RES:{json.dumps(response)}\n"
            writer.write(msg.encode())
            asyncio.create_task(writer.drain())

async def handle_client(reader, writer, pipe_conn):
    """Maneja la conexión de cada alumno/profesor."""
    addr = writer.get_extra_info('peername')
    print(f"[*] Nuevo cliente conectado: {addr}")

    try:
        while True:
            data = await reader.read(1024)
            if not data: break
            
            message = data.decode().strip()
            
            # Protocolo simple: LOGIN|usuario|password
            if message.startswith("LOGIN|"):
                _, user, passwd = message.split("|")
                print(f"[SERVER] Pidiendo validación para {user}...")
                
                # Registramos al cliente para saber a quién responderle luego
                pending_auths[user] = writer
                # Enviamos al proceso hijo por el Pipe
                pipe_conn.send({"user": user, "pass": passwd})
            else:
                writer.write(b"ERROR: Comand desconocido o falta login\n")
                await writer.drain()

    except Exception as e:
        print(f"[!] Error con {addr}: {e}")
    finally:
        writer.close()
        await writer.wait_closed()

async def main():
    args = get_args()
    loop = asyncio.get_running_loop()
    
    # Configuración de IPC
    parent_conn, child_conn = Pipe()
    auth_proc = Process(target=start_auth_process, args=(child_conn,))
    auth_proc.start()

    # Registramos el Pipe en el loop de asyncio para que no sea bloqueante
    loop.add_reader(parent_conn.fileno(), handle_auth_response, parent_conn)

    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, parent_conn), 
        args.host, args.port
    )

    print(f"[V] Central de Operaciones en {args.host}:{args.port}")
    
    async with server:
        try:
            await server.serve_forever()
        finally:
            auth_proc.terminate()
            auth_proc.join()

if __name__ == "__main__":
    asyncio.run(main())