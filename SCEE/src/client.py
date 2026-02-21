import socket, argparse, threading, queue, sys

res_q = queue.Queue()

def listen(sock):
    while True:
        try:
            data = sock.recv(1024).decode().strip()
            if not data: break
            for line in data.split('\n'):
                if line.startswith("CHAT|"):
                    _, u, m = line.split("|")
                    print(f"\n\r[📩 {u}]: {m}\nSala >> ", end="", flush=True)
                else: res_q.put(line)
        except: break

def menu_principal(rol):
    print("\n" + "="*40 + f"\n  SCEE - PANEL ({rol.upper()})\n" + "="*40)
    print(" 1. Buscar salas\n 2. Mis salas (Entrar)")
    if rol.lower() == "profesor":
        print(" 3. Crear sala (Profe)")
    print(" 4. Salir")
    print("="*40)
    return input("Seleccioná: ")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user", required=True)
    parser.add_argument("-p", "--password", required=True)
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 5000))
    sock.send(f"LOGIN|{args.user}|{args.password}".encode())
    
    r = sock.recv(1024).decode().strip()
    if "AUTH_RES|200" in r:
        mi_rol = r.split("|")[3]
        print(f"[S] Bienvenido {r.split('|')[2]}")
        threading.Thread(target=listen, args=(sock,), daemon=True).start()
        
        while True:
            opc = menu_principal(mi_rol)
            if opc == "1":
                sock.send(b"LIST_AVAILABLE")
                raw = res_q.get().split("|")
                if raw[1] != "VACIO":
                    for s in raw[1].split(","): print(f" ID: {s.split(':')[0]} | {s.split(':')[1]}")
                    t = input("\nID para unirse: ")
                    if t: sock.send(f"JOIN|{t}".encode()); res_q.get()
            elif opc == "2":
                sock.send(b"LIST_MY_SALAS")
                raw = res_q.get().split("|")
                if raw[1] != "VACIO":
                    for s in raw[1].split(","): print(f" ID: {s.split(':')[0]} | {s.split(':')[1]}")
                    tid = input("\nID para entrar: ")
                    if tid:
                        sock.send(f"JOIN|{tid}".encode())
                        rid = res_q.get().split("|")[1]
                        print(f"\n[!] SALA {rid} ACTIVA. Escribí tu mensaje o '/salir'.")
                        while True:
                            sub = input("Sala >> ")
                            if sub.strip() == "/salir":
                                sock.send(b"LEAVE_ROOM"); res_q.get(); break
                            elif sub.strip():
                                sock.send(f"SEND_MSG|{sub}".encode()); res_q.get()
            elif opc == "3" and mi_rol.lower() == "profesor":
                n = input("Nombre sala: ").strip()
                if n:
                    d = input("Descripción: ").strip()
                    sock.send(f"CREATE_SALA|{n}|{d}".encode()); res_q.get()
                else: print("[!] El nombre es obligatorio.")
            elif opc == "4": break
    sock.close()

if __name__ == "__main__": main()