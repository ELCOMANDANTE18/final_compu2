import asyncio
import os
import argparse
from dotenv import load_dotenv

# Cargamos las variables del archivo .env
load_dotenv()

def get_args():
    """Paso 1: Parseo de argumentos (Requisito de la materia)."""
    parser = argparse.ArgumentParser(description="Servidor Principal de SCEE")
    # Si no pasamos argumentos, usa los del .env por defecto
    parser.add_argument("-h_host", "--host", default=os.getenv("SERVER_HOST"), help="Host del servidor")
    parser.add_argument("-p", "--port", type=int, default=os.getenv("SERVER_PORT"), help="Puerto del servidor")
    return parser.parse_args()


async def handle_client(reader, writer):
    """Paso 2: Qué hacer cuando se conecta un cliente."""
    addr = writer.get_extra_info('peername')
    print(f"[*] Conexión establecida con {addr}")

    try:
        while True:
            # Esperamos datos del cliente (máximo 1024 bytes)
            data = await reader.read(1024)
            if not data:
                break # Si no hay datos, el cliente se desconectó

            message = data.decode().strip() # Decodifica los bytes a texto
            print(f"[<{addr}] Mensaje recibido: {message}")

            # Respuesta simple para probar la conexión
            response = f"Servidor: Recibí tu mensaje '{message}'\n"
            writer.write(response.encode()) # Prepara un mensaje , lo convierte a bytes (encode) y lo envía al cliente 
            await writer.drain() # Asegura que los datos se envíen realmente

    except Exception as e:
        print(f"[!] Error con el cliente {addr}: {e}")
    finally:
        print(f"[*] Cerrando conexión con {addr}")
        writer.close()
        await writer.wait_closed()

async def main():  #La central de Operaciones
    args = get_args()
    
    # Creamos el servidor de sockets
    server = await asyncio.start_server(handle_client, args.host, args.port)

    addr = server.sockets[0].getsockname()
    print(f"[V] Servidor SCEE iniciado en {addr}")

    # Mantenemos el servidor corriendo indefinidamente
    async with server:
        await server.serve_forever() # Es el bucle infinito espera hsata que alguien lo detenga

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Servidor detenido por el usuario.")        

        