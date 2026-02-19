import asyncio
import os
import argparse
from multiprocessing import Process, Pipe # Agregamos estas herramientas
from dotenv import load_dotenv
from processes.auth import auth_process_loop # Importamos tu nuevo proceso

load_dotenv()

# --- Configuración del Proceso de Auth ---
# Creamos el Pipe: parent_conn es para el servidor, child_conn para el proceso auth
parent_conn, child_conn = Pipe()
auth_proc = Process(target=auth_process_loop, args=(child_conn,))

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"[*] Conexión establecida con {addr}")

    try:
        while True:
            data = await reader.read(1024)
            if not data: break
            
            user_data = data.decode().strip()
            
            # PASO CLAVE: El servidor principal le manda la data al proceso Auth por el Pipe
            print(f"[SERVER] Consultando autenticación para {user_data}...")
            parent_conn.send({"user": user_data, "pass": "1234"}) # Ejemplo simple
            
            # Por ahora, leemos la respuesta (ojo: esto es bloqueante, lo arreglaremos en el Issue #5)
            if parent_conn.poll(timeout=2):
                response = parent_conn.recv()
                writer.write(f"Respuesta Auth: {response['status']}\n".encode())
            else:
                writer.write(b"Error: Tiempo de espera de auth agotado\n")
                
            await writer.drain()

    finally:
        writer.close()
        await writer.wait_closed()

async def main():
    # Iniciamos el proceso hijo antes de arrancar el servidor asíncrono
    auth_proc.start()
    
    server = await asyncio.start_server(handle_client, '127.0.0.1', 5000)
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        # Nos aseguramos de cerrar el proceso hijo al apagar todo
        auth_proc.terminate()
        auth_proc.join()