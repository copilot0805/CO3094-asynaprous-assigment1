<<<<<<< HEAD
# AsynapRous Hybrid Chat System - CO3094

Hệ thống Chat lai (Hybrid Chat) được xây dựng trên nền tảng framework **AsynapRous** tự thiết kế, sử dụng lập trình mạng Python thuần (Socket) và kiến trúc non-blocking. Hệ thống hỗ trợ mô hình Client-Server để quản lý danh bạ (Tracker) và mô hình P2P để truyền tin nhắn trực tiếp giữa các người dùng.

## 🛠 Yêu cầu hệ thống
- Python 3.10 trở lên.
- Không sử dụng thư viện ngoài (chỉ dùng Python Standard Library).
- Trình duyệt Web hiện đại (Chrome, Edge) để chạy giao diện.

## 📂 Cấu trúc thư mục chính
- `daemon/`: Chứa mã nguồn cốt lõi của framework (Request, Response, HttpAdapter, Backend).
- `apps/`: Chứa các ứng dụng chạy trên framework.
  - `sampleapp.py`: Logic của Tracker Server.
  - `peer_node.py`: Logic của các nút Chat (vừa là Client vừa là P2P Server).
- `www/`: Chứa giao diện Web (`index.html` và `login.html`).
- `static/`: Chứa các file tĩnh (CSS, Images).

---

## 🚀 Hướng dẫn chạy từng phần

### 2.1. Proxy Server (Điều phối tải)
Phần này mô phỏng một Reverse Proxy có khả năng cân bằng tải (Load Balancing) theo thuật toán Round-Robin.

1. **Cấu hình**: Chỉnh sửa file cấu hình proxy (thường là `proxy.conf`) để định nghĩa các backend.
2. **Lệnh chạy**:
   ```bash
   python start_proxy.py --server-port 8080
   ```
3. **Chức năng**: Proxy sẽ lắng nghe tại cổng 8080 và điều hướng yêu cầu đến các máy chủ backend dựa trên Header `Host`.

### 2.2. RESTful Backend (Máy chủ Tracker)
Giai đoạn khởi tạo của hệ thống Chat, đóng vai trò là máy chủ tập trung (Centralized Server) để quản lý các Peer.

1. **Lệnh chạy**:
   ```bash
   python start_sampleapp.py --server-port 8000
   ```
2. **Các API chính**:
   - `POST /submit-info`: Peer đăng ký IP/Port.
   - `GET /get-list`: Lấy danh sách các Peer đang hoạt động.
3. **Kiểm tra**: Sử dụng Postman để gọi thử các API trên cổng 8000.

### 2.3. Hybrid Chat Application (Ứng dụng Chat lai)
Đây là phần quan trọng nhất, kết hợp cả Client-Server và P2P. Mỗi người dùng khi chạy sẽ khởi tạo một Web Server riêng để phục vụ GUI và nhận tin nhắn.

#### Bước 1: Đảm bảo Tracker Server đang chạy
*(⚠️ Chú ý: Đảm bảo máy chủ Tracker ở phần 2.2 vẫn đang chạy ngầm. **TUYỆT ĐỐI KHÔNG** chạy lại lệnh `start_sampleapp.py` thêm lần nữa ở Terminal khác để tránh lỗi chiếm dụng cổng `[Errno 10048]`).*

#### Bước 2: Chạy Node của người dùng thứ nhất (Ken)
Mở một Terminal mới và chạy:
```bash
python apps/peer_node.py Ken 5001
```
*Truy cập Web tại: `http://127.0.0.1:5001/login.html` (Yêu cầu đăng nhập với tên "Ken" để được cấp Cookie).*

#### Bước 3: Chạy Node của người dùng thứ hai (Huy)
Mở thêm một Terminal mới và chạy:
```bash
python apps/peer_node.py Huy 5002
```
*Truy cập Web tại: `http://127.0.0.1:5002/login.html` (Yêu cầu đăng nhập với tên "Huy" để được cấp Cookie).*

**Tính năng P2P:**
- Khi Ken nhắn cho Huy, gói tin sẽ được gửi trực tiếp từ cổng 5001 sang cổng 5002 (P2P Direct).
- Khi chọn kênh **Global**, tin nhắn sẽ được phát tán tới tất cả mọi người có trong danh sách (Broadcast).
- Hệ thống vẫn có thể chat P2P ngay cả khi Tracker Server đã tắt (nhờ cơ chế Cache danh bạ).

---

## 💡 Đặc điểm kỹ thuật nổi bật

1. **Non-blocking IO & Concurrency**: 
   - Backend sử dụng vòng lặp sự kiện (Event Loop) hoặc đa luồng (Multi-threading) để xử lý kết nối mà không bị nghẽn.
   - Quá trình gửi tin nhắn P2P được bọc trong các luồng ngầm (Background Threads) giúp giao diện người dùng không bao giờ bị treo (Fail-fast).
   - Frontend (Javascript) sử dụng `setInterval` để cập nhật dữ liệu bất đồng bộ mà không cần tải lại trang.

2. **Xử lý gói tin HTTP chuẩn xác (Content-Length)**:
   - Framework không đọc cứng (hardcode) số lượng byte mà tự động bóc tách Header, quét giá trị `Content-Length` để đọc chính xác toàn bộ Body, khắc phục triệt để lỗi phân mảnh dữ liệu (fragmentation).

3. **Bảo mật & Access Control (Authentication)**:
   - Hệ thống yêu cầu xác thực người dùng thông qua trang Đăng nhập và quản lý phiên làm việc bằng **HTTP Cookies**.
   - Xử lý thành công lỗi xung đột Cookie (Cookie Collision) trên môi trường Localhost bằng cách định danh Session linh hoạt theo từng số Port (vd: `session_5001`). Các yêu cầu không có Cookie hợp lệ sẽ bị chặn ở cấp độ API (trả về lỗi `401 Unauthorized`).

4. **Quản lý trạng thái (State Management)**:
   - Tin nhắn được lưu trữ cục bộ tại mỗi Peer (Immutable logs), đảm bảo tính riêng tư và đáp ứng đúng yêu cầu thiết kế không thể chỉnh sửa/xóa.

---
**Lớp:** Kỹ thuật Máy tính - Đại học Bách Khoa TP.HCM
=======
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
