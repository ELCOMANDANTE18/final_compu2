import asyncio, os, datetime, aiomysql, argparse
from multiprocessing import Process, Pipe
from dotenv import load_dotenv

# Importamos el punto de entrada del worker
from src.processes.auth import start_auth_process

load_dotenv()

# --- CLASE DE PERSISTENCIA ---
class DatabaseManager:
    def __init__(self):
        self.conn = None

    async def connect(self):
        """Establece la conexión con MariaDB."""
        self.conn = await aiomysql.connect(
            host=os.getenv("DB_HOST", "localhost"), port=3306,
            user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME"), autocommit=True
        )

    async def login(self, user, password):
        async with self.conn.cursor() as cur:
            await cur.execute("SELECT id, rol FROM usuarios WHERE username=%s AND password_hash=%s", (user, password))
            return await cur.fetchone()

    async def register(self, user, password, rol):
        async with self.conn.cursor() as cur:
            await cur.execute("SELECT id FROM usuarios WHERE username = %s", (user,))
            if await cur.fetchone():
                return False, "El usuario ya existe."
            try:
                query = "INSERT INTO usuarios (username, password_hash, rol) VALUES (%s, %s, %s)"
                await cur.execute(query, (user, password, rol))
                return True, cur.lastrowid
            except Exception as e:
                return False, str(e)

    async def create_room(self, nombre, descripcion, creator_id):
        async with self.conn.cursor() as cur:
            query = "INSERT INTO salas (nombre, descripcion, id_creador) VALUES (%s, %s, %s)"
            await cur.execute(query, (nombre, descripcion, int(creator_id)))
            room_id = cur.lastrowid
            await cur.execute("INSERT IGNORE INTO miembros_sala (id_usuario, id_sala) VALUES (%s, %s)", (int(creator_id), room_id))
            return True

    async def save_submission(self, tp_id, alumno_id, content):
        async with self.conn.cursor() as cur:
            query = """
                INSERT INTO entregas (id_tp, id_alumno, contenido, estado) 
                VALUES (%s, %s, %s, 'entregado')
            """
            await cur.execute(query, (int(tp_id), int(alumno_id), content))
            return True

    async def get_tasks(self, room_id, user_id):
        async with self.conn.cursor() as cur:
            query = """
                SELECT t.id, t.titulo, t.descripcion, DATE_FORMAT(t.fecha_entrega, '%%Y-%%m-%%d %%H:%%i')
                FROM tareas t
                LEFT JOIN entregas e ON t.id = e.id_tp AND e.id_alumno = %s
                WHERE t.id_sala = %s AND e.id IS NULL
            """
            await cur.execute(query, (int(user_id), int(room_id)))
            res = await cur.fetchall()
            return "|".join([f"{r[0]}§{r[1]}§{r[2]}§{r[3]}" for r in res]) if res else "VACIO"  

    async def save_message(self, room_id, user_id, msg):
        async with self.conn.cursor() as cur:
            await cur.execute("INSERT INTO mensajes (id_sala, id_usuario, contenido) VALUES (%s, %s, %s)", 
                            (int(room_id), int(user_id), msg))

    async def join_room(self, user_id, room_id):
        async with self.conn.cursor() as cur:
            await cur.execute("SELECT id FROM salas WHERE id = %s", (int(room_id),))
            if not await cur.fetchone(): return None
            await cur.execute("INSERT IGNORE INTO miembros_sala (id_usuario, id_sala) VALUES (%s, %s)", (int(user_id), int(room_id)))
            await cur.execute("SELECT u.username, m.contenido FROM mensajes m JOIN usuarios u ON m.id_usuario = u.id WHERE m.id_sala = %s ORDER BY m.fecha ASC LIMIT 20", (int(room_id),))
            res = await cur.fetchall()
            return "|".join([f"{r[0]}:{r[1]}" for r in res]) if res else "VACIO"

    async def list_rooms(self, user_id, action):
        async with self.conn.cursor() as cur:
            cond = "NOT IN" if action == "LIST_AVAILABLE" else "IN"
            q = f"SELECT id, nombre FROM salas WHERE id {cond} (SELECT id_sala FROM miembros_sala WHERE id_usuario = %s)"
            await cur.execute(q, (int(user_id),))
            r_list = await cur.fetchall()
            return ",".join([f"{r[0]}:{r[1]}" for r in r_list]) if r_list else "VACIO"

    async def list_submissions(self, room_id):
        async with self.conn.cursor() as cur:
            query = """
                SELECT e.id, u.username, t.titulo, e.contenido 
                FROM entregas e
                JOIN usuarios u ON e.id_alumno = u.id
                JOIN tareas t ON e.id_tp = t.id
                WHERE t.id_sala = %s AND e.estado = 'entregado'
            """
            await cur.execute(query, (int(room_id),))
            res = await cur.fetchall()
            return "|".join([f"{r[0]}§{r[1]}§{r[2]}§{r[3]}" for r in res]) if res else "VACIO"

    async def grade_submission(self, submission_id, grade):
        async with self.conn.cursor() as cur:
            await cur.execute(
                "UPDATE entregas SET estado = 'corregido', calificacion = %s WHERE id = %s",
                (int(grade), int(submission_id))
            )
            return True

    async def get_grades(self, user_id):
        async with self.conn.cursor() as cur:
            query = """
                SELECT t.titulo, e.calificacion, DATE_FORMAT(e.fecha_entrega, '%%d/%%m %%H:%%i')
                FROM entregas e
                JOIN tareas t ON e.id_tp = t.id
                WHERE e.id_alumno = %s AND e.estado = 'corregido'
            """
            await cur.execute(query, (int(user_id),))
            res = await cur.fetchall()
            return "|".join([f"{r[0]}§{r[1]}§{r[2]}" for r in res]) if res else "VACIO"    

