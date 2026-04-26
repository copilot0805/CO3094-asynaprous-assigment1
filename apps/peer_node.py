import sys
import os
import json
import urllib.request
import threading

# --- THÊM 2 DÒNG NÀY ĐỂ CHỈ ĐƯỜNG CHO PYTHON ---
# Lùi lại 1 bước để ra thư mục gốc, rồi mới tìm thư viện daemon
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))
# -----------------------------------------------

from daemon.asynaprous import AsynapRous


# Lấy tham số cấu hình từ Command Line
MY_NAME = sys.argv[1] if len(sys.argv) > 1 else "Ken"
MY_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5001
MY_IP = "127.0.0.1"
TRACKER_URL = "http://127.0.0.1:8000"

app = AsynapRous()

# QUẢN LÝ KÊNH (Channel Management) & TRẠNG THÁI
# Lưu trữ tin nhắn theo dạng: {"Global": [...], "Huy": [...]}
CHANNELS = {"Global": []} 
ACTIVE_PEERS = {}

def register_to_tracker():
    """Giai đoạn Khởi tạo: Nộp IP/Port lên Tracker (Peer registration)"""
    url = f"{TRACKER_URL}/submit-info"
    payload = json.dumps({"username": MY_NAME, "ip": MY_IP, "port": MY_PORT}).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=payload, method='POST')
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req) as response:
            print(f"[*] {MY_NAME} đã đăng ký thành công với Tracker tại cổng {MY_PORT}!")
    except Exception as e:
        print(f"[!] Lỗi kết nối Tracker: {e}")

def update_peers():
    """Peer discovery: Xin danh bạ từ Tracker"""
    global ACTIVE_PEERS
    url = f"{TRACKER_URL}/get-list"
    try:
        with urllib.request.urlopen(url, timeout=0.5) as response:
            ACTIVE_PEERS = json.loads(response.read().decode('utf-8'))
    except Exception:
        pass

def send_http_p2p(target_ip, target_port, channel, msg):
    """Direct peer communication: Bắn tin nhắn qua HTTP REST"""
    url = f"http://{target_ip}:{target_port}/api/receive"
    payload = json.dumps({"from": MY_NAME, "channel": channel, "msg": msg}).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=payload, method='POST')
        req.add_header('Content-Type', 'application/json')
        urllib.request.urlopen(req, timeout=2)
    except Exception as e:
        print(f"[!] Gửi tin tới {target_ip}:{target_port} thất bại.")

# =================================================================
# CÁC API DÀNH CHO GIAO DIỆN JAVASCRIPT (CLIENT-SIDE)
# =================================================================

@app.route('/api/poll', methods=['GET'])
def api_poll(request, *args, **kwargs):
    """JS GUI gọi API này mỗi giây để cập nhật dữ liệu (Non-blocking GUI)"""
    update_peers()
    data = {
        "my_name": MY_NAME,
        "peers": list(ACTIVE_PEERS.keys()),
        "channels": CHANNELS
    }
    # return json.dumps(data).encode('utf-8')
    return data

@app.route('/api/send', methods=['POST'])
def api_send(request, *args, **kwargs):
    """JS GUI gửi tin nhắn lên đây, Backend sẽ ném nó đi P2P"""
    data = json.loads(request.body)
    target = data.get('target') # Lấy tên kênh ("Global" hoặc tên 1 người)
    msg = data.get('message')
    
    # update_peers() # Cập nhật danh bạ trước khi gửi
    
    if target == "Global":
        # BROADCAST: Gửi cho tất cả mọi người
        CHANNELS["Global"].append({"from": MY_NAME, "msg": msg})
        for peer_name, info in ACTIVE_PEERS.items():
            if peer_name != MY_NAME:
                send_http_p2p(info['ip'], info['port'], "Global", msg)
    else:
        # DIRECT P2P: Chỉ gửi cho 1 người
        if target not in CHANNELS:
            CHANNELS[target] = []
        CHANNELS[target].append({"from": MY_NAME, "msg": msg})
        
        if target in ACTIVE_PEERS:
            info = ACTIVE_PEERS[target]
            send_http_p2p(info['ip'], info['port'], target, msg) # Lấy channel là tên mình để người kia biết ai gửi
            
    # return json.dumps({"status": "ok"}).encode('utf-8')
    return {"status": "ok"}

# =================================================================
# API ĐỂ NHẬN TIN NHẮN TỪ CÁC PEER KHÁC BẮN TỚI
# =================================================================

@app.route('/api/receive', methods=['POST'])
def api_receive(request, *args, **kwargs):
    """Khi Huy gửi tin cho Ken, máy của Huy sẽ POST vào API này trên máy của Ken"""
    data = json.loads(request.body)
    sender = data.get('from')
    channel = data.get('channel') 
    msg = data.get('msg')
    
    # Quyết định lưu vào kênh nào
    store_channel = "Global" if channel == "Global" else sender
    
    if store_channel not in CHANNELS:
        CHANNELS[store_channel] = []
        
    CHANNELS[store_channel].append({"from": sender, "msg": msg})
    print(f"[Nhận tin] {sender} -> Kênh '{store_channel}': {msg}")
    
    # return json.dumps({"status": "received"}).encode('utf-8')
    return {"status": "received"}

# =================================================================

if __name__ == "__main__":
    app.prepare_address(MY_IP, MY_PORT)
    register_to_tracker()
    print(f"[*] Hãy mở trình duyệt và truy cập: http://{MY_IP}:{MY_PORT}/index.html")
    app.run()