"""Peer node for the hybrid chat application."""
import json
import os
import sys
import threading
import time
import urllib.request
import uuid

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CURRENT_DIR))

from daemon.asynaprous import AsynapRous

MY_NAME = sys.argv[1] if len(sys.argv) > 1 else "Ken"
MY_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5001
MY_IP = "127.0.0.1"
TRACKER_URL = "http://127.0.0.1:2026"

app = AsynapRous()

CHANNELS = {"Global": []}
ACTIVE_PEERS = {}
BASIC_PASSWORD = "password"
SESSION = {}  # {token: {"username": ..., "expires_at": ...}}


def _session_cookie_name():
    return f"sessionid_{MY_PORT}"


def parse_json_body(request):
    """Parse JSON from request body, returning a dict or empty dict."""
    body_str = (
        request.body.decode("utf-8")
        if isinstance(request.body, bytes)
        else request.body
    )
    if not body_str:
        return {}
    try:
        return json.loads(body_str)
    except Exception:
        return {}


# ============= SESSION MANAGEMENT (IN-MEMORY) =============
def create_session(username, ip, ttl=3600):
    """Create a session token (ttl in seconds, default 1 hour)."""
    token = str(uuid.uuid4())
    expires = int(time.time()) + ttl
    SESSION[token] = {"username": username, "expires_at": expires, "ip": ip}
    print(f"[Session] Created token for {username}: {token[:8]}... (expires in {ttl}s)")
    return token


def verify_session(token, ip=None):
    """Verify session token; return username if valid, None if expired/not found."""
    if token not in SESSION:
        return None
    sess = SESSION[token]
    if int(time.time()) > sess["expires_at"]:  # expired
        del SESSION[token]
        print(f"[Session] Token {token[:8]}... expired")
        return None
    # Optional: check IP match
    # if ip and sess["ip"] != ip:
    #     return None
    return sess["username"]


def delete_session(token):
    """Delete session token."""
    if token in SESSION:
        del SESSION[token]
        print(f"[Session] Deleted token {token[:8]}...")


def cleanup_sessions():
    """Background task: remove expired sessions every 60 seconds."""
    while True:
        now = int(time.time())
        expired = [tk for tk, s in SESSION.items() if s["expires_at"] <= now]
        for tk in expired:
            del SESSION[tk]
        if expired:
            print(f"[Session] Cleaned up {len(expired)} expired session(s)")
        time.sleep(60)


# ============= AUTHENTICATION =============
def build_unauthorized_response(message="Unauthorized"):
    """Build a 401 response."""
    return (
        {"error": "Unauthorized", "message": message, "redirect": "/login.html"},
        None,
        401,
        {"Content-Type": "application/json"},
    )


def is_authenticated(request):
    """Check if request has valid session."""
    if hasattr(request, "cookies") and request.cookies:
        token = request.cookies.get(_session_cookie_name())
        if token and verify_session(token):
            return True
    return False


# ============= TRACKER FUNCTIONS =============
def register_to_tracker():
    """Register this peer with the tracker."""
    url = f"{TRACKER_URL}/submit-info"
    payload = json.dumps(
        {"username": MY_NAME, "ip": MY_IP, "port": MY_PORT}
    ).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        urllib.request.urlopen(req, timeout=2)
        print(f"[*] {MY_NAME} da dang ky thanh cong voi Tracker.")
    except Exception as e:
        print(f"[!] Loi Tracker: {e}")


def update_peers():
    """Fetch active peers from tracker."""
    global ACTIVE_PEERS
    url = f"{TRACKER_URL}/get-list"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=0.5) as response:
            ACTIVE_PEERS = json.loads(response.read().decode("utf-8"))
    except Exception:
        pass


def send_http_p2p_worker(target_ip, target_port, channel, msg):
    """Send P2P message to another peer."""
    url = f"http://{target_ip}:{target_port}/api/receive"
    payload = json.dumps(
        {"from": MY_NAME, "channel": channel, "msg": msg}
    ).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        pass


# ============= API ROUTES =============
@app.route('/api/login', methods=['POST'])
def api_login(request, *args, **kwargs):
    """Login: create session and return token in cookie."""
    data = parse_json_body(request)
    username = data.get("username", "")
    password = data.get("password", "")
    
    print(f"[HttpAdapter] Login attempt: username={username}")
    
    if username == MY_NAME and password == BASIC_PASSWORD:
        ip = "127.0.0.1"
        token = create_session(username, ip, ttl=3600)  # 1 hour
        cookie_name = _session_cookie_name()
        print(f"[HttpAdapter] Login success for {username}")
        return (
            {"status": "ok", "message": "Logged in"},
            {cookie_name: token},
            200,
            {"Content-Type": "application/json"},
        )
    
    print(f"[HttpAdapter] Login failed for {username}")
    return build_unauthorized_response(f"Sai username hoặc password. Node: {MY_NAME}")


