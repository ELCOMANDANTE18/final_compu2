import asyncio, os, datetime, aiomysql
from multiprocessing import Process, Pipe
from dotenv import load_dotenv

# Importamos el punto de entrada del worker
from src.processes.auth import start_auth_process

load_dotenv()

# --- CLASE DE PERSISTENCIA (Movida desde database_logic.py) ---
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

    async def get_tasks(self, room_id):
        async with self.conn.cursor() as cur:
            query = "SELECT titulo, descripcion, DATE_FORMAT(fecha_entrega, '%%Y-%%m-%%d %%H:%%i') FROM tareas WHERE id_sala = %s"
            await cur.execute(query, (int(room_id),))
            res = await cur.fetchall()
            return "|".join([f"{r[0]}§{r[1]}§{r[2]}" for r in res]) if res else "VACIO"

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

# --- LÓGICA DEL SERVIDOR ---
pending_auths, active_sessions = {}, {}

def log(tag, msg):
    """Imprime logs con timestamp para monitoreo en terminal."""
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
    """Recibe respuestas del worker auth.py y responde al cliente."""
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
                    log("CMD", f"[{u}] Uniéndose a sala {m.split('|')[1]}")
                    pipe_conn.send({"type": "JOIN_SALA", "id_sala": m.split("|")[1], "id_user": sess['user_id'], "user": u})
                
                elif m.startswith("SEND_MSG|"):
                    log("CHAT", f"[{u}] Mensaje en sala {sess['id_sala']}")
                    pipe_conn.send({"type": "SAVE_MSG", "id_sala": sess['id_sala'], "id_user": sess['user_id'], "msg": m.split("|")[1]})
                    await broadcast(m.split("|")[1], sess['id_sala'], writer, u)
                    writer.write(b"DATA_RES|OK\n")
                
                elif m == "GET_TASKS":
                    log("CMD", f"[{u}] Solicitando tareas")
                    pipe_conn.send({"type": "GET_TASKS", "id_sala": sess['id_sala'], "id_user": sess['user_id'], "user": u})

                elif m.startswith("CREATE_SALA|"):
                    if sess['rol'] == 'profesor':
                        p = m.split("|")
                        log("CMD", f"[{u}] Creando sala: {p[1]}")
                        pipe_conn.send({"type": "CREATE_SALA", "nombre": p[1], "descripcion": p[2], "id_user": sess['user_id'], "user": u})
                    else:
                        writer.write(b"DATA_RES|ERROR|Solo profesores pueden crear salas\n")

                elif m == "LIST_USERS":
                    # Lógica local del servidor (no requiere DB)
                    users = ",".join([s['username'] for s in active_sessions.values()])
                    writer.write(f"LISTA|{users if users else 'VACIO'}\n".encode())
                
                elif m.startswith("LIST_"):
                    log("CMD", f"[{u}] Listado: {m}")
                    pipe_conn.send({"type": m, "id_user": sess['user_id'], "user": u})
                
                elif m == "LEAVE_ROOM":
                    log("ROOM", f"[{u}] Salió de la sala {sess['id_sala']}")
                    sess['id_sala'] = "Ninguna"
                    writer.write(b"DATA_RES|LEAVE\n")
                
                pending_auths[u] = writer
            else:
                p = m.split("|")
                if len(p) >= 3:
                    log("AUTH", f"Petición {p[0]} para: {p[1]}")
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
    os.system('clear' if os.name == 'posix' else 'cls')
    print_banner()

    parent_conn, child_conn = Pipe()
    db_proc = Process(target=start_auth_process, args=(child_conn,), daemon=True)
    db_proc.start()
    log("SYSTEM", f"Worker auth.py iniciado (PID: {db_proc.pid})")

    loop = asyncio.get_running_loop()
    loop.add_reader(parent_conn.fileno(), handle_auth_response, parent_conn)

    server = await asyncio.start_server(lambda r, w: handle_client(r, w, parent_conn), "0.0.0.0", 5000)
    log("SERVER", "Escuchando en 0.0.0.0:5000")

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("SYSTEM", "Servidor finalizado.")