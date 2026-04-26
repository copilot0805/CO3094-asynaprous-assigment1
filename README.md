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
- `www/`: Chứa giao diện Web (`index.html`).
- `static/`: Chứa các file tĩnh (CSS, Images).

---

## 🚀 Hướng dẫn chạy từng phần

### 2.1. Proxy Server (Điều phối tải)
Phần này mô phỏng một Reverse Proxy có khả năng cân bằng tải (Load Balancing) theo thuật toán Round-Robin.

1. **Cấu hình**: Chỉnh sửa file cấu hình proxy (thường là `proxy.conf`) để định nghĩa các backend.
2. **Lệnh chạy**:
   ```bash
   python start_proxy.py --proxy-port 8080
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

#### Bước 1: Đảm bảo Tracker Server đang chạy (Cổng 8000)
Khởi chạy lệnh ở thư mục gốc:
```bash
python start_sampleapp.py --server-port 8000
```

#### Bước 2: Chạy Node của người dùng thứ nhất (Ken)
Mở một Terminal mới và chạy:
```bash
python apps/peer_node.py Ken 5001
```
*Giao diện Web tại: `http://127.0.0.1:5001/index.html`*

#### Bước 3: Chạy Node của người dùng thứ hai (Huy)
Mở thêm một Terminal mới và chạy:
```bash
python apps/peer_node.py Huy 5002
```
*Giao diện Web tại: `http://127.0.0.1:5002/index.html`*

**Tính năng P2P:**
- Khi Ken nhắn cho Huy, gói tin sẽ được gửi trực tiếp từ cổng 5001 sang cổng 5002 (P2P Direct).
- Khi chọn kênh **Global**, tin nhắn sẽ được phát tán tới tất cả mọi người có trong danh sách (Broadcast).
- Hệ thống vẫn có thể chat P2P ngay cả khi Tracker Server đã tắt (nhờ cơ chế Cache danh bạ).

---

## 💡 Đặc điểm kỹ thuật nổi bật

1. **Non-blocking IO**: 
   - Backend sử dụng vòng lặp sự kiện (Event Loop) hoặc đa luồng (Multi-threading) để xử lý kết nối mà không bị nghẽn.
   - Frontend (Javascript) sử dụng `setInterval` để cập nhật dữ liệu bất đồng bộ mà không cần tải lại trang.

2. **Xử lý lỗi (Error Handling)**:
   - Cơ chế **Fail-fast** với `timeout` trong giao tiếp P2P giúp ứng dụng không bị "treo" (blocking) khi máy chủ Tracker gặp sự cố.
   - Sử dụng **Raw Socket** để đóng gói liền mạch phần Header và Body của gói tin HTTP, khắc phục triệt để lỗi phân mảnh (fragmentation) khi truyền dữ liệu JSON.

3. **Quản lý trạng thái (State Management)**:
   - Tin nhắn được lưu trữ cục bộ tại mỗi Peer (Immutable logs), đảm bảo tính riêng tư và đáp ứng đúng yêu cầu thiết kế không thể chỉnh sửa/xóa.

---