@app.route('/api/logout', methods=['POST'])
def api_logout(request, *args, **kwargs):
    """Logout: delete session token."""
    token = request.cookies.get(_session_cookie_name()) if hasattr(request, "cookies") else None
    if token:
        delete_session(token)
    cookie_name = _session_cookie_name()
    print(f"[HttpAdapter] Logout for {cookie_name}")
    return (
        {"status": "ok", "message": "Logged out"},
        {cookie_name: ""},
        200,
        {"Content-Type": "application/json", "Set-Cookie": f"{cookie_name}=; Max-Age=0; Path=/"},
    )


@app.route('/api/poll', methods=['GET'])
def api_poll(request, *args, **kwargs):
    """Poll: return peers and channels (auth required)."""
    if not is_authenticated(request):
        return build_unauthorized_response()
    
    update_peers()
    return {
        "my_name": MY_NAME,
        "peers": list(ACTIVE_PEERS.keys()),
        "channels": CHANNELS,
    }


@app.route('/api/send', methods=['POST'])
def api_send(request, *args, **kwargs):
    """Send message (auth required)."""
    if not is_authenticated(request):
        return build_unauthorized_response()
    
    data = parse_json_body(request)
    target = data.get("target")
    msg = data.get("message")
    return send_message_to_target(target, msg)


def send_message_to_target(target, msg):
    """Send message to Global or direct peer."""
    if not target or msg is None:
        return {"status": "error", "message": "Missing target or message"}
    
    if target == "Global":
        CHANNELS["Global"].append({"from": MY_NAME, "msg": msg})
        for peer_name, info in ACTIVE_PEERS.items():
            if peer_name != MY_NAME:
                threading.Thread(
                    target=send_http_p2p_worker,
                    args=(info["ip"], info["port"], "Global", msg),
                    daemon=True,
                ).start()
    else:
        if target not in CHANNELS:
            CHANNELS[target] = []
        CHANNELS[target].append({"from": MY_NAME, "msg": msg})
        if target in ACTIVE_PEERS:
            info = ACTIVE_PEERS[target]
            threading.Thread(
                target=send_http_p2p_worker,
                args=(info["ip"], info["port"], target, msg),
                daemon=True,
            ).start()
    
    return {"status": "ok"}


@app.route('/api/receive', methods=['POST'])
def api_receive(request, *args, **kwargs):
    """Receive P2P message (no auth required)."""
    try:
        data = parse_json_body(request)
        sender = data.get("from")
        channel = data.get("channel")
        msg = data.get("msg")
        
        store_channel = "Global" if channel == "Global" else sender
        if store_channel not in CHANNELS:
            CHANNELS[store_channel] = []
        
        CHANNELS[store_channel].append({"from": sender, "msg": msg})
        return {"status": "received"}
    except Exception as e:
        print(f"[!] Loi nhan tin tu P2P: {e}")
        return {"status": "error"}


@app.route('/connect-peer', methods=['POST'])
def connect_peer(request, *args, **kwargs):
    if not is_authenticated(request):
        return build_unauthorized_response()
    update_peers()
    data = parse_json_body(request)
    target = data.get("target")
    if not target or target not in ACTIVE_PEERS:
        return {"status": "error", "message": "Peer not found"}
    return {"status": "ok", "peer": ACTIVE_PEERS[target]}


@app.route('/broadcast-peer', methods=['POST'])
def broadcast_peer(request, *args, **kwargs):
    if not is_authenticated(request):
        return build_unauthorized_response()
    data = parse_json_body(request)
    msg = data.get("message")
    return send_message_to_target("Global", msg)


@app.route('/send-peer', methods=['POST'])
def send_peer(request, *args, **kwargs):
    if not is_authenticated(request):
        return build_unauthorized_response()
    data = parse_json_body(request)
    target = data.get("target")
    msg = data.get("message")
    return send_message_to_target(target, msg)


if __name__ == "__main__":
    app.prepare_address(MY_IP, MY_PORT)
    register_to_tracker()
    
    # Start cleanup background thread
    threading.Thread(target=cleanup_sessions, daemon=True).start()
    
    print(
        f"[*] Node {MY_NAME} chay o cong {MY_PORT}. "
        f"Browser: http://{MY_IP}:{MY_PORT}/login.html"
    )
    app.run()