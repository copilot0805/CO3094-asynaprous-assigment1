#
# Copyright (C) 2026 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# AsynapRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#


"""Sample RESTful app and tracker service for the assignment."""

import os
import json
import sqlite3
import atexit
import signal
import sys

from daemon.asynaprous import AsynapRous

app = AsynapRous()

# SQLite shared state (standard library, no external deps)
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "peers.db")
RESET_DB_ON_STARTUP = os.getenv("ASYNAPROUS_RESET_TRACKER_DB", "1") != "0"


def reset_db_on_startup():
    """Remove any existing DB file before initializing the tracker.

    This prevents stale peers from previous runs when the process was force-killed
    and exit handlers (atexit/signal) did not get a chance to run.
    """
    if not RESET_DB_ON_STARTUP:
        return

    try:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            print(f"[Tracker] Reset DB file on startup: {DB_PATH}")
    except Exception as e:
        print(f"[Tracker] Failed to reset DB file {DB_PATH} on startup: {e}")


def cleanup_db():
    """Remove the peer tracking DB on process exit.

    Notes:
    - This will run on graceful shutdown paths (e.g., Ctrl+C / SIGTERM / normal exit).
    - If the terminal is force-killed, Python may not get a chance to run cleanup.
    """
    try:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            print(f"[Tracker] Cleaned up DB file: {DB_PATH}")
    except Exception as e:
        print(f"[Tracker] Failed to remove DB file {DB_PATH}: {e}")


def _install_exit_handlers():
    atexit.register(cleanup_db)

    def _handle_signal(signum, frame):
        cleanup_db()
        raise SystemExit(0)

    try:
        signal.signal(signal.SIGINT, _handle_signal)
    except Exception:
        pass
    try:
        signal.signal(signal.SIGTERM, _handle_signal)
    except Exception:
        pass


_install_exit_handlers()

def init_db():
    """Initialize the SQLite database for peer tracking."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS peers (
                username TEXT PRIMARY KEY,
                ip TEXT NOT NULL,
                port INTEGER NOT NULL
            )
            """
        )

def upsert_peer(username, ip, port):
    """Insert or update a peer in the database."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO peers(username, ip, port) VALUES(?, ?, ?)"
            " ON CONFLICT(username) DO UPDATE SET ip=excluded.ip, port=excluded.port",
            (username, ip, port),
        )

def get_all_peers():
    """Return all peers from the database."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT username, ip, port FROM peers").fetchall()
    return {row[0]: {"ip": row[1], "port": row[2]} for row in rows}

# @app.route('/login', methods=['POST'])
# def login(request, *args, **kwargs):    
#     """
#     Handle user login via POST request.

#     This route simulates a login process and prints the provided headers and body
#     to the console.

#     :param headers (str): The request headers or user identifier.
#     :param body (str): The request body or login payload.
#     """
#     actual_body = request.body
#     print(f"[SampleApp] Logging in with request body: {actual_body}")
#     data = {
#         "message": "Welcome to the RESTful TCP WebApp",
#         "received": actual_body,
#     }

#     # Convert to JSON string
#     json_str = json.dumps(data)
#     return (json_str.encode("utf-8"))

# @app.route("/echo", methods=["POST"])
# def echo(request, *args, **kwargs):
#     """Echo back JSON payloads or report an error."""
#     actual_body = request.body
#     print(f"[SampleApp] received body {actual_body}")

#     try:
#         if actual_body:
#             message = json.loads(actual_body)
#         else:
#             message = "No body received"
#         data = {"received": message}
#         json_str = json.dumps(data)
#         return (json_str.encode("utf-8"))
#     except json.JSONDecodeError:
#         data = {"error": "Invalid JSON format"}
#         json_str = json.dumps(data)
#         return (json_str.encode("utf-8"))


# @app.route('/hello', methods=['PUT'])
# async def hello(request, *args, **kwargs):
#     """
#     Handle greeting via PUT request.

#     This route prints a greeting message to the console using the provided headers
#     and body.

#     :param headers (str): The request headers or user identifier.
#     :param body (str): The request body or message payload.
#     """
#     actual_body = request.body
#     print(f"[SampleApp] ['PUT'] **ASYNC** Hello received: {actual_body}")
#     data =  {"id": 1, "name": "Alice", "email": "alice@example.com"}

#     # Convert to JSON string
#     json_str = json.dumps(data)
#     return (json_str.encode("utf-8"))

# Tracker server
@app.route('/submit-info', methods=['POST'])
def submit_info(request, *args, **kwargs):
    """
    Register a peer and store its IP/port in the tracker.
    """
    # Vì HttpAdapter truyền đối tượng Request vào, ta lấy body trực tiếp từ nó!
    actual_body = request.body
    print(f"[Tracker] Received submit-info request with body: {actual_body}")
    
    try:
        data = json.loads(actual_body)
        username = data.get('username')
        if username:
            upsert_peer(username, data.get('ip'), data.get('port'))
            print(f"[Tracker] Registered peer: {username}")
            response_data = {
                "message": f"Peer {username} registered successfully",
                "status": "success",
            }
        else:
            response_data = {"error": "Missing username in JSON payload"}
    except json.JSONDecodeError:
        response_data = {"error": "Invalid JSON format"}
    except Exception as e:
        response_data = {"error": str(e)}

    return response_data

@app.route('/remove-info', methods=['POST'])
def remove_info(request, *args, **kwargs):
    """Xóa một peer khỏi cơ sở dữ liệu khi họ Offline/Logout."""
    actual_body = request.body.decode('utf-8') if isinstance(request.body, bytes) else request.body
    print(f"[Tracker] Received remove-info request: {actual_body}")
    
    try:
        data = json.loads(actual_body)
        username = data.get('username')
        if username:
            # Kết nối vào SQLite và xóa Peer
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM peers WHERE username = ?", (username,))
            conn.commit()
            conn.close()
            
            print(f"[Tracker] Đã xóa peer: {username}")
            return {"status": "success", "message": f"Peer {username} removed"}
        else:
            return {"error": "Missing username in JSON payload"}
    except Exception as e:
        return {"error": str(e)}

# @app.route('/add-list', methods=['POST'])
# def add_list(request, *args, **kwargs):
#     """
#     Compatibility endpoint: behaves like submit-info for peer registration.
#     """
#     return submit_info(request, *args, **kwargs)

@app.route('/get-list', methods=['GET'])
def get_list(request, *args, **kwargs):
    """
    Peer Discovery: Return the list of active peers to the chat application.
    """
    peers = get_all_peers()
    print(f"[Tracker] Received get-list request. Now ACTIVE_PEERS: {len(peers)}")
    return peers

def create_sampleapp(ip, port):
    """Prepare and launch the RESTful application."""
    reset_db_on_startup()
    init_db()
    app.prepare_address(ip, port)
    app.run()

