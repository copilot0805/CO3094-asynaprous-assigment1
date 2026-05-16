#
# Copyright (C) 2026 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# AsynApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.response
~~~~~~~~~~~~~~~~~

This module provides a :class: `Response <Response>` object to manage and persist 
response settings (cookies, auth, proxies), and to construct HTTP responses
based on incoming requests. 

The current version supports MIME type detection, content loading and header formatting
"""
import datetime
import mimetypes
import os
from .dictionary import CaseInsensitiveDict


DEBUG_SET_COOKIE = os.getenv("ASYNAPROUS_DEBUG_SET_COOKIE", "0") == "1"

BASE_DIR = ""

class Response():   
    """The :class:`Response <Response>` object, which contains a
    server's response to an HTTP request.

    Instances are generated from a :class:`Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    :class:`Response <Response>` object encapsulates headers, content, 
    status code, cookies, and metadata related to the request-response cycle.
    It is used to construct and serve HTTP responses in a custom web server.

    :attrs status_code (int): HTTP status code (e.g., 200, 404).
    :attrs headers (dict): dictionary of response headers.
    :attrs url (str): url of the response.
    :attrsencoding (str): encoding used for decoding response content.
    :attrs history (list): list of previous Response objects (for redirects).
    :attrs reason (str): textual reason for the status code (e.g., "OK", "Not Found").
    :attrs cookies (CaseInsensitiveDict): response cookies.
    :attrs elapsed (datetime.timedelta): time taken to complete the request.
    :attrs request (PreparedRequest): the original request object.

    Usage::

      >>> import Response
      >>> resp = Response()
      >>> resp.build_response(req)
      >>> resp
      <Response>
    """

    __attrs__ = [
        "_content",
        "_header",
        "status_code",
        "method",
        "headers",
        "url",
        "history",
        "encoding",
        "reason",
        "cookies",
        "elapsed",
        "request",
        "body",
    ]


    def __init__(self, request=None):
        """
        Initializes a new :class:`Response <Response>` object.

        : params request : The originating request object.
        """

        self._content = False
        self._content_consumed = False
        self._next = None

        #: Integer Code of responded HTTP Status, e.g. 404 or 200.
        self.status_code = None

        #: Case-insensitive Dictionary of Response Headers.
        #: For example, ``headers['content-type']`` will return the
        #: value of a ``'Content-Type'`` response header.
        self.headers = {}

        #: URL location of Response.
        self.url = None

        #: Encoding to decode with when accessing response text.
        self.encoding = None

        #: A list of :class:`Response <Response>` objects from
        #: the history of the Request.
        self.history = []

        #: Textual reason of responded HTTP Status, e.g. "Not Found" or "OK".
        self.reason = None

        #: A of Cookies the response headers.
        self.cookies = CaseInsensitiveDict()

        #: The amount of time elapsed between sending the request
        self.elapsed = datetime.timedelta(0)

        #: The :class:`PreparedRequest <PreparedRequest>` object to which this
        #: is a response.
        self.request = None


    def get_mime_type(self, path):
        """
        Determines the MIME type of a file based on its path.

        "params path (str): Path to the file.

        :rtype str: MIME type string (e.g., 'text/html', 'image/png').
        """

        try:
            mime_type, _ = mimetypes.guess_type(path)
        except Exception:
            return 'application/octet-stream'
        return mime_type or 'application/octet-stream'


    def prepare_content_type(self, mime_type):
        """
        Dựa vào loại file (MIME type), trả về thư mục gốc chứa file đó.
        """
        if not mime_type:
            return ""

        # Gắn Mime-type vào Header để báo cho trình duyệt biết
        self.headers['Content-Type'] = mime_type
        
        # Mặc định file nằm ở thư mục hiện tại
        base_dir = ""

        # Tách chuỗi Mime-type (VD: 'image/png' -> main_type='image', sub_type='png')
        if '/' in mime_type:
            main_type, sub_type = mime_type.split('/', 1)
            
            # --- ĐỊNH TUYẾN THƯ MỤC CHUẨN XÁC ---
            if sub_type == 'html':
                base_dir = BASE_DIR + "www/"
            elif sub_type == 'css':
                # Code cũ của thầy đã trỏ đúng thư mục css
                base_dir = BASE_DIR + "static/" 
            elif main_type == 'image':
                # FIX: Khi nhận yêu cầu ảnh, phải trỏ thẳng vào thư mục chứa ảnh!
                base_dir = BASE_DIR + "static/images/" 
            elif sub_type == 'json':
                base_dir = BASE_DIR + "api/" # Ví dụ thư mục chứa json

        return base_dir


    def build_content(self, path, base_dir):
        """
        Loads the objects file from storage space.

        :params path (str): relative path to the file.
        :params base_dir (str): base directory where the file is located.

        :rtype tuple: (int, bytes) representing content length and content data.
        """

        filepath = os.path.join(base_dir, path.lstrip('/'))

        print("[Response] Serving the object at location {}".format(filepath))
            #
            #  TODO: implement the step of fetch the object file
            #        store in the return value of content
            #
        try:
            with open(filepath, "rb") as f:
               content = f.read()
        except Exception as e:
            print("[Response] build_content exception: {}".format(e))
            return -1, b""
        return len(content), content



    def build_response_header(self, request): # NEW
        """
        Đóng gói Dictionary headers thành chuỗi Byte chuẩn HTTP
        """
        # 1. Khởi tạo dòng trạng thái (Status Line) - Mặc định là 200 OK
        status = self.status_code if self.status_code else 200
        reason = self.reason if self.reason else "OK"
        header_lines = [f"HTTP/1.1 {status} {reason}"]

        # 2. Bổ sung các thẻ Header bắt buộc
        if not self.headers:
            self.headers = CaseInsensitiveDict()
        self.headers['Content-Length'] = str(len(self._content)) if self._content else "0"
        self.headers['Connection'] = "close"
        self.headers['Server'] = "AsynapRous/CE-Ken"  # dummy server name

        # --- CODE MỚI ĐỂ XỬ LÝ COOKIE (SET-COOKIE) ---
        # Nếu trong quá trình xử lý (ví dụ lúc đăng nhập), chúng ta có nhét dữ liệu
        # vào biến self.cookies, thì bây giờ lôi nó ra để báo cho trình duyệt biết.
        if hasattr(self, 'cookies') and self.cookies:
            for key, value in self.cookies.items():
                # Lệnh Set-Cookie báo trình duyệt: "Ê, nhớ cái key=value này nha!"
                header_lines.append(f"Set-Cookie: {key}={value}; Path=/")
        # ---------------------------------------------
        
        # 3. Nối các thẻ trong Dictionary thành định dạng "Key: Value"
        for key, value in self.headers.items():
            header_lines.append(f"{key}: {value}")

        # 4. Gộp lại bằng \r\n (Carriage Return + Line Feed) và chốt hạ bằng dòng trắng \r\n\r\n
        header_str = "\r\n".join(header_lines) + "\r\n\r\n"

        # Debug: print response headers when Set-Cookie is present
        if DEBUG_SET_COOKIE and hasattr(self, 'cookies') and self.cookies:
            try:
                print(f"[Debug] Response headers (Set-Cookie) for {getattr(request, 'path', '')}:\n{header_str.rstrip()}")
            except Exception:
                pass
        
        return header_str.encode('utf-8')

    #     # Header text alignment
    #         #
    #         #  TODO: implement the header building to create formated
    #         #        header from the provied headers
    #         #
    #         #
    #         # TODO prepare the request authentication
    #         #
    #         # self.auth = ...


    #     return str(fmt_header).encode('utf-8')


    def build_notfound(self):
        """
        Constructs a standard 404 Not Found HTTP response.

        :rtype bytes: Encoded 404 response.
        """

        # return (
        #         "HTTP/1.1 404 Not Found\r\n"
        #         "Accept-Ranges: bytes\r\n"
        #         "Content-Type: text/html\r\n"
        #         "Content-Length: 13\r\n"
        #         "Cache-Control: max-age=86000\r\n"
        #         "Connection: close\r\n"
        #         "\r\n"
        #         "404 Not Found"
        #     ).encode('utf-8')
        self.status_code = 404
        return (
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: text/html\r\n"
                "Connection: close\r\n"
                "\r\n"
                "<h1>404 Not Found</h1>"
            ).encode('utf-8')



    def build_unauthorized(self):
        """Trả về lỗi 401 kèm WWW-Authenticate (Kích hoạt bảng đăng nhập)"""
        self.status_code = 401
        return (
            "HTTP/1.1 401 Unauthorized\r\n"
            "WWW-Authenticate: Basic realm=\"AsynapRous Restricted\"\r\n"
            "Content-Type: text/html\r\n"
            "Connection: close\r\n"
            "\r\n"
            "<h1>401 Unauthorized</h1><p>Vui long dang nhap de tiep tuc.</p>"
        ).encode('utf-8')
    

    # def build_response(self, request, envelop_content=None):
    #         print(f"[Response] Start build response with path: {request.path}")

    #         path = request.path
            
    #         # 1. Định tuyến linh hoạt và an toàn
    #         if path == '/':
    #             path = '/index.html'  
    #             request.path = path
                
    #         if path.endswith('.html'):
    #             base_dir = self.prepare_content_type(mime_type='text/html')
    #         elif path.endswith('.css'):
    #             base_dir = self.prepare_content_type(mime_type='text/css')
    #         elif path.endswith(('.png', '.jpg', '.jpeg', '.ico', '.gif', '.svg')):
    #             mime = self.get_mime_type(path)
    #             base_dir = self.prepare_content_type(mime_type=mime)
    #             path = path.split('/')[-1] # Lấy tên file ảnh
    #         elif path.endswith('.json'):
    #             base_dir = self.prepare_content_type(mime_type='application/json')
    #         else:
    #             return self.build_notfound()
            
    #         # 2. Nạp Dữ Liệu
    #         if envelop_content:
    #             self._content = envelop_content
    #         else:
    #             length, content = self.build_content(path, base_dir)
    #             if length == -1:
    #                 return self.build_notfound() 
    #             self._content = content

    #         # 3. Đóng gói Header & Trả kết quả
    #         self._header = self.build_response_header(request)
    #         return self._header + self._content

    def build_response(self, request, envelop_content=None):
        print(f"[Response] Start build response with path: {request.path}")

        path = request.path
        if path == '/':
            path = '/index.html'  
            request.path = path

        # --- FIX: TƯƠNG THÍCH VỚI HTTPADAPTER CỦA THẦY ---
        # Ưu tiên 1: Lấy envelop_content nếu có
        if envelop_content:
            self._content = envelop_content
            
        # Ưu tiên 2: Kiểm tra xem HttpAdapter đã lén gán self._content chưa
        if self._content:
            self.headers['Content-Type'] = 'application/json' 
        else:
            # Nếu không có nội dung API, đi tìm file tĩnh
            if path.endswith('.html'):
                base_dir = self.prepare_content_type(mime_type='text/html')
            elif path.endswith('.css'):
                base_dir = self.prepare_content_type(mime_type='text/css')
            elif path.endswith(('.png', '.jpg', '.jpeg', '.ico', '.gif', '.svg')):
                mime = self.get_mime_type(path)
                base_dir = self.prepare_content_type(mime_type=mime)
                path = path.split('/')[-1] 
            elif path.endswith('.json'):
                base_dir = self.prepare_content_type(mime_type='application/json')
            else:
                return self.build_notfound() 

            length, content = self.build_content(path, base_dir)
            if length == -1:
                return self.build_notfound() 
            self._content = content

        self._header = self.build_response_header(request)
        return self._header + self._content