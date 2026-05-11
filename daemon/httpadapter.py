# #
# # Copyright (C) 2026 pdnguyen of HCMC University of Technology VNU-HCM.
# # All rights reserved.
# # This file is part of the CO3093/CO3094 course.
# #
# # AsynapRous release
# #
# # The authors hereby grant to Licensee personal permission to use
# # and modify the Licensed Source Code for the sole purpose of studying
# # while attending the course
# #

# """
# daemon.httpadapter
# ~~~~~~~~~~~~~~~~~

# This module provides a http adapter object to manage and persist 
# http settings (headers, bodies). The adapter supports both
# raw URL paths and RESTful route definitions, and integrates with
# Request and Response objects to handle client-server communication.
# """

# from .request import Request
# from .response import Response
# from .dictionary import CaseInsensitiveDict

# import asyncio
# import inspect

# class HttpAdapter:
#     """
#     A mutable :class:`HTTP adapter <HTTP adapter>` for managing client connections
#     and routing requests.

#     The `HttpAdapter` class encapsulates the logic for receiving HTTP requests,
#     dispatching them to appropriate route handlers, and constructing responses.
#     It supports RESTful routing via hooks and integrates with :class:`Request <Request>` 
#     and :class:`Response <Response>` objects for full request lifecycle management.

#     Attributes:
#         ip (str): IP address of the client.
#         port (int): Port number of the client.
#         conn (socket): Active socket connection.
#         connaddr (tuple): Address of the connected client.
#         routes (dict): Mapping of route paths to handler functions.
#         request (Request): Request object for parsing incoming data.
#         response (Response): Response object for building and sending replies.
#     """

#     __attrs__ = [
#         "ip",
#         "port",
#         "conn",
#         "connaddr",
#         "routes",
#         "request",
#         "response",
#     ]

#     def __init__(self, ip, port, conn, connaddr, routes):
#         """
#         Initialize a new HttpAdapter instance.

#         :param ip (str): IP address of the client.
#         :param port (int): Port number of the client.
#         :param conn (socket): Active socket connection.
#         :param connaddr (tuple): Address of the connected client.
#         :param routes (dict): Mapping of route paths to handler functions.
#         """

#         #: IP address.
#         self.ip = ip
#         #: Port.
#         self.port = port
#         #: Connection
#         self.conn = conn
#         #: Conndection address
#         self.connaddr = connaddr
#         #: Routes
#         self.routes = routes
#         #: Request
#         self.request = Request()
#         #: Response
#         self.response = Response()

#     def handle_client(self, conn, addr, routes):
#         """
#         Handle an incoming client connection.

#         This method reads the request from the socket, prepares the request object,
#         invokes the appropriate route handler if available, builds the response,
#         and sends it back to the client.

#         :param conn (socket): The client socket connection.
#         :param addr (tuple): The client's address.
#         :param routes (dict): The route mapping for dispatching requests.
#         """

#         # Connection handler.
#         self.conn = conn        
#         # Connection address.
#         self.connaddr = addr
#         # Request handler
#         req = self.request
#         # Response handler
#         resp = self.response

#         # Handle the request
#         msg = conn.recv(1024).decode()
#         req.prepare(msg, routes)
#         print("[HttpAdapter] Invoke handle_client connection {}".format(addr))

#         # Handle request hook
#         if req.hook:
#             #
#             # TODO: handle for App hook here
#             #
#             response = ""

#         #print("[HttpAdapter] Response content {}".format(response))
#         conn.sendall(response)
#         conn.close()

#     async def handle_client_coroutine(self, reader, writer):
#         """
#         Handle an incoming client connection using stream reader writer asynchronously.

#         This method reads the request from the socket, prepares the request object,
#         invokes the appropriate route handler if available, builds the response,
#         and sends it back to the client.

#         :param conn (socket): The client socket connection.
#         :param addr (tuple): The client's address.
#         :param routes (dict): The route mapping for dispatching requests.
#         """
#         addr = writer.get_extra_info("peername")
#         print(
#             "[HttpAdapter] Invoke handle_client_coroutine connection {})".format(addr)
#         )

#         # Request handler
#         req = self.request
#         # Response handler
#         resp = self.response


#         # TODO Handle the request asynchronously
#         try:
#             # Read headers first (until \r\n\r\n)
#             data = b""
#             while b"\r\n\r\n" not in data:
#                 chunk = await reader.read(4096)
#                 if not chunk:
#                     break
#                 data += chunk

#             if not data:
#                 print("[HttpAdapter] No data received from {}".format(addr))
#                 return

#             # Split header/body and read the rest of body by Content-Length
#             if b"\r\n\r\n" in data:
#                 header_bytes, body = data.split(b"\r\n\r\n", 1)
#                 header_bytes += b"\r\n\r\n"
#             else:
#                 header_bytes, body = data, b""

#             header_text = header_bytes.decode("utf-8", errors="ignore")
#             content_length = 0
#             for line in header_text.split("\r\n"):
#                 if line.lower().startswith("content-length:"):
#                     try:
#                         content_length = int(line.split(":", 1)[1].strip())
#                     except ValueError:
#                         content_length = 0
#                     break

