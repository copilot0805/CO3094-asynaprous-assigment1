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
