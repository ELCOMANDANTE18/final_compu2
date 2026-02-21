import socket
import argparse

def get_args():
    parser = argparse.ArgumentParser(description="SCEE Client")
    parser.add_argument("-u", "--user", required=True)
    parser.add_argument("-p", "--password", required=True)
    parser.add_argument("-r", "--role", choices=['alumno', 'profesor'])
    parser.add_argument("--register", action="store_true")
    return parser.parse_args()

def mostrar_menu_por_rol(rol):
    print("\n" + "="*45)
    print(f"       SCEE - PANEL ({rol.upper()})")
    print("="*45)
    print(" 1. Buscar salas nuevas (Unirse)")
    print(" 2. Ver mis salas actuales (Entrar)") # <--- ¡Ahora sí entra!
    if rol.lower() == "profesor":
        print(" 3. Crear una nueva sala (Docentes)")
    print(" 4. Ver mi estado de sesión")
    print(" 5. Salir")
    print("="*45)
    return input("Seleccioná: ")

def main():
    args = get_args()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 5000))
        cmd = f"REGISTER|{args.user}|{args.password}|{args.role}" if args.register else f"LOGIN|{args.user}|{args.password}"
        sock.send(cmd.encode())
        res = sock.recv(1024).decode().strip()
        partes = res.split("|")

        if "AUTH_RES|200" in res:
            mi_rol = partes[3]
            while True:
                opc = mostrar_menu_por_rol(mi_rol)
                
                # --- OPCIÓN 1: UNIRSE A UNA NUEVA ---
                if opc == "1":
                    sock.send(b"LIST_AVAILABLE")
                    raw = sock.recv(1024).decode().split("|")
                    if raw[1] == "VACIO": print("\n[!] No hay salas nuevas.")
                    else:
                        print("\n--- SALAS DISPONIBLES ---")
                        for s in raw[1].split(","):
                            sid, snom = s.split(":")
                            print(f" ID: {sid} | {snom}")
                        target = input("\nIngresá ID para unirte y entrar: ")
                        if target:
                            sock.send(f"JOIN|{target}".encode())
                            print(f"\n[S] {sock.recv(1024).decode()}")

                # --- OPCIÓN 2: ENTRAR A UNA DONDE YA ESTOY ---
                elif opc == "2":
                    sock.send(b"LIST_MY_SALAS")
                    raw = sock.recv(1024).decode().split("|")
                    if raw[1] == "VACIO": print("\n[!] No sos miembro de ninguna sala todavía.")
                    else:
                        print("\n--- TUS SALAS ---")
                        for s in raw[1].split(","):
                            sid, snom = s.split(":")
                            print(f" ID: {sid} | {snom} (MIEMBRO)")
                        
                        target = input("\nIngresá el ID de la sala a la que querés entrar: ")
                        if target:
                            # Reutilizamos JOIN porque el server ya maneja la membresía existente
                            sock.send(f"JOIN|{target}".encode())
                            print(f"\n[S] {sock.recv(1024).decode()}")

                elif opc == "3" and mi_rol == "profesor":
                    nom = input("Nombre de sala: ")
                    sock.send(f"CREATE_SALA|{nom}".encode())
                    print(f"\n[S] {sock.recv(1024).decode()}")

                elif opc == "4":
                    sock.send(b"INFO_SESION")
                    # Mostramos el recuadro de info completo
                    print(f"\n{sock.recv(1024).decode().split('|')[2]}")
                
                elif opc == "5": break
    finally: sock.close()

if __name__ == "__main__": main()