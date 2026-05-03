import sys
import os
import json
import urllib.request
import threading

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))

from daemon.asynaprous import AsynapRous

MY_NAME = sys.argv[1] if len(sys.argv) > 1 else "Ken"
MY_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5001
MY_IP = "127.0.0.1"
TRACKER_URL = "http://127.0.0.1:8000"

app = AsynapRous()

CHANNELS = {"Global": []} 
ACTIVE_PEERS = {}

def register_to_tracker():
    url = f"{TRACKER_URL}/submit-info"
    payload = json.dumps({"username": MY_NAME, "ip": MY_IP, "port": MY_PORT}).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=payload, method='POST')
        req.add_header('Content-Type', 'application/json')
        urllib.request.urlopen(req)
        print(f"[*] {MY_NAME} da dang ky thanh cong voi Tracker.")
    except Exception as e:
        print(f"[!] Loi Tracker: {e}")

def update_peers():
    global ACTIVE_PEERS
    url = f"{TRACKER_URL}/get-list"
    try:
        with urllib.request.urlopen(url, timeout=0.5) as response:
            ACTIVE_PEERS = json.loads(response.read().decode('utf-8'))
    except Exception:
        pass

def send_http_p2p_worker(target_ip, target_port, channel, msg):
    """Hàm chạy ngầm (Non-blocking) để gửi tin nhắn"""
    url = f"http://{target_ip}:{target_port}/api/receive"
    payload = json.dumps({"from": MY_NAME, "channel": channel, "msg": msg}).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=payload, method='POST')
        req.add_header('Content-Type', 'application/json')
        urllib.request.urlopen(req, timeout=2)
    except Exception as e:
        pass

# =================================================================
# API XỬ LÝ ĐĂNG NHẬP (TASK 2.2) - ĐÃ FIX LỖI COOKIE COLLISION
# =================================================================
@app.route('/api/login', methods=['POST'])
def api_login(request, *args, **kwargs):
    try:
        body_str = request.body.decode('utf-8') if isinstance(request.body, bytes) else request.body
        data = json.loads(body_str)
        username = data.get('username', '')
    except Exception:
        username = ""
    
    if username == MY_NAME:
        # TẠO TÊN COOKIE ĐỘC NHẤT THEO PORT (Tránh đè nhau trên localhost)
        cookie_name = f"session_{MY_PORT}"
        cookie_val = f"user_{username}_logged_in"
        return {"status": "ok", "cookie_name": cookie_name, "cookie_val": cookie_val}
    else:
        return {"status": "error", "message": f"Sai Username! Vui lòng nhập đúng tên Node: {MY_NAME}"}

# Hàm kiểm tra chứng thực nội bộ
def is_authenticated(request):
    if hasattr(request, 'cookies') and request.cookies:
        # Chỉ tìm đúng cái Cookie thuộc về Port của mình
        cookie_name = f"session_{MY_PORT}"
        session = request.cookies.get(cookie_name)
        if session == f"user_{MY_NAME}_logged_in":
            return True
    return False

# =================================================================
# CÁC API DÀNH CHO GIAO DIỆN (ĐÃ GẮN ACCESS CONTROL & MULTI-THREAD)
# =================================================================
@app.route('/api/poll', methods=['GET'])
def api_poll(request, *args, **kwargs):
    # Kiểm tra Cookie trước (Task 2.2)
    if not is_authenticated(request):
        return {"error": "Unauthorized", "redirect": "/login.html"}
        
    update_peers()
    return {
        "my_name": MY_NAME,
        "peers": list(ACTIVE_PEERS.keys()),
        "channels": CHANNELS
    }

@app.route('/api/send', methods=['POST'])
def api_send(request, *args, **kwargs):
    # Kiểm tra Cookie (Task 2.2)
    if not is_authenticated(request):
         return {"error": "Unauthorized"}
         
    data = json.loads(request.body)
    target = data.get('target') 
    msg = data.get('message')
    
    if target == "Global":
        CHANNELS["Global"].append({"from": MY_NAME, "msg": msg})
        for peer_name, info in ACTIVE_PEERS.items():
            if peer_name != MY_NAME:
                # GỬI THEO LUỒNG NGẦM ĐỂ TRÁNH BLOCKING (Task 2.3)
                threading.Thread(target=send_http_p2p_worker, args=(info['ip'], info['port'], "Global", msg)).start()
    else:
        if target not in CHANNELS:
            CHANNELS[target] = []
        CHANNELS[target].append({"from": MY_NAME, "msg": msg})
        
        if target in ACTIVE_PEERS:
            info = ACTIVE_PEERS[target]
            # GỬI THEO LUỒNG NGẦM ĐỂ TRÁNH BLOCKING (Task 2.3)
            threading.Thread(target=send_http_p2p_worker, args=(info['ip'], info['port'], target, msg)).start()
            
    return {"status": "ok"}

# =================================================================
# API XỬ LÝ ĐĂNG NHẬP (TASK 2.2)
# =================================================================
@app.route('/api/login', methods=['POST'])
def api_login(request, *args, **kwargs):
    try:
        body_str = request.body.decode('utf-8') if isinstance(request.body, bytes) else request.body
        data = json.loads(body_str)
        username = data.get('username', '')
    except Exception:
        username = ""
    
    if username == MY_NAME:
        # TẠO TÊN COOKIE ĐỘC NHẤT THEO PORT (Tránh đè nhau trên localhost)
        cookie_name = f"session_{MY_PORT}"
        cookie_val = f"user_{username}_logged_in"
        return {"status": "ok", "cookie_name": cookie_name, "cookie_val": cookie_val}
    else:
        return {"status": "error", "message": f"Sai Username! Vui lòng nhập đúng tên Node: {MY_NAME}"}

# Hàm kiểm tra chứng thực nội bộ
def is_authenticated(request):
    if hasattr(request, 'cookies') and request.cookies:
        # Chỉ tìm đúng cái Cookie thuộc về Port của mình
        cookie_name = f"session_{MY_PORT}"
        session = request.cookies.get(cookie_name)
        if session == f"user_{MY_NAME}_logged_in":
            return True
    return False

# =================================================================
# API NHẬN TIN NHẮN (Bổ sung Try-Catch để chống rớt mạng làm Crash app)
# =================================================================
@app.route('/api/receive', methods=['POST'])
def api_receive(request, *args, **kwargs):
    try:
        body_str = request.body.decode('utf-8') if isinstance(request.body, bytes) else request.body
        data = json.loads(body_str)
        sender = data.get('from')
        channel = data.get('channel') 
        msg = data.get('msg')
        
        store_channel = "Global" if channel == "Global" else sender
        if store_channel not in CHANNELS:
            CHANNELS[store_channel] = []
            
        CHANNELS[store_channel].append({"from": sender, "msg": msg})
        return {"status": "received"}
    except Exception as e:
        print(f"[!] Lỗi nhận tin từ luồng P2P: {e}")
        return {"status": "error"}

if __name__ == "__main__":
    app.prepare_address(MY_IP, MY_PORT)
    register_to_tracker()
    print(f"[*] Node {MY_NAME} chay o cong {MY_PORT}. Browser: http://{MY_IP}:{MY_PORT}/index.html")
    app.run()