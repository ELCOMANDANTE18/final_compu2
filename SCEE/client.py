import socket, argparse, threading, queue, sys, os
# Colores para la terminal
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

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
    print(f"\n=== {GREEN}SCEE PANEL ({rol.upper()}){RESET} ===")
    print("1. Buscar salas")
    print("2. Mis salas (Entrar)")
    print("3. Usuarios activos")
    print(f"{RED}4. Salir{RESET}")
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
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    
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
                        
                        tid = input("\nID para entrar (o Enter para volver): ").strip()
                        if not tid: continue

                        if not tid.isdigit():
                            print(f"{RED}[!] Error: El ID debe ser un número.{RESET}")
                            input("Presioná Enter para reintentar...")
                            continue

                        sock.send(f"JOIN|{tid}".encode())
                        respuesta = res_q.get()
                        d_join = respuesta.split("|")

                        if d_join[0] == "JOIN_OK":
                            # 1. MOSTRAR HISTORIAL
                            print(f"\n--- HISTORIAL SALA {d_join[1]} ---")
                            if d_join[2] != "VACIO":
                                for m in d_join[2:]:
                                    if ":" in m:
                                        uh, mh = m.split(":", 1)
                                        print(f"[{uh}]: {mh}")

                            # 2. NOTIFICACIONES INICIALES SEGÚN ROL
                            if mi_rol == "profesor":
                                sock.send(b"LIST_SUBMISSIONS")
                                s_check = res_q.get().split("|")
                                count = len(s_check[1:]) if s_check[1] != "VACIO" else 0
                                if count > 0:
                                    print(f"\n{YELLOW}📝 NOTIFICACIÓN: Hay {count} entregas esperando corrección.{RESET}")
                                print(f"\n[!] Comandos: /tareas, /nueva, /entregas, /corregir [ID] [NOTA], /borrar [ID], ENTER para salir.")
                            else:
                                sock.send(b"GET_TASKS")
                                t_check = res_q.get().split("|")
                                num_t = len(t_check[1:]) if t_check[1] != "VACIO" else 0
                                if num_t > 0:
                                    print(f"\n{YELLOW}🔔 AVISO: Tenés {num_t} tareas pendientes. Usá /tareas para verlas.{RESET}")
                                
                                sock.send(b"GET_GRADES")
                                n_check = res_q.get().split("|")
                                num_n = len(n_check[1:]) if n_check[1] != "VACIO" else 0
                                if num_n > 0:
                                    print(f"{GREEN}🎓 NOTIFICACIÓN: Tenés {num_n} notas cargadas. Usá /notas para verlas.{RESET}")

                                print(f"\n[!] Comandos: /tareas, /subir [ID], /mis_entregas, /notas, /borrar [ID], ENTER para salir.")

                            # 3. BUCLE INTERACTIVO DE LA SALA
                            while True:
                                txt = input("Sala >> ").strip()
                                if not txt: 
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
                                        print("\n[!] No hay tareas pendientes en esta sala.")

                                elif txt == "/notas" and mi_rol != "profesor":
                                    sock.send(b"GET_GRADES")
                                    n_res = res_q.get().split("|")
                                    if len(n_res) > 1 and n_res[1] != "VACIO":
                                        print("\n--- 🎓 MIS CALIFICACIONES ---")
                                        for n in n_res[1:]:
                                            p = n.split("§")
                                            print(f"📌 {p[0]} | ⭐ Nota: {p[1]} | 📅 Fecha: {p[2]}")
                                    else:
                                        print("\n[!] Aún no tenés notas corregidas.")

                                elif txt.startswith("/borrar"):
                                    parts = txt.split(" ")
                                    # Verificamos que se haya pasado un ID y que no sea una cadena vacía
                                    if len(parts) >= 2 and parts[1].strip():
                                        id_obj = parts[1].strip()
                                        
                                        # Validación extra: asegurarse de que el ID sea numérico para evitar errores de tipo
                                        if not id_obj.isdigit():
                                            print(f"{RED}[!] Error: El ID debe ser un número.{RESET}")
                                            continue

                                        cmd = "BORRAR_TAREA" if mi_rol == "profesor" else "BORRAR_ENTREGA"
                                        sock.send(f"{cmd}|{id_obj}".encode())
                                        
                                        # Esperamos la confirmación del servidor
                                        respuesta_borrar = res_q.get()
                                        if "OK" in respuesta_borrar:
                                            print(f"{GREEN}✅ [S] El elemento con ID {id_obj} fue eliminado correctamente.{RESET}")
                                        else:
                                            print(f"{RED}[!] No se pudo borrar: {respuesta_borrar}{RESET}")
                                    else:
                                        # Si el ID está vacío o no se proporcionó
                                        print(f"{YELLOW}[!] Error: Debes especificar un ID. Uso: /borrar [ID]{RESET}")

                                # --- COMANDOS PROFESOR ---
                                elif txt == "/nueva" and mi_rol == "profesor":
                                    titulo = input("Título: ").strip()
                                    descripcion = input("Descripción: ").strip()
                                    fecha = input("Fecha (YYYY-MM-DD HH:MM): ").strip()
                                    if titulo and descripcion and fecha:
                                        sock.send(f"CREAR_TAREA|{titulo}|{descripcion}|{fecha}".encode())
                                        res_q.get()
                                    else: print(f"{RED}[!] Error: Campos vacíos.{RESET}")

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
                                        eid, nota = parts[1], parts[2]
                                        if nota.isdigit() and 1 <= int(nota) <= 10:
                                            sock.send(f"GRADE|{eid}|{nota}".encode())
                                            res_q.get()
                                            print(f"{GREEN}[S] Calificado.{RESET}")
                                    else: print(f"{YELLOW}[!] Uso: /corregir [ID] [NOTA]{RESET}")

                                # --- COMANDOS ALUMNO ---
                                elif txt.startswith("/subir") and mi_rol != "profesor":
                                    parts = txt.split(" ")
                                    if len(parts) >= 2:
                                        tp_id = parts[1]
                                        cont = input(f"Contenido para TP {tp_id}: ").strip()
                                        if cont:
                                            sock.send(f"SUBIR_ENTREGA|{tp_id}|{cont}".encode())
                                            res_q.get()
                                            print(f"{GREEN}[S] Enviado.{RESET}")
                                    else: print(f"{YELLOW}[!] Uso: /subir [ID_TAREA]{RESET}")

                                # --- NUEVA FUNCIÓN: VER MIS ENTREGAS ---
                                elif txt == "/mis_entregas" and mi_rol != "profesor":
                                    sock.send(f"GET_MY_SUBMISSIONS|{tid}".encode())
                                    m_res = res_q.get().split("|")
                                    if len(m_res) > 1 and m_res[1] != "VACIO":
                                        print("\n--- MIS ENTREGAS (PENDIENTES DE CORRECCIÓN) ---")
                                        for ent in m_res[1:]:
                                            eid, etit, efec = ent.split("§")
                                            print(f"🆔 ID ENTREGA: {eid} | 📌 Tarea: {etit} | 📅 Enviado: {efec}")
                                        print(f"\n{YELLOW}[!] Si querés anular una, usá: /borrar [ID ENTREGA]{RESET}")
                                    else:
                                        print("\n[!] No tenés entregas pendientes de corregir en esta sala.")

                                # --- CHAT ---
                                else: 
                                    sock.send(f"SEND_MSG|{txt}".encode())
                                    res_q.get()

                        elif "ERROR" in respuesta:
                            print(f"{RED}[!] Error al entrar: {d_join[-1]}{RESET}")
                            input("Presioná Enter para continuar...")

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
                    nombre = input("Nombre de la sala: ").strip()
                    if nombre and nombre != "0":
                        desc = input("Descripción: ").strip()
                        sock.send(f"CREATE_SALA|{nombre}|{desc}".encode())
                        resp_s = res_q.get().split("|")
                        if resp_s[1] == "OK": print(f"{GREEN}Sala creada.{RESET}")
                        else: print(f"{RED}Error: {resp_s[-1]}{RESET}")

                elif opc == "4": 
                    sock.send(b"QUIT") 
                    print(f"{YELLOW}¡Hasta luego! 🍇{RESET}")
                    break
        else:
            msg_err = auth_data.split("|")[-1] if "|" in auth_data else auth_data
            print(f"[!] Error de acceso: {msg_err}")

    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__": 
    main()