#             remaining = content_length - len(body)
#             while remaining > 0:
#                 chunk = await reader.read(min(4096, remaining))
#                 if not chunk:
#                     break
#                 body += chunk
#                 remaining -= len(chunk)

#             msg = header_bytes + body

#             # Decoding the raw request data and preparing the Request object
#             req.prepare(msg.decode("utf-8", errors="ignore"), routes=self.routes)

#             # Process Logic App(hook) if client request matches a route with a hook (EX: /Login)
#             # logic function can be async or sync, we will handle both cases
#             if req.hook:
#                 if inspect.iscoroutinefunction(req.hook):
#                     hook_result = await req.hook(req)
#                 else:
#                     hook_result = req.hook(req)

#                 # Temporarily store the hook result (EX: {"message": "login success"}) in the variable _content
#                 import json
#                 if isinstance(hook_result, tuple):
#                     body = hook_result[0] if len(hook_result) > 0 else ""
#                     cookies = hook_result[1] if len(hook_result) > 1 else None
#                     status_code = hook_result[2] if len(hook_result) > 2 else None
#                     headers = hook_result[3] if len(hook_result) > 3 else None
#                     reason = hook_result[4] if len(hook_result) > 4 else None

#                     if isinstance(body, dict):
#                         resp._content = json.dumps(body).encode("utf-8")
#                     else:
#                         resp._content = str(body).encode("utf-8")

#                     if cookies:
#                         resp.cookies.update(cookies)
#                     if headers:
#                         resp.headers.update(headers)
#                     if status_code:
#                         resp.status_code = status_code
#                         if reason:
#                             resp.reason = reason
#                         else:
#                             status_reasons = {
#                                 200: "OK",
#                                 201: "Created",
#                                 204: "No Content",
#                                 400: "Bad Request",
#                                 401: "Unauthorized",
#                                 403: "Forbidden",
#                                 404: "Not Found",
#                                 500: "Internal Server Error",
#                             }
#                             resp.reason = status_reasons.get(status_code, resp.reason)
#                 elif isinstance(hook_result, dict):
#                     resp._content = json.dumps(hook_result).encode("utf-8")
#                 else:
#                     resp._content = str(hook_result).encode("utf-8")

#             # package header & body into HTTP response format
#             response = resp.build_response(req)

#             # Pump data back to the client asynchronously
#             writer.write(response)
#             await writer.drain()

#         except Exception as e:
#             print("[HttpAdapter] Error handling client {}: {}".format(addr, e))

#     # @property
#     # def extract_cookies(self, req, resp):
#     #     """
#     #     Build cookies from the :class:`Request <Request>` headers.

#     #     :param req:(Request) The :class:`Request <Request>` object.
#     #     :param resp: (Response) The res:class:`Response <Response>` object.
#     #     :rtype: cookies - A dictionary of cookie key-value pairs.
#     #     """
#     #     cookies = {}
#     #     for header in headers:
#     #         if header.startswith("Cookie:"):
#     #             cookie_str = header.split(":", 1)[1].strip()
#     #             for pair in cookie_str.split(";"):
#     #                 key, value = pair.strip().split("=")
#     #                 cookies[key] = value
#     #     return cookies

#     # def build_response(self, req, resp):
#     #     """Builds a :class:`Response <Response>` object 

#     #     :param req: The :class:`Request <Request>` used to generate the response.
#     #     :param resp: The  response object.
#     #     :rtype: Response
#     #     """
#     #     response = Response()

#     #     # Set encoding.
#     #     response.encoding = get_encoding_from_headers(response.headers)
#     #     response.raw = resp
#     #     response.reason = response.raw.reason

#     #     if isinstance(req.url, bytes):
#     #         response.url = req.url.decode("utf-8")
#     #     else:
#     #         response.url = req.url

#     #     # Add new cookies from the server.
#     #     response.cookies = extract_cookies(req)

#     #     # Give the Response some context.
#     #     response.request = req
#     #     response.connection = self

#     #     return response

#     # def build_json_response(self, req, resp):
#     #     """Builds a :class:`Response <Response>` object from JSON data

#     #     :param req: The :class:`Request <Request>` used to generate the response.
#     #     :param resp: The  response object.
#     #     :rtype: Response
#     #     """
#     #     response = Response(req)

#     #     # Set encoding.
#     #     response.raw = resp

#     #     if isinstance(req.url, bytes):
#     #         response.url = req.url.decode("utf-8")
#     #     else:
#     #         response.url = req.url

#     #     # Give the Response some context.
#     #     response.request = req
#     #     response.connection = self

#     #     return response


#     # def get_connection(self, url, proxies=None):
#         # """Returns a url connection for the given URL. 

#         # :param url: The URL to connect to.
#         # :param proxies: (optional) A Requests-style dictionary of proxies used on this request.
#         # :rtype: int
#         # """

#         # proxy = select_proxy(url, proxies)

