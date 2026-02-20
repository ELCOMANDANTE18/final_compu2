import socket
import argparse
import sys

def get_args():
    parser = argparse.ArgumentParser(description="SCEE Client - Mendoza")
    parser.add_argument("-u", "--user", required=True)
    parser.add_argument("-p", "--password", required=True)
    parser.add_argument("-r", "--role", choices=['alumno', 'profesor'])
    parser.add_argument("--register", action="store_true")
    return parser.parse_args()

def mostrar_menu_por_rol(rol):
    print("\n" + "="*40)
    print(f"       SCEE - MENÚ ({rol.upper()})")
    print("="*40)
    print(" 1. Ver salas disponibles")
    if rol.lower() != "alumno":
        print(" 2. Crear una nueva sala (Docentes)")
    print(" 3. Ver mi estado de sesión")
    print(" 4. Salir")
    print("="*40)
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
        if "AUTH_RES|200" in res and len(partes) >= 4:
            mi_nombre, mi_rol = partes[2], partes[3]
            print(f"\n[S] ¡Bienvenido {mi_nombre}! Rol: {mi_rol}")

            while True:
                opc = mostrar_menu_por_rol(mi_rol)
                if opc == "1":
                    sock.send(b"LIST_SALAS")
                    raw = sock.recv(1024).decode()
                    if "|" in raw:
                        data = raw.split("|")[1]
                        if data == "VACIO": print("\n[!] No hay salas.")
                        else:
                            print("\n--- SALAS ---")
                            for s in data.split(","):
                                sid, snom = s.split(":")
                                print(f"  ID: {sid} | {snom}")
                            target = input("\nID para unirse: ")
                            if target:
                                sock.send(f"JOIN|{target}".encode())
                                print(f"\n[S] {sock.recv(1024).decode()}")
                elif opc == "2" and mi_rol.lower() != "alumno":
                    nom = input("Nombre de sala: ")
                    sock.send(f"CREATE_SALA|{nom}".encode())
                    print(f"\n[S] {sock.recv(1024).decode()}")
                elif opc == "3":
                    sock.send(b"INFO_SESION")
                    info = sock.recv(1024).decode()
                    if "OK|200" in info:
                        print("\n" + "─"*55 + f"\n  {info.split('|')[2].strip()}\n" + "─"*55)
                elif opc == "4": break
        else:
            print(f"\n[!] Error: {res}")
    except Exception as e: print(f"\n[!] Error: {e}")
    finally: sock.close()

if __name__ == "__main__": main()