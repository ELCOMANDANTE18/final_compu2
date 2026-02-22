import asyncio, os, argparse, datetime
from multiprocessing import Process, Pipe
from dotenv import load_dotenv
from processes.auth import start_auth_process

load_dotenv()
pending_auths, active_sessions = {}, {}

def log(tag, msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{tag}] {msg}")

async def broadcast(message, room_id, sender_writer, sender_name):
    payload = f"CHAT|{sender_name}|{message}\n".encode()
    for writer, sess in active_sessions.items():
        if str(sess.get('id_sala')) == str(room_id) and writer != sender_writer:
            try: writer.write(payload); await writer.drain()
            except: continue

def handle_auth_response(pipe_conn):
    if pipe_conn.poll():
        res = pipe_conn.recv()
        user, status, tipo = res.get("user_requested"), res.get("status"), res.get("type")
        writer = pending_auths.pop(user, None)
        if writer:
            if status == "OK":
                if tipo == "JOIN_RES": 
                    active_sessions[writer]["id_sala"] = res.get("id_sala")
                    msg = f"JOIN_OK|{res.get('id_sala')}|{res.get('history')}\n"
                elif tipo in ["LOGIN_RES", "AUTH_RES"]:
                    active_sessions[writer] = {"user_id": res.get("user_id"), "username": user, "rol": res.get("role"), "id_sala": "Ninguna"}
                    msg = f"AUTH_RES|200|{user}|{res.get('role')}\n"
                else: msg = f"{tipo}|{res.get('data', 'OK')}\n"
            else: msg = f"ERROR|400|{res.get('message')}\n"
            writer.write(msg.encode()); asyncio.create_task(writer.drain())

async def handle_client(reader, writer, pipe_conn):
    try:
        while True:
            data = await reader.read(1024)
            if not data: break
            m = data.decode().strip(); sess = active_sessions.get(writer)
            if sess:
                u = sess['username']
                if m.startswith("JOIN|"): pipe_conn.send({"type": "JOIN_SALA", "id_sala": m.split("|")[1], "id_user": sess['user_id'], "user": u})
                elif m.startswith("SEND_MSG|"):
                    pipe_conn.send({"type": "SAVE_MSG", "id_sala": sess['id_sala'], "id_user": sess['user_id'], "msg": m.split("|")[1]})
                    await broadcast(m.split("|")[1], sess['id_sala'], writer, u); writer.write(b"DATA_RES|OK\n")
                elif m == "GET_TASKS": pipe_conn.send({"type": "GET_TASKS", "id_sala": sess['id_sala'], "id_user": sess['user_id'], "user": u})
                elif m.startswith("LIST_"): pipe_conn.send({"type": m, "id_user": sess['user_id'], "user": u})
                elif m == "LEAVE_ROOM": sess['id_sala'] = "Ninguna"; writer.write(b"DATA_RES|LEAVE\n")
                pending_auths[u] = writer
            else:
                p = m.split("|")
                if len(p) >= 3: pending_auths[p[1]] = writer; pipe_conn.send({"type": p[0], "user": p[1], "pass": p[2], "rol": p[3] if len(p)>3 else "alumno"})
            await writer.drain()
    finally:
        u = active_sessions.pop(writer, None); writer.close()

async def main():
    p_conn, c_conn = Pipe(); Process(target=start_auth_process, args=(c_conn,), daemon=True).start()
    loop = asyncio.get_running_loop(); loop.add_reader(p_conn.fileno(), handle_auth_response, p_conn)
    server = await asyncio.start_server(lambda r, w: handle_client(r, w, p_conn), "127.0.0.1", 5000)
    print("--- SERVER SCEE ACTIVO (MENDOZA) ---")
    async with server: await server.serve_forever()

if __name__ == "__main__": asyncio.run(main())