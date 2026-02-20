import socket
import argparse
import sys

def get_client_args():
    parser = argparse.ArgumentParser(description="Cliente SCEE - Acceso al Sistema")
    parser.add_argument("-u", "--user", required=True, help="Nombre de usuario")
    parser.add_argument("-p", "--password", required=True, help="Contraseña")
    parser.add_argument("-r", "--role", choices=['alumno', 'profesor', 'admin'], help="Rol (solo para registro)")
    parser.add_argument("--register", action="store_true", help="Indica si se desea registrar un nuevo usuario")
    return parser.parse_args()

def main():
    args = get_client_args()
    host = "127.0.0.1"
    port = 5000

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        print(f"[*] Conectado al Servidor SCEE en {host}:{port}")

        # Construcción automática del comando según los argumentos
        if args.register:
            if not args.role:
                print("Error: El registro requiere especificar un rol (--role)")
                sys.exit(1)
            cmd = f"REGISTER|{args.user}|{args.password}|{args.role}"
        else:
            cmd = f"LOGIN|{args.user}|{args.password}"

        # Enviamos la petición inicial
        client_socket.send(cmd.encode())
        response = client_socket.recv(1024).decode()
        print(f"[S] {response}")

        # Si el acceso fue exitoso, entramos en modo interactivo para los comandos de sala
        if "200" in response:
            print("--- Sesión Iniciada. Escribe comandos o 'salir' ---")
            while True:
                msg = input(f"{args.user} > ")
                if msg.lower() == 'salir': break
                client_socket.send(msg.encode())
                print(f"[S] {client_socket.recv(1024).decode()}")

    except Exception as e:
        print(f"[!] Error de conexión: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()