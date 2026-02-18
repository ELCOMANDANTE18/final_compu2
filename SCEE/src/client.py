import asyncio
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

def get_args():
    """Parseo de argumentos para el cliente."""
    parser = argparse.ArgumentParser(description="Cliente de SCEE")
    parser.add_argument("-h_host", "--host", default=os.getenv("SERVER_HOST"), help="IP del servidor")
    parser.add_argument("-p", "--port", type=int, default=os.getenv("SERVER_PORT"), help="Puerto del servidor")
    return parser.parse_args()

async def send_messages(writer):
    """Lee la entrada del usuario y la envía al servidor."""
    print("Escribe tus mensajes (o 'salir' para terminar):")
    while True:
        # Usamos run_in_executor para que input() no bloquee el bucle de eventos
        message = await asyncio.get_event_loop().run_in_executor(None, input, "> ")
        
        if message.lower() == 'salir':
            break
            
        writer.write(message.encode())
        await writer.drain()

async def receive_messages(reader):
    """Escucha respuestas del servidor de forma asíncrona."""
    while True:
        data = await reader.read(1024)
        if not data:
            print("\n[!] Conexión cerrada por el servidor.")
            break
        print(f"\n[S] {data.decode().strip()}")

async def main():
    args = get_args()
    try:
        # Conexión TCP al servidor central
        reader, writer = await asyncio.open_connection(args.host, args.port)
        print(f"[*] Conectado a la Central de Operaciones en {args.host}:{args.port}")

        # Ejecutamos enviar y recibir al mismo tiempo (Concurrencia)
        await asyncio.gather(
            send_messages(writer),
            receive_messages(reader)
        )

    except ConnectionRefusedError:
        print("[!] No se pudo conectar. ¿Está prendido el servidor?")
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        print("[*] Desconectado.")

if __name__ == "__main__":
    asyncio.run(main())