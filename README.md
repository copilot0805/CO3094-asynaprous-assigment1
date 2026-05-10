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

## 🚀 Hướng dẫn demo (theo đúng luồng chạy)

### Bước 1: Chạy Proxy (Reverse Proxy + Round-Robin)

1. **Giữ nguyên cấu hình** ở [config/proxy.conf](config/proxy.conf).
2. **Chạy lệnh**:

   ```bash
   python start_proxy.py --server-port 8080
   ```

3. **Ý nghĩa**: Proxy lắng nghe cổng 8080 và điều hướng theo header `Host`:
   - `app2.local` → backend pool `127.0.0.1:9002` và `127.0.0.1:9003`

> **Gợi ý**: Có thể trỏ `app1.local`, `app2.local` về `127.0.0.1` trong file hosts của hệ điều hành.

### Bước 2: Chạy Tracker (Backend)

Mở 2 Terminal mới và chạy:

```bash
python start_sampleapp.py --server-port 9002
```

```bash
python start_sampleapp.py --server-port 9003
```

> Tracker được gọi qua Proxy bằng header `Host: app2.local`.

### Bước 3: Chạy 4 Peer Node

Mỗi Peer mở một Web Server riêng để phục vụ UI và nhận tin nhắn P2P.

Terminal 1:

```bash
python apps/peer_node.py Ken 5001
```

Truy cập: `http://127.0.0.1:5001/login.html`

Terminal 2:

```bash
python apps/peer_node.py Huan 5002
```

Truy cập: `http://127.0.0.1:5002/login.html`

Terminal 3:

```bash
python apps/peer_node.py Huy 5003  
```

Truy cập: `http://127.0.0.1:5003/login.html`

Terminal 4:

```bash
python apps/peer_node.py Hieu 5004
```

Truy cập: `http://127.0.0.1:5004/login.html`



> Đăng nhập bằng đúng tên peer (Ken/Huan/Huy/Hieu). Mật khẩu mặc định: `password`.

### Bước 4: Demo chức năng

- Ken nhắn cho Huan: gói tin đi trực tiếp P2P (5001 → 5002).
- Chọn kênh **Global**: broadcast tới tất cả peer trong danh sách.
- Nếu Tracker tắt, vẫn có thể chat với peer đã cache danh bạ.

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

---

## 📌 Những thay đổi đã thực hiện

### Nội dung đã sửa

- Route Tracker đi qua Proxy; P2P giữ kết nối trực tiếp.
- Bổ sung xác thực: `Authorization` Basic + Cookie, trả `401` với `WWW-Authenticate`.
- Sửa đọc HTTP body theo `Content-Length` (tránh thiếu/đủ byte).
- Thêm chia sẻ trạng thái tracker bằng SQLite để nhiều backend thấy chung danh sách peer.
- Cập nhật UI theo yêu cầu 2.3: danh sách kênh/peer, badge thông báo.

### Các file đã chỉnh sửa

- [daemon/httpadapter.py](daemon/httpadapter.py)
- [daemon/request.py](daemon/request.py)
- [daemon/response.py](daemon/response.py)
- [daemon/proxy.py](daemon/proxy.py)
- [daemon/backend.py](daemon/backend.py)
- [apps/peer_node.py](apps/peer_node.py)
- [apps/sampleapp.py](apps/sampleapp.py)
- [www/index.html](www/index.html)
- [www/login.html](www/login.html)
- [.gitignore](.gitignore)
