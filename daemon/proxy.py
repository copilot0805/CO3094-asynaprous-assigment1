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
daemon.proxy
~~~~~~~~~~~~~~~~~

This module implements a simple proxy server using Python's socket and threading libraries.
It routes incoming HTTP requests to backend services based on hostname mappings and returns
the corresponding responses to clients.

Requirement:
-----------------
- socket: provides socket networking interface.
- threading: enables concurrent client handling via threads.
- response: customized :class: `Response <Response>` utilities.
- httpadapter: :class: `HttpAdapter <HttpAdapter >` adapter for HTTP request processing.
- dictionary: :class: `CaseInsensitiveDict <CaseInsensitiveDict>` for managing headers and cookies.

"""
import socket
import threading
from .response import *
from .httpadapter import HttpAdapter
from .dictionary import CaseInsensitiveDict

#: A dictionary mapping hostnames to backend IP and port tuples.
#: Used to determine routing targets for incoming requests.
PROXY_PASS = {
    "192.168.56.103:8080": ('192.168.56.103', 9000),
    "app1.local": ('192.168.56.103', 9001),
    "app2.local": ('192.168.56.103', 9002),
}


def forward_request(host, port, request):
    """
    Forwards an HTTP request to a backend server and retrieves the response.

    :params host (str): IP address of the backend server.
    :params port (int): port number of the backend server.
    :params request (str): incoming HTTP request.

    :rtype bytes: Raw HTTP response from the backend server. If the connection
                  fails, returns a 404 Not Found response.
    """

    backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # THÊM DÒNG NÀY: Ép Proxy chỉ đợi Backend tối đa 0.5 giây cho mỗi lần đọc
    backend.settimeout(2)

    try:
        backend.connect((host, port))
        backend.sendall(request.encode('utf-8'))

        response = b""
        while True:
            try:
                chunk = backend.recv(4096)
                if not chunk:
                    break
                response += chunk
            except socket.timeout:
                break
    
        return response
    except socket.error as e:
      print("Socket error: {}".format(e))
      return (
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 13\r\n"
            "Connection: close\r\n"
            "\r\n"
            "404 Not Found"
        ).encode('utf-8')
    finally:
        # Nhớ đóng socket của Proxy đi
        backend.close()


# def resolve_routing_policy(hostname, routes):
#     """
#     Handles an routing policy to return the matching proxy_pass.
#     It determines the target backend to forward the request to.

#     :params host (str): IP address of the request target server.
#     :params port (int): port number of the request target server.
#     :params routes (dict): dictionary mapping hostnames and location.
#     """

#     print(hostname)
#     proxy_map, policy = routes.get(hostname,('127.0.0.1:9000','round-robin'))
#     print(proxy_map)
#     print(policy)

#     proxy_host = ''
#     proxy_port = '9000'
#     if isinstance(proxy_map, list):
#         if len(proxy_map) == 0:
#             print("[Proxy] Emtpy resolved routing of hostname {}".format(hostname))
#             print("Empty proxy_map result")
#             # TODO: implement the error handling for non mapped host
#             #       the policy is design by team, but it can be 
#             #       basic default host in your self-defined system
#             # Use a dummy host to raise an invalid connection
#             proxy_host = '127.0.0.1'
#             proxy_port = '9000'
#         elif len(value) == 1:
#             proxy_host, proxy_port = proxy_map[0].split(":", 2)
#         #elif: # apply the policy handling 
#         #   proxy_map
#         #   policy
#         else:
#             # Out-of-handle mapped host
#             proxy_host = '127.0.0.1'
#             proxy_port = '9000'
#     else:
#         print("[Proxy] resolve route of hostname {} is a singulair to".format(hostname))
#         proxy_host, proxy_port = proxy_map.split(":", 2)

#     return proxy_host, proxy_port
# Biến toàn cục để nhớ vị trí Server đã gọi lần trước cho thuật toán Round-Robin
# Format: {'app2.local': 0, 'app1.local': 0}
ROUND_ROBIN_STATE = {}

