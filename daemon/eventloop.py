import collections
import selectors

class EventLoop:
    """
    Vòng lặp sự kiện tư thiết kế thay thế cho asyncio.
    Nhiệm vụ: Quản lý hàng đợi các hàm (callbacks) và lắng nghe Socket (non-blocking).
    """
    def __init__(self):
        # Hàng đợi chứa các hàm đã sẵn sàng để thực thi ngay (FIFO - First In First Out)
        self.ready = collections.deque()
        
        # lo việc canh chừng các Socket (File Descriptors)
        self.selector = selectors.DefaultSelector()

    def call_soon(self, callback, *args):
        """Nhét một hàm (callback) vào hàng đợi để chạy càng sớm càng tốt."""
        self.ready.append((callback, args))

    def add_reader(self, sock, callback, *args):
        """
        Nhờ hệ điều hành canh chừng một Socket. 
        Khi nào Socket này CÓ DỮ LIỆU ĐỂ ĐỌC, gọi hàm callback.
        """
        # Bắt buộc phải chuyển Socket sang chế độ Non-blocking
        sock.setblocking(False)
        try:
            self.selector.register(sock, selectors.EVENT_READ, (callback, args))
        except KeyError:
            # Nếu đã register rồi thì update lại
            self.selector.modify(sock, selectors.EVENT_READ, (callback, args))

    def remove_reader(self, sock):
        """Hủy canh chừng Socket khi đã đọc xong hoặc ngắt kết nối."""
        try:
            self.selector.unregister(sock)
        except KeyError:
            pass

    def run_forever(self):
        """
        Trái tim của hệ thống: Vòng lặp vô tận (The Tick)
        """
        print("[EventLoop] Động cơ Async 'nhà làm' bắt đầu khởi chạy...")
        while True:
            # 1. Chạy tất cả các hàm đang xếp hàng chờ trong 'ready'
            while self.ready:
                callback, args = self.ready.popleft()
                callback(*args)

            # 2. Nếu hàng đợi rỗng, đi hỏi xem có Socket nào có dữ liệu không
            timeout = 0 if self.ready else None
            
            # Hàm select() sẽ DỪNG TẠI ĐÂY chờ sự kiện, thay vì làm treo cả hệ thống!
            events = self.selector.select(timeout)

            # 3. Hệ điều hành báo: CÓ SOCKET CÓ DỮ LIỆU! 
            for key, mask in events:
                callback, args = key.data
                sock = key.fileobj
                # Ném hàm xử lý của Socket đó vào hàng đợi để vòng lặp sau chạy
                self.call_soon(callback, sock, *args)

# Tạo ra một biến toàn cục (Singleton) để dùng chung
_global_loop = EventLoop()

def get_event_loop():
    """Hàm lấy Vòng lặp sự kiện ra để xài"""
    return _global_loop


class Future:
    """
    Chiếc hộp rỗng (Lời hứa). 
    Khi một hàm mạng (như recv) chưa có dữ liệu, nó sẽ trả về hộp này và báo CPU đi làm việc khác.
    """
    def __init__(self):
        self.result = None
        self._is_done = False
        self._callbacks = []

    def set_result(self, result):
        """Khi đã có dữ liệu thực sự từ mạng, nhét vào hộp và gọi các hàm đang chờ tỉnh dậy."""
        self.result = result
        self._is_done = True
        for callback in self._callbacks:
            get_event_loop().call_soon(callback)

    def __await__(self):
        """Phép thuật của Python: Cho phép dùng chữ 'await' với cái hộp này!"""
        if not self._is_done:
            yield self  # Tạm dừng hàm (đóng băng) trả quyền điều khiển cho EventLoop
        return self.result


class Task:
    """
    Trình điều khiển Coroutine. Nó sẽ chạy hàm async, mỗi khi gặp 'await', 
    nó sẽ dừng lại và gửi danh thiếp cho Future để khi nào Future xong thì gọi nó dậy.
    """
    def __init__(self, coro):
        self.coro = coro
        get_event_loop().call_soon(self.step)

    def step(self):
        try:
            # Chạy hàm async cho đến khi đụng chữ 'await' tiếp theo
            future = self.coro.send(None)
            # Dặn cái hộp Future gọi dậy chạy tiếp khi có dữ liệu
            future._callbacks.append(self.step)
        except StopIteration:
            # Hàm async đã chạy xong từ trên xuống dưới
            pass


# =====================================================================
# CÁC HÀM GIAO TIẾP MẠNG KHÔNG CHẶN (NON-BLOCKING IO)
# =====================================================================

def async_accept(server_sock):
    """Đứng chờ khách kết nối mà không làm treo Server"""
    future = Future()
    def on_accept(_sock): # <--- CHỈ CẦN THÊM CHỮ '_sock' VÀO ĐÂY
        get_event_loop().remove_reader(server_sock)
        try:
            conn, addr = server_sock.accept()
            conn.setblocking(False) 
            future.set_result((conn, addr))
        except BlockingIOError:
            get_event_loop().add_reader(server_sock, on_accept)
            
    get_event_loop().add_reader(server_sock, on_accept)
    return future

def async_recv(sock, nbytes):
    """Cái muôi múc dữ liệu từ mạng mà không làm treo tiến trình"""
    future = Future()
    def on_read(_sock): # <--- VÀ THÊM CHỮ '_sock' VÀO ĐÂY NỮA LÀ XONG
        get_event_loop().remove_reader(sock)
        try:
            data = sock.recv(nbytes)
            future.set_result(data)
        except BlockingIOError:
            get_event_loop().add_reader(sock, on_read)
            
    get_event_loop().add_reader(sock, on_read)
    return future

async def async_read_full_http_message(sock):
    """
    Đọc TOÀN BỘ gói tin HTTP theo đúng Content-Length 
    mà không làm treo CPU (Non-blocking hoàn toàn).
    """
    data = b""
    
    # Bước 1: Đọc cho đến khi hết phần Header (dấu hiệu: \r\n\r\n)
    while b"\r\n\r\n" not in data:
        # Nhường CPU cho thằng khác trong lúc chờ gói tin tới
        chunk = await async_recv(sock, 1024)
        if not chunk:
            break
        data += chunk
            
    if not data:
        return b""
        
    # Bước 2: Tách Header và Body
    parts = data.split(b"\r\n\r\n", 1)
    header_bytes = parts[0]
    body_bytes = parts[1] if len(parts) > 1 else b""
    
    # Bước 3: Quét Content-Length từ Header
    content_length = 0
    headers_str = header_bytes.decode('utf-8', errors='ignore')
    for line in headers_str.split('\r\n'):
        if line.lower().startswith('content-length:'):
            try:
                content_length = int(line.split(':', 1)[1].strip())
            except ValueError:
                content_length = 0
            break
            
    # Bước 4: Vét nốt phần Body còn thiếu dựa đúng trên Content-Length
    while len(body_bytes) < content_length:
        bytes_to_read = min(4096, content_length - len(body_bytes))
        
        # Tiếp tục nhường CPU nếu mạng bị lag, body chưa tới đủ
        chunk = await async_recv(sock, bytes_to_read)
        if not chunk:
            break
        body_bytes += chunk
            
    return header_bytes + b"\r\n\r\n" + body_bytes