#
# Copyright (C) 2026 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# AsynapRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.request
~~~~~~~~~~~~~~~~~

This module provides a Request object to manage and persist 
request settings (cookies, auth, proxies).
"""
import base64
from .dictionary import CaseInsensitiveDict

class Request():
    """The fully mutable "class" `Request <Request>` object,
    containing the exact bytes that will be sent to the server.

    Instances are generated from a "class" `Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    Usage::

      >>> import deamon.request
      >>> req = request.Request()
      ## Incoming message obtain aka. incoming_msg
      >>> r = req.prepare(incoming_msg)
      >>> r
      <Request>
    """
    __attrs__ = [
        "method",
        "url",
        "headers",
        "body",
        "_raw_headers",
        "_raw_body",
        "reason",
        "cookies",
        "body",
        "routes",
        "hook",
    ]

    def __init__(self):
        #: HTTP verb to send to the server.
        self.method = None
        #: HTTP URL to send the request to.
        self.url = None
        #: dictionary of HTTP headers.
        self.headers = None
        #: HTTP path
        self.path = None        
        # The cookies set used to create Cookie header
        self.cookies = None
        #: request body to send to the server.
        self.body = None
        # The raw header
        self._raw_headers = None
        #: The raw body
        self._raw_body = None
        #: Routes
        self.routes = {}
        #: Hook point for routed mapped-path
        self.hook = None

    def extract_request_line(self, request):
        try:
            lines = request.splitlines()
            first_line = lines[0]
            method, path, version = first_line.split()

            if path == '/':
                path = '/index.html'
        except Exception:
            return None, None, None

        return method, path, version
             
    def prepare_headers(self, request):
        """Prepares the given HTTP headers."""
        lines = request.split('\r\n')
        headers = {}
        for line in lines[1:]:
            if ': ' in line:
                key, val = line.split(': ', 1)
                headers[key.lower()] = val
        return headers

    # def fetch_headers_body(self, request):
    #     """Prepares the given HTTP headers."""
    #     # Split request into header section and body section
    #     parts = request.split("\r\n\r\n", 1)  # split once at blank line

    #     _headers = parts[0]
    #     _body = parts[1] if len(parts) > 1 else ""
    #     return _headers, _body
    def fetch_headers_body(self, request):
        """Prepares the given HTTP headers and body."""
        # Kiểm tra mọi loại dấu xuống dòng
        if "\r\n\r\n" in request:
            parts = request.split("\r\n\r\n", 1)
        elif "\n\n" in request:
            parts = request.split("\n\n", 1)
        else:
            parts = [request, ""]
            
        _headers = parts[0]
        # Dùng strip() để dọn sạch khoảng trắng/xuống dòng thừa
        _body = parts[1].strip() 
        return _headers, _body

    def prepare(self, request, routes=None):
        """Prepares the entire request with the given parameters."""

        print("[Request] prepare request missg {}".format(request))
        self.method, self.path, self.version = self.extract_request_line(request)
        if not self.method:
            return 
        
        print("[Request] {} path {} version {}".format(self.method, self.path, self.version))

        # --- FIX 1: LẤY CẢ HEADER VÀ BODY ---
        raw_headers, raw_body = self.fetch_headers_body(request)
        
        # Nếu raw_body rỗng, ta gán thành chuỗi rỗng thay vì để nó mặc định là None
        self.body = raw_body if raw_body else "" 
        # ------------------------------------

        self.headers = self.prepare_headers(raw_headers) # Truyền raw_headers vào đây cho chuẩn
        if self.headers is None:
            self.headers = CaseInsensitiveDict()

        if not routes == {}:
            self.routes = routes
            print("[Request] Routing METHOD {} path {}".format(self.method, self.path))
            self.hook = routes.get((self.method, self.path))
            if self.hook:
                print("[Request] Hook has request {}".format(request))

        # take the raw cookies from the dictionary of headers
        cookies_str = self.headers.get('cookie', '')
        self.cookies = {} # parse cookies_str into self.cookies dictionary
            #
            #  TODO: implement the cookie function here
            #        by parsing the header            #
        if cookies_str:
            pairs = cookies_str.split(';')
            for pair in pairs:
                if '=' in pair:
                    # Cut exactly one '=' to separate key and value, and strip whitespace
                    key, value = pair.strip().split('=', 1)
                    # Use str.strip() to remove leading/trailing whitespace from key and value
                    self.cookies[key.strip()] = value.strip()
            print(f"[Request] Parsed cookies: {self.cookies}")

            auth_header = self.headers.get('authorization', '')
            if auth_header.lower().startswith('basic '):
                encoded_credentials = auth_header.split(' ', 1)[1]
                try:
                    decoded_str = base64.b64decode(encoded_credentials).decode('utf-8')
                    username, password = decoded_str.split(':', 1)
                    self.auth = (username, password)
                    print(f"[Request] authenticated user: {username}")
                except Exception as e:
                    print(f"[Request] Failed to decode Basic auth credentials: {e}")

        return

    def prepare_body(self, data, files, json=None):
        self.prepare_content_length(self.body)
        self.body = data
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return


    def prepare_content_length(self, body):
        self.headers["Content-Length"] = "0"
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return


    def prepare_auth(self, auth, url=""):
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        pass

    def prepare_cookies(self, cookies):
            self.headers["Cookie"] = cookies