def resolve_routing_policy(hostname, routes):
    """
    Handles routing policy to return the matching proxy_pass.
    Implements Round-Robin Load Balancing.
    """
    global ROUND_ROBIN_STATE

    print(f"[Proxy] Resolving routing for Hostname: {hostname}")
    
    # 1. Tìm cấu hình của hostname trong file .conf (biến routes)
    # Ví dụ: proxy_map = ['192.168.56.114:9002', '192.168.56.114:9003']
    #        policy = 'round-robin'
    route_config = routes.get(hostname)
    
    # Rơi vào trường hợp Host không tồn tại trong file conf
    if not route_config:
        print(f"[Proxy] LỖI: Không tìm thấy host '{hostname}' trong proxy.conf")
        return '127.0.0.1', '9000' # Chuyển về 1 cổng chết/hoặc trang chủ báo lỗi

    proxy_map, policy = route_config
    
    # Đảm bảo proxy_map luôn là một List để dễ xử lý
    if not isinstance(proxy_map, list):
        proxy_map = [proxy_map]
        
    if len(proxy_map) == 0:
        return '127.0.0.1', '9000'

    proxy_host = ''
    proxy_port = '9000'

    # 2. Xử lý chia bài (Load Balancing)
    if len(proxy_map) == 1:
        # Nếu chỉ có 1 Server thì khỏi cần chia bài, quăng thẳng luôn
        target = proxy_map[0]
        proxy_host, proxy_port = target.split(":", 1)
        
    else:
        # Nếu có nhiều Server -> Áp dụng policy (Mặc định thầy yêu cầu round-robin)
        # if policy == 'round-robin':
        if policy == 'round': # "round" mean "round-robin"
            # Khởi tạo bộ nhớ cho Host này nếu chưa có
            if hostname not in ROUND_ROBIN_STATE:
                ROUND_ROBIN_STATE[hostname] = 0
                
            # Lấy vị trí index hiện tại
            current_index = ROUND_ROBIN_STATE[hostname]
            
            # Chọn Server theo index
            target = proxy_map[current_index]
            proxy_host, proxy_port = target.split(":", 1)
            
            print(f"[Proxy LoadBalancer] Round-Robin -> Chọn Server thứ {current_index + 1}: {target}")
            
            # Tăng index lên 1, nếu vượt quá số lượng Server thì quay về 0
            ROUND_ROBIN_STATE[hostname] = (current_index + 1) % len(proxy_map)
        else:
            # Nếu policy khác (VD: least-conn, hash), tạm thời cứ lấy Server đầu tiên
            target = proxy_map[0]
            proxy_host, proxy_port = target.split(":", 1)

    return proxy_host, proxy_port

def handle_client(ip, port, conn, addr, routes):
    """
    Handles an individual client connection by parsing the request,
    determining the target backend, and forwarding the request.

    The handler extracts the Host header from the request to
    matches the hostname against known routes. In the matching
    condition,it forwards the request to the appropriate backend.

    The handler sends the backend response back to the client or
    returns 404 if the hostname is unreachable or is not recognized.

    :params ip (str): IP address of the proxy server.
    :params port (int): port number of the proxy server.
    :params conn (socket.socket): client connection socket.
    :params addr (tuple): client address (IP, port).
    :params routes (dict): dictionary mapping hostnames and location.
    """

    # request = conn.recv(1024).decode()
    request = conn.recv(4096).decode('utf-8', errors='ignore')
    if not request:
        return # Nếu khách kết nối mà không gửi gì thì ngắt luôn

    # # Extract hostname
    # for line in request.splitlines():
    #     if line.lower().startswith('host:'):
    #         hostname = line.split(':', 1)[1].strip()
    # Extract hostname
    hostname = ""
    for line in request.splitlines():
        if line.lower().startswith('host:'):
            # Lấy phần tên phía sau chữ 'Host:' (VD: ' app2.local:8080')
            raw_host = line.split(':', 1)[1].strip()
            
            # Cắt bỏ phần Port (nếu có) để chỉ lấy 'app2.local'
            if ':' in raw_host:
                hostname = raw_host.split(':')[0]
            else:
                hostname = raw_host
            break # Tìm thấy rồi thì thoát vòng lặp cho nhanh

    print("[Proxy] {} at Host: {}".format(addr, hostname))

    # Resolve the matching destination in routes and need conver port
    # to integer value
    resolved_host, resolved_port = resolve_routing_policy(hostname, routes)
    try:
        resolved_port = int(resolved_port)
    except ValueError:
        print("Not a valid integer")

    if resolved_host:
        print("[Proxy] Host name {} is forwarded to {}:{}".format(hostname,resolved_host, resolved_port))
        response = forward_request(resolved_host, resolved_port, request)        
    else:
        response = (
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 13\r\n"
            "Connection: close\r\n"
            "\r\n"
            "404 Not Found"
        ).encode('utf-8')
    conn.sendall(response)
    conn.close()

def run_proxy(ip, port, routes):
    """
    Starts the proxy server and listens for incoming connections. 

    The process dinds the proxy server to the specified IP and port.
    In each incomping connection, it accepts the connections and
    spawns a new thread for each client using `handle_client`.
 

    :params ip (str): IP address to bind the proxy server.
    :params port (int): port number to listen on.
    :params routes (dict): dictionary mapping hostnames and location.

    """

    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # --- THÊM DÒNG NÀY ĐỂ ÉP HỆ THỐNG NHẢ CỔNG NGAY LẬP TỨC ---
    proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        proxy.bind((ip, port))
        proxy.listen(50)
        print("[Proxy] Listening on IP {} port {}".format(ip,port))
        while True:
            conn, addr = proxy.accept()
            #
            #  TODO: implement the step of the client incomping connection
            #        using multi-thread programming with the
            #        provided handle_client routine
            #
            # threading to handle multiple clients concurrently
            client_thread = threading.Thread(
                target=handle_client, 
                args=(ip, port, conn, addr, routes))
            
            client_thread.daemon = True  # Daemonize thread to exit when main thread exits
            client_thread.start()  

    except socket.error as e:
      print("Socket error: {}".format(e))

def create_proxy(ip, port, routes):
    """
    Entry point for launching the proxy server.

    :params ip (str): IP address to bind the proxy server.
    :params port (int): port number to listen on.
    :params routes (dict): dictionary mapping hostnames and location.
    """

    run_proxy(ip, port, routes)
