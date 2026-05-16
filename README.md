# AsynapRous Hybrid Chat System — CO3094

Hệ thống Chat lai (Hybrid P2P Chat) xây trên framework AsynapRous tự thiết kế. Dùng Python chuẩn (Raw Sockets), không dùng Flask/AsyncIO/… Frontend bằng HTML/JS.

## Yêu cầu
- Python 3.10+
- Trình duyệt hiện đại (Chrome/Edge/Firefox). Dùng cửa sổ ẩn danh khi cần kiểm thử nhiều cửa sổ để tránh cache cookie.

## Cấu trúc dự án (những file/thư mục trọng tâm)
- `apps`
  - `sampleapp.py` — Tracker / ứng dụng mẫu (chứa API `submit-info`, `get-list`, dùng SQLite)
  - `peer_node.py` — Peer node: web UI + P2P chat + auth/session
- `config`
  - `proxy.conf` — cấu hình Virtual Host & policy round-robin
- `daemon`
  - `eventloop.py` — Event Loop non-blocking (custom)
  - `backend.py` — server socket / accept / worker
  - `proxy.py` — reverse proxy + round-robin
  - `request.py`, `response.py` — parser / builder HTTP (cookies, `Set-Cookie`)
- `www` — giao diện (`login.html`, `index.html`)
- `static` — CSS/JS/hình ảnh
- `start_*.py` — entry points để chạy nhanh (`proxy`/`backend`/`sampleapp`/`peer_node`)

## Tổng quan vận hành (tóm tắt)
- Kiến trúc: Hybrid — Tracker (Centralized) + P2P direct messaging.
- Event loop tự chế (`select`/`selectors`) để xử lý non-blocking I/O.
- Session: cookie-based (RFC 6265 style) + session store in-memory (demo). Cookie đặt tên theo cổng (ví dụ `sessionid_5001`) để tránh collision khi chạy nhiều peer trên cùng máy.
- Proxy: forward request bằng socket, dùng timeouts và multi-threading để tránh block.

## Hướng dẫn chạy (Demo chuẩn)
Lưu ý: mở nhiều terminal/console để chạy song song từng tiến trình.

### 1) Demo Proxy (cân bằng tải & định tuyến)
Mục tiêu: proxy lắng nghe cổng 8080, chuyển request theo Host (ví dụ `app2.local`) tới backend `9002`/`9003` theo round-robin.

Mở 3 terminal, chạy:

```bash
python start_proxy.py
python start_sampleapp.py --port 9002
python start_sampleapp.py --port 9003
```

Kiểm tra bằng Postman (hoặc curl): gửi liên tục HTTP GET tới `http://localhost:8080` kèm header:

```bash
Host: app2.local
```

Quan sát terminal proxy và terminal backend: bạn sẽ thấy request được forward xen kẽ giữa port `9002` và `9003` theo chính sách round-robin.

Gợi ý curl:

```bash
curl -H "Host: app2.local" http://localhost:8080
```

### 2) Asynchronous HTTP Server Demo (AsynapRous framework + Auth + P2P)
Mục tiêu: khởi động Tracker (`sampleapp`) và nhiều peer node, kiểm tra login/session và chat P2P.

Mở các terminal và chạy theo thứ tự:

```bash
python start_sampleapp.py
python apps/peer_node.py Ken 5001
python apps/peer_node.py Huan 5002
python apps/peer_node.py Huy 5003
python apps/peer_node.py Hieu 5004
```

Mở trình duyệt tới `http://127.0.0.1:5001/login.html` (thay port tương ứng cho từng peer).

Thông tin đăng nhập mẫu:
- Username = tên peer (ví dụ Ken)
- Password mặc định: `password`

Sau khi login, server trả `Set-Cookie` (ví dụ `sessionid_5001=...; Max-Age=3600`) — trình duyệt sẽ lưu cookie và dùng cho các request tiếp theo.

Sau login, mở UI (`/index.html`) để gửi tin nhắn:
- Direct: gửi tới 1 peer
- Global: broadcast
- Group: tạo nhóm (invite), gửi multicast ở tầng ứng dụng

## Kịch bản thử nghiệm gợi ý
- Login tất cả peer (Ken, Huan, Huy, Hieu).
- Tại Ken (`5001`) gửi tin nhắn đến Huan (`5002`) (unicast): xác nhận Huan nhận.
- Tạo nhóm tại Ken: mời Huan & Huy → gửi tin multicast; xác nhận chỉ các thành viên nhóm nhận.
- Tắt Tracker/Proxy (`Ctrl+C`) → các peer vẫn giao tiếp P2P dùng danh bạ local (fault-tolerance test).

## Điểm nhấn kỹ thuật
- Custom Event Loop (`select`/`selectors`) cho non-blocking I/O.
- Đọc HTTP theo `Content-Length` để tránh fragmentation.
- Session cookie (RFC 6265 style) + cookie tên theo port để tránh collision.
- Hybrid: Tracker cho discovery, P2P cho data plane.
- Proxy: forward with timeouts + round-robin.

## Gợi ý vận hành / lỗi thường gặp
- Nếu nhận `401`: redirect client về `/login.html`.
- Session hiện lưu in-memory → restart server làm mất session; dùng SQLite/Redis cho production.
- Khi test nhiều peer trên cùng máy, dùng cổng khác nhau và kiểm tra cookie per-port.

## Các file đã chỉnh sửa (tóm tắt)
- `httpadapter.py`, `request.py`, `response.py`, `proxy.py`, `backend.py`
- `peer_node.py`, `sampleapp.py`
- `index.html`, `login.html`
>>>>>>> origin/feature/tracker
