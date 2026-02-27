import socket, argparse, threading, queue, sys, os

res_q = queue.Queue()

def log(tag, msg):
    import datetime
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{tag}] {msg}")

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
                    partes = line.split("|")
                    if len(partes) >= 3:
                        _, u, m = partes[0], partes[1], "|".join(partes[2:])
                        sys.stdout.write(f"\r[📩 {u}]: {m}\nSala >> ")
                        sys.stdout.flush()
                else: 
                    res_q.put(line)
        except: 
            break

def menu_principal(rol):
    """Muestra el menú según el rol del usuario."""
    print(f"\n=== SCEE PANEL ({rol.upper()}) ===")
    print("1. Buscar salas")
    print("2. Mis salas (Entrar)")
    print("3. Usuarios activos")
    print("4. Salir")
    if rol == "profesor":
        print("5. Crear sala") 
    return input("Seleccioná: ")

def main():
    os.system('clear' if os.name == 'posix' else 'cls')
    print_banner()
    
    p = argparse.ArgumentParser(description="Cliente SCEE - Mendoza")
    p.add_argument("-u", required=True, help="Usuario")
    p.add_argument("-p", required=True, help="Contraseña")
    p.add_argument("-r", default="alumno", help="Rol")
    p.add_argument("--host", default="::1", help="Host del servidor (default: ::1)")
    p.add_argument("--port", type=int, default=5001, help="Puerto (default: 5001)")
    p.add_argument("--register", action="store_true", help="Registrar")
    
    args = p.parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        sock.connect((args.host, args.port))
        log("NETWORK", f"Conectado a {args.host}:{args.port}")
        
        cmd = "REGISTER" if args.register else "LOGIN"
        sock.send(f"{cmd}|{args.u}|{args.p}|{args.r}".encode())
        
        auth_data = sock.recv(1024).decode().strip()
        
        if "AUTH_RES|200" in auth_data:
            partes = auth_data.split("|")
            mi_rol = partes[3]
            usuario = partes[2]
            tipo_accion = "registrado" if args.register else "conectado"
            
            print(f"[S] Usuario {usuario} {tipo_accion} con éxito.")
            threading.Thread(target=listen, args=(sock,), daemon=True).start()
            
            while True:
                opc = menu_principal(mi_rol)
                
                if opc in ["1", "2"]:
                    sock.send(b"LIST_AVAILABLE" if opc == "1" else b"LIST_MY_SALAS")
                    resp = res_q.get().split("|")
                    if resp[1] != "VACIO":
                        for s in resp[1].split(","): 
                            if ":" in s:
                                print(f" ID: {s.split(':')[0]} | {s.split(':')[1]}")
                        
                        tid = input("\nID para entrar (o Enter para volver): ")
                        if not tid or not tid.isdigit(): continue
                        
                        sock.send(f"JOIN|{tid}".encode())
                        d_join = res_q.get().split("|")
                        
                        if d_join[0] == "JOIN_OK":
                            print(f"\n--- HISTORIAL SALA {d_join[1]} ---")
                            if d_join[2] != "VACIO":
                                for m in d_join[2:]:
                                    if ":" in m: 
                                        uh, mh = m.split(":", 1)
                                        print(f"[{uh}]: {mh}")

                            # Notificaciones iniciales según rol
                            if mi_rol == "profesor":
                                sock.send(b"LIST_SUBMISSIONS")
                                s_check = res_q.get().split("|")
                                count = len(s_check[1:]) if s_check[1] != "VACIO" else 0
                                if count > 0:
                                    print(f"\n📝 NOTIFICACIÓN: Hay {count} entregas esperando corrección.")
                                print(f"\n[!] Comandos: /tareas, /nueva, /entregas, /corregir [ID] [NOTA], ENTER para salir.")
                            else:
                                # Notificación de Tareas Pendientes
                                sock.send(b"GET_TASKS")
                                t_check = res_q.get().split("|")
                                num_t = len(t_check[1:]) if t_check[1] != "VACIO" else 0
                                if num_t > 0:
                                    print(f"\n🔔 AVISO: Tenés {num_t} tareas pendientes. Usá /tareas para verlas.")
                                
                                # --- NUEVO: Notificación de Notas ---
                                sock.send(b"GET_GRADES")
                                n_check = res_q.get().split("|")
                                num_n = len(n_check[1:]) if n_check[1] != "VACIO" else 0
                                if num_n > 0:
                                    print(f"🎓 NOTIFICACIÓN: Tenés {num_n} notas cargadas. Usá /notas para verlas.")

                                print(f"\n[!] Comandos: /tareas, /subir [ID], /notas, ENTER para salir.")

                            # UN SOLO BUCLE PARA TODO DENTRO DE LA SALA
                            while True:
                                txt = input("Sala >> ")
                                if not txt.strip(): 
                                    sock.send(b"LEAVE_ROOM")
                                    res_q.get()
                                    break
                                
                                # --- COMANDOS COMUNES ---
                                if txt == "/tareas":
                                    sock.send(b"GET_TASKS")
                                    t_res = res_q.get().split("|")
                                    if len(t_res) > 1 and t_res[1] != "VACIO":
                                        titulo_lista = "GESTIÓN DE TAREAS" if mi_rol == "profesor" else "TAREAS PENDIENTES"
                                        print(f"\n--- {titulo_lista} ---")
                                        for t in t_res[1:]:
                                            p = t.split("§")
                                            print(f"🆔 ID: {p[0]} | 📌 {p[1]}\n   📅 {p[3]}\n   📝 {p[2]}\n")
                                    else:
                                        print("\n[!] No hay tareas en esta sala.")

                                elif txt == "/notas" and mi_rol != "profesor":
                                    sock.send(b"GET_GRADES")
                                    n_res = res_q.get().split("|")
                                    if len(n_res) > 1 and n_res[1] != "VACIO":
                                        print("\n--- 🎓 MIS CALIFICACIONES ---")
                                        for n in n_res[1:]:
                                            p = n.split("§")
                                            print(f"📌 {p[0]} | ⭐ Nota: {p[1]} | 📅 Fecha: {p[2]}")
                                    else:
                                        print("\n[!] Aún no tenés notas cargadas o corregidas.")        

                                # --- COMANDOS PROFESOR ---
                                elif txt == "/nueva" and mi_rol == "profesor":
                                    tit = input("Título: "); desc = input("Descripción: "); fec = input("Fecha (YYYY-MM-DD HH:MM): ")
                                    sock.send(f"CREAR_TAREA|{tit}|{desc}|{fec}".encode())
                                    res_q.get()
                                    print("[S] Tarea creada.")

                                elif txt == "/entregas" and mi_rol == "profesor":
                                    sock.send(b"LIST_SUBMISSIONS")
                                    e_res = res_q.get().split("|")
                                    if len(e_res) > 1 and e_res[1] != "VACIO":
                                        print("\n--- ENTREGAS PENDIENTES ---")
                                        for ent in e_res[1:]:
                                            eid, eal, etit, econ = ent.split("§")
                                            print(f"🆔 ID: {eid} | 👤 Alumno: {eal}\n   📌 Tarea: {etit}\n   💬 Contenido: {econ}\n")
                                    else: print("No hay entregas pendientes.")

                                elif txt.startswith("/corregir") and mi_rol == "profesor":
                                    parts = txt.split(" ")
                                    if len(parts) == 3:
                                        sock.send(f"GRADE|{parts[1]}|{parts[2]}".encode())
                                        res_q.get()
                                        print(f"[S] Entrega {parts[1]} calificada.")

                                # --- COMANDOS ALUMNO ---
                                elif txt.startswith("/subir") and mi_rol != "profesor":
                                    parts = txt.split(" ")
                                    if len(parts) >= 2:
                                        tp_id = parts[1]
                                        cont = input(f"Contenido para TP {tp_id}: ")
                                        sock.send(f"SUBIR_ENTREGA|{tp_id}|{cont}".encode())
                                        res_q.get()
                                        print("[S] Entrega enviada.")
                                    else:
                                        print("[!] Uso: /subir [ID_TAREA]")

                                # --- CHAT ---
                                else: 
                                    sock.send(f"SEND_MSG|{txt}".encode())
                                    res_q.get()

                elif opc == "3":
                    sock.send(b"LIST_USERS")
                    resp = res_q.get().split("|")
                    if resp[1] != "VACIO":
                        print("\n--- USUARIOS CONECTADOS ---")
                        for user in resp[1].split(","):
                            print(f" • {user}")
                    else:
                        print("\n[!] No hay otros usuarios conectados.")

                elif opc == "5" and mi_rol == "profesor":
                    print("\n--- NUEVA SALA (Escribe '0' para cancelar) ---")
                    nombre = input("Nombre de la sala: ")
                    if nombre.strip() == "0": continue
                    desc = input("Descripción (opcional): ")
                    sock.send(f"CREATE_SALA|{nombre}|{desc}".encode())
                    resp_s = res_q.get().split("|")
                    if resp_s[1] == "OK":
                        print(f"\n[S] Sala '{nombre}' creada con éxito.")
                    else:
                        print(f"\n[!] Error: {resp_s[-1]}")

                elif opc == "4": 
                    break
        else:
            msg_err = auth_data.split("|")[-1] if "|" in auth_data else auth_data
            print(f"[!] Error de acceso: {msg_err}")

    except ConnectionRefusedError:
        print("[!] Error: No se pudo conectar con el servidor SCEE.")
    except Exception as e:
        print(f"[!] Error inesperado: {e}")
    finally:
        sock.close()

if __name__ == "__main__": 
    main()