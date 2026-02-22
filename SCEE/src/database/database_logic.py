import aiomysql
import os

class DatabaseManager:
    def __init__(self):
        self.conn = None

    async def connect(self):
        self.conn = await aiomysql.connect(
            host=os.getenv("DB_HOST"), port=3306,
            user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME"), autocommit=True
        )

    async def login(self, user, password):
        async with self.conn.cursor() as cur:
            await cur.execute("SELECT id, rol FROM usuarios WHERE username=%s AND password_hash=%s", (user, password))
            return await cur.fetchone()

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
            if not await cur.fetchone():
                return None
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