# --- LÓGICA DEL SERVIDOR ---
pending_auths, active_sessions = {}, {}

def log(tag, msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{tag}] {msg}")

async def broadcast(message, room_id, sender_writer, sender_name):
    payload = f"CHAT|{sender_name}|{message}\n".encode()
    for writer, sess in active_sessions.items():
        if str(sess.get('id_sala')) == str(room_id) and writer != sender_writer:
            try: 
                writer.write(payload)
                await writer.drain()
            except: continue

def handle_auth_response(pipe_conn):
    if pipe_conn.poll():
        res = pipe_conn.recv()
        user, status, tipo = res.get("user_requested"), res.get("status"), res.get("type")
        writer = pending_auths.pop(user, None)
        
        log("DATABASE", f"Resultado para {user}: {status} | Acción: {tipo}")

        if writer:
            if status == "OK":
                if tipo == "JOIN_RES": 
                    active_sessions[writer]["id_sala"] = res.get("id_sala")
                    msg = f"JOIN_OK|{res.get('id_sala')}|{res.get('history')}\n"
                elif tipo in ["LOGIN_RES", "AUTH_RES"]:
                    active_sessions[writer] = {"user_id": res.get("user_id"), "username": user, "rol": res.get("role"), "id_sala": "Ninguna"}
                    msg = f"AUTH_RES|200|{user}|{res.get('role')}\n"
                    log("AUTH", f"Sesión iniciada: {user}")
                else: 
                    msg = f"{tipo}|{res.get('data', 'OK')}\n"
            else: 
                msg = f"ERROR|400|{res.get('message')}\n"
            
            writer.write(msg.encode())
            asyncio.create_task(writer.drain())

