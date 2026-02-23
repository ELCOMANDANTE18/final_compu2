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
    p = argparse.ArgumentParser(); p.add_argument("-u"); p.add_argument("-p"); p.add_argument("-r", default="alumno")
    args = p.parse_args(); sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM); sock.connect(("127.0.0.1", 5000))
    sock.send(f"LOGIN|{args.u}|{args.p}|{args.r}".encode())
    
    auth_data = sock.recv(1024).decode().strip()
    if "AUTH_RES|200" in auth_data:
        mi_rol = auth_data.split("|")[3]; print(f"[S] Bienvenido {auth_data.split('|')[2]}")
        threading.Thread(target=listen, args=(sock,), daemon=True).start()
        
        while True:
            opc = menu_principal(mi_rol)
            if opc in ["1", "2"]:
                sock.send(b"LIST_AVAILABLE" if opc == "1" else b"LIST_MY_SALAS")
                resp = res_q.get().split("|")
                if resp[1] != "VACIO":
                    for s in resp[1].split(","): print(f" ID: {s.split(':')[0]} | {s.split(':')[1]}")
                    tid = input("\nID para entrar (o Enter para volver): ")
                    if not tid or not tid.isdigit(): continue
                    
                    sock.send(f"JOIN|{tid}".encode()); d_join = res_q.get().split("|")
                    if d_join[0] == "JOIN_OK":
                        print(f"\n--- HISTORIAL SALA {d_join[1]} ---")
                        if d_join[2] != "VACIO":
                            for m in d_join[2:]:
                                if ":" in m: uh, mh = m.split(":", 1); print(f"[{uh}]: {mh}")
                        
                        # --- AUTO-NOTIFICACIÓN DE TAREAS AL ENTRAR ---
                        sock.send(b"GET_TASKS")
                        t_check = res_q.get().split("|")
                        if t_check[0] == "TASKS_LIST" and t_check[1] != "VACIO":
                            num = len(t_check) - 1
                            print(f"\n🔔 AVISO: Tenés {num} tareas pendientes. Usá /tareas para verlas.")

                        print(f"\n[!] Comandos: /tareas, {'' if mi_rol != 'profesor' else '/nueva, '}ENTER para salir.")
                        while True:
                            txt = input("Sala >> ")
                            if not txt.strip(): sock.send(b"LEAVE_ROOM"); res_q.get(); break
                            elif txt == "/tareas":
                                sock.send(b"GET_TASKS")
                                t_res = res_q.get().split("|")
                                
                                if t_res[1] != "VACIO":
                                    print("\n--- 📚 TAREAS PENDIENTES ---")
                                    lista_titulos = []
                                    for t in t_res[1:]:
                                        try:
                                            # Usamos § que es el separador que definiste en la DB
                                            partes = t.split("§") 
                                            if len(partes) >= 3:
                                                titulo, desc, fecha = partes[0], partes[1], partes[2]
                                                lista_titulos.append(titulo)
                                                print(f"📌 [{titulo}]\n   📅 Entrega: {fecha}\n   📝 Detalle: {desc}\n")
                                        except: continue
                                    
                                    # --- LÓGICA DE ENTREGA INMEDIATA ---
                                    opcion = input("¿Querés entregar alguna tarea ahora? (Escribí el título o Enter para volver): ").strip()
                                    
                                    if opcion in lista_titulos:
                                        path = input(f"📂 Ruta del archivo para '{opcion}': ").strip()
                                        if os.path.exists(path):
                                            size = os.path.getsize(path)
                                            # Aplicamos el límite de 20MB ($20 \times 1024 \times 1024$ bytes)
                                            if size > 20 * 1024 * 1024:
                                                print("❌ Error: El archivo supera los 20MB permitidos.")
                                            else:
                                                fname = f"{opcion.replace(' ', '_')}_{os.path.basename(path)}"
                                                sock.send(f"UPLOAD|{fname}|{size}".encode())
                                                
                                                if res_q.get() == "FILE_READY":
                                                    print(f"🚀 Subiendo entrega...")
                                                    with open(path, "rb") as f:
                                                        sock.sendall(f.read())
                                                    print(f"[S] {res_q.get()}") # Confirmación UPLOAD_OK
                                        else:
                                            print("❌ Archivo no encontrado.")
                                else:
                                    print("\n✅ No hay tareas pendientes en esta sala.")
            elif opc == "4": break
    sock.close()

if __name__ == "__main__": main()