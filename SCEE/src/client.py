import socket, argparse, threading, queue, sys, os

res_q = queue.Queue()

def print_banner():
    """Muestra el logo del proyecto al iniciar la sesión del cliente."""
    banner = r"""
      ______   ______  ________  ________ 
     /      \ /      \|        \|        \
    |  $$$$$$|  $$$$$$| $$$$$$$$| $$$$$$$$
    | $$___\$| $$   \$| $$__    | $$__    
     \$$    \| $$     | $$  \   | $$  \   
     _\$$$$$$| $$   __| $$$$$   | $$$$$   
    |  \__| $| $$__/  | $$_____ | $$_____ 
     \$$    $$\$$    $| $$     \| $$     \
      \$$$$$$  \$$$$$$ \$$$$$$$$ \$$$$$$$$
    """
    print(banner)
    print("="*42)
    print(" SCEE CLIENT - Sistema de Coordinación")
    print(" Sede Mendoza 🍇 | Usuario Activo")
    print("="*42 + "\n")

def listen(sock):
    while True:
        try:
            data = sock.recv(2048).decode().strip()
            if not data: break
            for line in data.split('\n'):
                if line.startswith("CHAT|"):
                    _, u, m = line.split("|")
                    sys.stdout.write(f"\r[📩 {u}]: {m}\nSala >> ")
                    sys.stdout.flush()
                else: res_q.put(line)
        except: break

def menu_principal(rol):
    print(f"\n=== SCEE PANEL ({rol.upper()}) ===")
    print("1. Buscar salas\n2. Mis salas (Entrar)\n3. Usuarios activos\n4. Salir")
    return input("Seleccioná: ")

def main():
    os.system('clear') if os.name == 'posix' else os.system('cls')
    print_banner()
    
    # --- CONFIGURACIÓN DE ARGUMENTOS ---
    p = argparse.ArgumentParser()
    p.add_argument("-u", required=True, help="Nombre de usuario")
    p.add_argument("-p", required=True, help="Contraseña")
    p.add_argument("-r", default="alumno", help="Rol del usuario")
    p.add_argument("--register", action="store_true", help="Registrar un nuevo usuario") # <-- AGREGADO
    
    args = p.parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        sock.connect(("127.0.0.1", 5000))
        
        # --- LÓGICA DE REGISTRO O LOGIN ---
        # Si pasaste --register por terminal, manda REGISTER, si no manda LOGIN
        cmd_type = "REGISTER" if args.register else "LOGIN"
        sock.send(f"{cmd_type}|{args.u}|{args.p}|{args.r}".encode())
        
        auth_data = sock.recv(1024).decode().strip()
        
        # El servidor responde 200 para login ok o 201 para registro ok
        if "AUTH_RES|200" in auth_data or "AUTH_RES|201" in auth_data:
            status_msg = "Bienvenido" if "200" in auth_data else "Registro exitoso"
            mi_rol = auth_data.split("|")[3]
            print(f"[✅] {status_msg} {auth_data.split('|')[2]}")
            
            threading.Thread(target=listen, args=(sock,), daemon=True).start()
            
            while True:
                opc = menu_principal(mi_rol)
                if opc in ["1", "2"]:
                    sock.send(b"LIST_AVAILABLE" if opc == "1" else b"LIST_MY_SALAS")
                    resp = res_q.get().split("|")
                    if resp[1] != "VACIO":
                        for s in resp[1].split(","): 
                            print(f" ID: {s.split(':')[0]} | {s.split(':')[1]}")
                        
                        tid = input("\nID para entrar (o Enter para volver): ")
                        if not tid or not tid.isdigit(): continue
                        
                        sock.send(f"JOIN|{tid}".encode())
                        d_join = res_q.get().split("|")
                        
                        if d_join[0] == "JOIN_OK":
                            print(f"\n--- HISTORIAL SALA {d_join[1]} ---")
                            if d_join[2] != "VACIO":
                                for m in d_join[2:]:
                                    if ":" in m: uh, mh = m.split(":", 1); print(f"[{uh}]: {mh}")
                            
                            # Notificación automática de tareas al entrar
                            sock.send(b"GET_TASKS")
                            t_check = res_q.get().split("|")
                            if t_check[0] == "TASKS_LIST" and t_check[1] != "VACIO":
                                num = len(t_check) - 1
                                print(f"\n🔔 AVISO: Tenés {num} tareas pendientes. Usá /tareas para verlas.")

                            print(f"\n[!] Comandos: /tareas, {'' if mi_rol != 'profesor' else '/nueva, '}ENTER para salir.")
                            while True:
                                txt = input("Sala >> ")
                                if not txt.strip(): 
                                    sock.send(b"LEAVE_ROOM"); res_q.get(); break
                                elif txt == "/tareas":
                                    sock.send(b"GET_TASKS")
                                    t_res = res_q.get().split("|")
                                    if t_res[1] != "VACIO":
                                        print("\n--- TAREAS ---")
                                        for t in t_res[1:]:
                                            try:
                                                partes = t.split(":")
                                                if len(partes) >= 3:
                                                    print(f"📌 {partes[0]}\n   📅 Entrega: {partes[-1]}\n   📝 Desc: {':'.join(partes[1:-1])}\n")
                                            except: continue
                                    else: print("Sin tareas.")
                                else: 
                                    sock.send(f"SEND_MSG|{txt}".encode()); res_q.get()
                elif opc == "4": break
        else:
            print(f"[❌] Error de autenticación: {auth_data}")
            
    except Exception as e:
        print(f"[❌] Error de conexión: {e}")
    finally:
        sock.close()

if __name__ == "__main__": main()