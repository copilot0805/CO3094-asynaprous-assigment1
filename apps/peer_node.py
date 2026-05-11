"""Peer node for the hybrid chat application."""

import base64
import json
import os
import sys
import threading
import urllib.request

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CURRENT_DIR))

from daemon.asynaprous import AsynapRous

MY_NAME = sys.argv[1] if len(sys.argv) > 1 else "Ken"
MY_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5001
MY_IP = "127.0.0.1"
# Send requests to proxy (8080) with Host header for tracker routing.
TRACKER_URL = "http://127.0.0.1:8080"
TRACKER_HOST = "app2.local"

app = AsynapRous()

CHANNELS = {"Global": []}
ACTIVE_PEERS = {}
BASIC_PASSWORD = "password"


def _session_cookie_name():
    return f"session_{MY_PORT}"


def _encode_cookie_value(username: str, password: str) -> str:
    """Encode credentials into a cookie-safe Base64 string.

    Note: Base64 is NOT encryption; it is only encoding.
    """
    raw = f"{username}:{password}".encode("utf-8")
    # Use URL-safe alphabet to avoid '+' and '/' in cookies.
    encoded = base64.urlsafe_b64encode(raw).decode("ascii")
    # Remove '=' padding to keep cookie compact.
    return encoded.rstrip("=")


def _decode_cookie_value(cookie_val: str):
    """Decode cookie value back to (username, password). Returns None if invalid."""
    try:
        if not cookie_val:
            return None
        # Restore padding
        padded = cookie_val + "=" * ((4 - (len(cookie_val) % 4)) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        if ":" not in decoded:
            return None
        username, password = decoded.split(":", 1)
        return username, password
    except Exception:
        return None


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


def register_to_tracker():
    """Register this peer with the tracker via the proxy."""
    url = f"{TRACKER_URL}/submit-info"
    payload = json.dumps(
        {"username": MY_NAME, "ip": MY_IP, "port": MY_PORT}
    ).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Host", TRACKER_HOST)
        urllib.request.urlopen(req)
        print(f"[*] {MY_NAME} da dang ky thanh cong voi Tracker.")
    except Exception as e:
        print(f"[!] Loi Tracker: {e}")


def update_peers():
    """Fetch active peers from the tracker."""
    global ACTIVE_PEERS
    url = f"{TRACKER_URL}/get-list"
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("Host", TRACKER_HOST)
        with urllib.request.urlopen(req, timeout=0.5) as response:
            ACTIVE_PEERS = json.loads(response.read().decode("utf-8"))
    except Exception:
        pass


def send_http_p2p_worker(target_ip, target_port, channel, msg):
    """Send a P2P message in a background thread."""
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

# =================================================================
# API XỬ LÝ ĐĂNG NHẬP (TASK 2.2) - BASIC + COOKIE AUTH
# =================================================================
def build_unauthorized_response(message="Unauthorized"):
    """Build a 401 response for cookie-based authentication."""
    return (
        {"error": "Unauthorized", "message": message, "redirect": "/login.html"},
        None,
        401,
        {
            "Content-Type": "application/json",
        },
    )


def is_cookie_authenticated(request):
    """Return True if session cookie decodes to valid credentials."""
    if hasattr(request, "cookies") and request.cookies:
        cookie_val = request.cookies.get(_session_cookie_name())
        creds = _decode_cookie_value(cookie_val)
        if creds == (MY_NAME, BASIC_PASSWORD):
            return True
    return False


def is_authenticated(request):
    """Return True if cookie auth is valid."""
    return is_cookie_authenticated(request)


@app.route('/api/login', methods=['POST'])
def api_login(request, *args, **kwargs):
    """Handle login and set session cookie on success."""
    data = parse_json_body(request)
    username = data.get("username", "")
    password = data.get("password", "")

    if username == MY_NAME and password == BASIC_PASSWORD:
        cookie_name = _session_cookie_name()
        cookie_val = _encode_cookie_value(username, password)
        return (
            {"status": "ok", "message": "Logged in"},
            {cookie_name: cookie_val},
            200,
            {"Content-Type": "application/json"},
        )

    return build_unauthorized_response(
        f"Sai Username hoặc mật khẩu. Node: {MY_NAME}"
    )

# =================================================================
# CÁC API DÀNH CHO GIAO DIỆN (ĐÃ GẮN ACCESS CONTROL & MULTI-THREAD)
# =================================================================
@app.route('/api/poll', methods=['GET'])
def api_poll(request, *args, **kwargs):
    """Return peer list and channel data for UI polling."""
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
    """Send a message to a target channel/peer."""
    if not is_authenticated(request):
        return build_unauthorized_response()

    data = parse_json_body(request)
    target = data.get("target")
    msg = data.get("message")

    return send_message_to_target(target, msg)


def send_message_to_target(target, msg):
    """Send a message to Global or a direct peer channel."""
    if not target or msg is None:
        return {"status": "error", "message": "Missing target or message"}

    if target == "Global":
        CHANNELS["Global"].append({"from": MY_NAME, "msg": msg})
        for peer_name, info in ACTIVE_PEERS.items():
            if peer_name != MY_NAME:
                # GỬI THEO LUỒNG NGẦM ĐỂ TRÁNH BLOCKING (Task 2.3)
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

# =================================================================
# API NHẬN TIN NHẮN (Bổ sung Try-Catch để chống rớt mạng làm Crash app)
# =================================================================
@app.route('/api/receive', methods=['POST'])
def api_receive(request, *args, **kwargs):
    """Receive a P2P message and store it locally."""
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
        print(f"[!] Lỗi nhận tin từ luồng P2P: {e}")
        return {"status": "error"}

# =================================================================
# ROUTE ALIASES (SPEC EXAMPLES) FOR TASK 2.3
# =================================================================
@app.route('/connect-peer', methods=['POST'])
def connect_peer(request, *args, **kwargs):
    """Return connection details for a target peer."""
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
    """Broadcast a message to all peers."""
    if not is_authenticated(request):
        return build_unauthorized_response()

    data = parse_json_body(request)
    msg = data.get("message")
    return send_message_to_target("Global", msg)


@app.route('/send-peer', methods=['POST'])
def send_peer(request, *args, **kwargs):
    """Send a message to a specific peer."""
    if not is_authenticated(request):
        return build_unauthorized_response()

    data = parse_json_body(request)
    target = data.get("target")
    msg = data.get("message")
    return send_message_to_target(target, msg)


if __name__ == "__main__":
    app.prepare_address(MY_IP, MY_PORT)
    register_to_tracker()
    print(
        f"[*] Node {MY_NAME} chay o cong {MY_PORT}. "
        f"Browser: http://{MY_IP}:{MY_PORT}/login.html"
    )
    app.run()