#         # if proxy:
#             # proxy = prepend_scheme_if_needed(proxy, "http")
#             # proxy_url = parse_url(proxy)
#             # if not proxy_url.host:
#                 # raise InvalidProxyURL(
#                     # "Please check proxy URL. It is malformed "
#                     # "and could be missing the host."
#                 # )
#             # proxy_manager = self.proxy_manager_for(proxy)
#             # conn = proxy_manager.connection_from_url(url)
#         # else:
#             # # Only scheme should be lower case
#             # parsed = urlparse(url)
#             # url = parsed.geturl()
#             # conn = self.poolmanager.connection_from_url(url)

#         # return conn


#     def add_headers(self, request):
#         """
#         Add headers to the request.

#         This method is intended to be overridden by subclasses to inject
#         custom headers. It does nothing by default.

        
#         :param request: :class:`Request <Request>` to add headers to.
#         """
#         pass

#     def build_proxy_headers(self, proxy):
#         """Returns a dictionary of the headers to add to any request sent
#         through a proxy. 

#         :class:`HttpAdapter <HttpAdapter>`.

#         :param proxy: The url of the proxy being used for this request.
#         :rtype: dict
#         """
#         headers = {}
#         #
#         # TODO: build your authentication here
#         #       username, password =...
#         # we provide dummy auth here
#         #
#         username, password = ("user1", "password")

#         if username:
#             headers["Proxy-Authorization"] = (username, password)

#         return headers

#
# Copyright (C) 2026 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
#

from .request import Request
from .response import Response
from .dictionary import CaseInsensitiveDict

import inspect
import json

# --- IMPORT HÀM ĐỌC MẠNG KHÔNG CHẶN NHÀ LÀM ---
from .eventloop import async_read_full_http_message

class HttpAdapter:
    __attrs__ = [
        "ip", "port", "conn", "connaddr", "routes", "request", "response",
    ]

    def __init__(self, ip, port, conn, connaddr, routes):
        self.ip = ip
        self.port = port
        self.conn = conn
        self.connaddr = connaddr
        self.routes = routes
        self.request = Request()
        self.response = Response()

    def handle_client(self, conn, addr, routes):
        self.conn = conn        
        self.connaddr = addr
        req = self.request
        resp = self.response

        msg = conn.recv(1024).decode()
        req.prepare(msg, routes)
        print("[HttpAdapter] Invoke handle_client connection {}".format(addr))

        if req.hook:
            pass # TODO: handle for App hook here
            
        response = ""
        conn.sendall(response)
        conn.close()

    # -------------------------------------------------------------
    # HÀM XỬ LÝ CLIENT BẰNG COROUTINE TỰ CHẾ
    # -------------------------------------------------------------
    async def handle_client_coroutine(self, conn):
        addr = self.connaddr
        print(f"[HttpAdapter] Invoke handle_client_coroutine connection {addr}")

        req = self.request
        resp = self.response

        try:
            # DÙNG VŨ KHÍ TỐI THƯỢNG: ĐỌC CONTENT-LENGTH KHÔNG CHẶN
            raw_request = await async_read_full_http_message(conn)
            if not raw_request:
                print(f"[HttpAdapter] No data received from {addr}")
                return

            # Giải mã và chuẩn bị Request
            req.prepare(raw_request.decode("utf-8", errors="ignore"), routes=self.routes)

            # Xử lý Logic App (Hook)
            if req.hook:
                if inspect.iscoroutinefunction(req.hook):
                    hook_result = await req.hook(req)
                else:
                    hook_result = req.hook(req)

                # Bóc tách kết quả từ Hook (do Huân viết)
                if isinstance(hook_result, tuple):
                    body = hook_result[0] if len(hook_result) > 0 else ""
                    cookies = hook_result[1] if len(hook_result) > 1 else None
                    status_code = hook_result[2] if len(hook_result) > 2 else None
                    headers = hook_result[3] if len(hook_result) > 3 else None
                    reason = hook_result[4] if len(hook_result) > 4 else None

                    if isinstance(body, dict):
                        resp._content = json.dumps(body).encode("utf-8")
                    else:
                        resp._content = str(body).encode("utf-8")

                    if cookies:
                        resp.cookies.update(cookies)
                    if headers:
                        resp.headers.update(headers)
                    if status_code:
                        resp.status_code = status_code
                        if reason:
                            resp.reason = reason
                        else:
                            status_reasons = {
                                200: "OK", 201: "Created", 204: "No Content",
                                400: "Bad Request", 401: "Unauthorized", 
                                403: "Forbidden", 404: "Not Found", 
                                500: "Internal Server Error",
                            }
                            resp.reason = status_reasons.get(status_code, resp.reason)
                elif isinstance(hook_result, dict):
                    resp._content = json.dumps(hook_result).encode("utf-8")
                else:
                    resp._content = str(hook_result).encode("utf-8")

            # Đóng gói HTTP response
            response = resp.build_response(req)

            # Bơm dữ liệu ngược lại cho Client (Phản hồi)
            conn.sendall(response)

        except Exception as e:
            print(f"[HttpAdapter] Error handling client {addr}: {e}")

    def add_headers(self, request):
        pass

    def build_proxy_headers(self, proxy):
        headers = {}
        username, password = ("user1", "password")
        if username:
            headers["Proxy-Authorization"] = (username, password)
        return headers