async def handle_client(reader, writer, pipe_conn):
    addr = writer.get_extra_info('peername')
    log("NETWORK", f"Nueva conexión: {addr}")

    try:
        while True:
            data = await reader.read(1024)
            if not data: break
            
            m = data.decode().strip()
            sess = active_sessions.get(writer)
            
            if sess:
                u = sess['username']
                if m.startswith("JOIN|"):
                    pipe_conn.send({"type": "JOIN_SALA", "id_sala": m.split("|")[1], "id_user": sess['user_id'], "user": u})
                elif m.startswith("SEND_MSG|"):
                    pipe_conn.send({"type": "SAVE_MSG", "id_sala": sess['id_sala'], "id_user": sess['user_id'], "msg": m.split("|")[1]})
                    await broadcast(m.split("|")[1], sess['id_sala'], writer, u)
                    writer.write(b"DATA_RES|OK\n")
                elif m.startswith("CREATE_SALA|"):
                    if sess['rol'] == 'profesor':
                        p = m.split("|")
                        pipe_conn.send({"type": "CREATE_SALA", "nombre": p[1], "descripcion": p[2], "id_user": sess['user_id'], "user": u})
                    else:
                        writer.write(b"DATA_RES|ERROR|Solo profesores pueden crear salas\n")
                elif m == "LIST_USERS":
                    users = ",".join([s['username'] for s in active_sessions.values()])
                    writer.write(f"LISTA|{users if users else 'VACIO'}\n".encode())
                elif m in ["LIST_AVAILABLE", "LIST_MY_SALAS"]:
                    pipe_conn.send({"type": m, "id_user": sess['user_id'], "user": u})
                elif m.startswith("CREAR_TAREA|"):
                    if sess['rol'].lower() == 'profesor':
                        p = m.split("|")
                        pipe_conn.send({"type": "CREATE_TASK", "id_sala": sess['id_sala'], "titulo": p[1], "descripcion": p[2], "fecha": p[3], "user": u})
                elif m == "GET_TASKS":
                    pipe_conn.send({"type": "GET_TASKS", "id_sala": sess['id_sala'], "id_user": sess['user_id'], "rol": sess['rol'], "user": u})
                elif m == "GET_GRADES":
                    pipe_conn.send({"type": "GET_GRADES", "id_user": sess['user_id'], "user": u})    
                elif m == "LIST_SUBMISSIONS" and sess['rol'] == 'profesor':
                    pipe_conn.send({"type": "LIST_SUBMISSIONS", "id_sala": sess['id_sala'], "user": u})
                elif m.startswith("GRADE|") and sess['rol'] == 'profesor':
                    _, s_id, nota = m.split("|")
                    pipe_conn.send({"type": "GRADE_SUBMISSION", "s_id": s_id, "grade": nota, "user": u})
                elif m.startswith("SUBIR_ENTREGA|"):
                    partes = m.split("|", 2)
                    if len(partes) >= 3:
                        pipe_conn.send({"type": "SAVE_SUBMISSION", "tp_id": partes[1], "id_user": sess['user_id'], "content": partes[2], "user": u})
                elif m == "LEAVE_ROOM":
                    sess['id_sala'] = "Ninguna"
                    writer.write(b"DATA_RES|LEAVE\n")
                
                pending_auths[u] = writer
            else:
                p = m.split("|")
                if len(p) >= 3:
                    pending_auths[p[1]] = writer
                    pipe_conn.send({"type": p[0], "user": p[1], "pass": p[2], "rol": p[3] if len(p)>3 else "alumno"})
            
            await writer.drain()
    except Exception as e:
        log("ERROR", f"Error con {addr}: {e}")
    finally:
        u = active_sessions.pop(writer, None)
        if u: log("NETWORK", f"Desconectado: {u['username']}")
        writer.close()

def print_banner():
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
    print("="*42 + "\n SCEE - Sede Mendoza 🍇📍\n" + "="*42)

async def main():
    parser = argparse.ArgumentParser(description="Servidor SCEE - Mendoza")
    parser.add_argument("--port", type=int, default=int(os.getenv("SERVER_PORT", 5000)), help="Puerto del servidor")
    args = parser.parse_args()

    os.system('clear' if os.name == 'posix' else 'cls')
    print_banner()

    # IPC y Proceso Worker (Mantiene la arquitectura original)
    parent_conn, child_conn = Pipe()
    db_proc = Process(target=start_auth_process, args=(child_conn,), daemon=True)
    db_proc.start()
    log("SYSTEM", f"Worker auth.py iniciado (PID: {db_proc.pid})")

    loop = asyncio.get_running_loop()
    loop.add_reader(parent_conn.fileno(), handle_auth_response, parent_conn)

    # --- NUEVO: Inicio del Servidor con soporte Dual Stack real ---
    try:
        # Al usar host=None, el servidor escucha en TODAS las interfaces (IPv4 e IPv6)
        server = await asyncio.start_server(
            lambda r, w: handle_client(r, w, parent_conn), 
            host=None, 
            port=args.port,
            reuse_address=True
        )
        log("SERVER", f"Escuchando en puerto {args.port} (MODO DUAL STACK IPv4/IPv6)")
    except Exception as e:
        log("ERROR", f"No se pudo iniciar el servidor: {e}")
        return

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("SYSTEM", "Servidor finalizado.")