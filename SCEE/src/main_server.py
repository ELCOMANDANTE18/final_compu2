import asyncio, os, argparse
from multiprocessing import Process, Pipe
from dotenv import load_dotenv
from processes.auth import start_auth_process

load_dotenv()

pending_auths, active_sessions = {}, {}

async def broadcast_to_room(message, room_id, sender_username, sender_writer):
    """Difusión de mensajes en tiempo real filtrada por ID de sala."""
    payload = f"CHAT|{sender_username}|{message}\n".encode()
    count = 0
    for writer, session in active_sessions.items():
        if str(session.get('id_sala')) == str(room_id) and writer != sender_writer:
            writer.write(payload)
            await writer.drain()
            count += 1
    return count

def handle_auth_response(pipe_conn):
    if pipe_conn.poll():
        response = pipe_conn.recv()
        username, status, tipo = response.get("user_requested"), response.get("status"), response.get("type")
        writer = pending_auths.pop(username, None)
        
        if writer:
            if status == "OK":
                if tipo == "LIST_RES": msg = f"SALAS_LIST|{response.get('data')}\n"
                elif tipo == "MY_SALAS_RES": msg = f"MY_SALAS_LIST|{response.get('data')}\n"
                elif tipo == "JOIN_RES":
                    active_sessions[writer]["id_sala"] = response.get("id_sala")
                    msg = f"JOIN_OK|{response.get('id_sala')}\n"
                    print(f"[SALA] {username} entró a la sala {response.get('id_sala')}")
                elif tipo == "SALA_CREATED":
                    msg = "OK|201|Sala creada\n"
                    print(f"[DB] {username} creó una nueva sala exitosamente")
                elif tipo == "LOGIN_RES":
                    active_sessions[writer] = {"user_id": response.get("user_id"), "username": username, "rol": response.get("role"), "id_sala": "Ninguna"}
                    msg = f"AUTH_RES|200|{username}|{response.get('role')}\n"
                    print(f"[SESIÓN] {username} ({response.get('role')}) conectado")
            else:
                msg = f"ERROR|401|{response.get('message')}\n"
            
            writer.write(msg.encode())
            asyncio.create_task(writer.drain())

async def handle_client(reader, writer, pipe_conn):
    try:
        while True:
            data = await reader.read(1024)
            if not data: break
            message = data.decode().strip()
            session = active_sessions.get(writer)

            if not session:
                p = message.split("|")
                if len(p) >= 3 and p[0] == "LOGIN":
                    pending_auths[p[1]] = writer
                    pipe_conn.send({"type": "LOGIN", "user": p[1], "pass": p[2]})
            else:
                if message == "LIST_AVAILABLE":
                    pipe_conn.send({"type": "LIST_AVAILABLE", "id_user": session['user_id'], "user": session['username']})
                    pending_auths[session['username']] = writer
                elif message == "LIST_MY_SALAS":
                    pipe_conn.send({"type": "LIST_MY_SALAS", "id_user": session['user_id'], "user": session['username']})
                    pending_auths[session['username']] = writer
                elif message.startswith("SEND_MSG|"):
                    txt = message.split("|")[1]
                    c = await broadcast_to_room(txt, session['id_sala'], session['username'], writer)
                    print(f"[CHAT] {session['username']} (Sala {session['id_sala']}): {txt} -> {c} receptores")
                    writer.write(b"OK|200|Enviado\n")
                elif message == "LEAVE_ROOM":
                    old = session['id_sala']
                    session['id_sala'] = "Ninguna"
                    print(f"[SALA] {session['username']} salió de la sala {old}")
                    writer.write(b"OK|200|Menu\n")
                elif message.startswith("CREATE_SALA|"):
                    parts = message.split("|")
                    pipe_conn.send({"type": "CREATE_SALA", "nombre": parts[1], "descripcion": parts[2], "id_creador": session['user_id'], "user": session['username']})
                    pending_auths[session['username']] = writer
                elif message.startswith("JOIN|"):
                    pipe_conn.send({"type": "JOIN_SALA", "id_sala": message.split("|")[1], "id_user": session['user_id'], "user": session['username']})
                    pending_auths[session['username']] = writer
            await writer.drain()
    finally:
        u = active_sessions.pop(writer, None)
        if u: print(f"[-] Desconectado: {u['username']}")
        writer.close()

async def main():
    loop = asyncio.get_running_loop()
    p_conn, c_conn = Pipe()
    Process(target=start_auth_process, args=(c_conn,), daemon=True).start()
    loop.add_reader(p_conn.fileno(), handle_auth_response, p_conn)
    server = await asyncio.start_server(lambda r, w: handle_client(r, w, p_conn), "127.0.0.1", 5000)
    print("="*50 + "\n   SERVER SCEE - MENDOZA ACTIVO\n" + "="*50)
    async with server: await server.serve_forever()

if __name__ == "__main__": asyncio.run(main())