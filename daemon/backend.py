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
# daemon.backend
# ~~~~~~~~~~~~~~~~~

# This module provides a backend object to manage and persist backend daemon. 
# It implements a basic backend server using Python's socket and threading libraries.
# It supports handling multiple client connections concurrently and routing requests using a
# custom HTTP adapter.

# Requirements:
# --------------
# - socket: provide socket networking interface.
# - threading: Enables concurrent client handling via threads.
# - response: response utilities.
# - httpadapter: the class for handling HTTP requests.
# - CaseInsensitiveDict: provides dictionary for managing headers or routes.


# Notes:
# ------
# - The server create daemon threads for client handling.
# - The current implementation error handling is minimal, socket errors are printed to the console.
# - The actual request processing is delegated to the HttpAdapter class.

# Usage Example:
# --------------
# >>> create_backend("127.0.0.1", 9000, routes={})

# """

# import asyncio
# import inspect
# import selectors
# import socket
# import threading
# import argparse

# """
# # import asyncio
# # import inspect
# """

# from .response import *
# from .httpadapter import HttpAdapter

# sel = selectors.DefaultSelector()

# # mode_async = "callback"
# mode_async = "coroutine"
# # mode_async = "threading"

# def handle_client(ip, port, conn, addr, routes):
#     """
#     Initializes an HttpAdapter instance and delegates the client handling logic to it.

#     :param ip (str): IP address of the server.
#     :param port (int): Port number the server is listening on.
#     :param conn (socket.socket): Client connection socket.
#     :param addr (tuple): client address (IP, port).
#     :param routes (dict): Dictionary of route handlers.
#     """
#     print("[Backend] Invoke handle_client accepted connection from {}".format(addr))
#     daemon = HttpAdapter(ip, port, conn, addr, routes)

#     # Handle client
#     daemon.handle_client(conn, addr, routes)


# # Callback for handling new client (itself run in sync mode)
# def handle_client_callback(server, ip, port,conn, addr, routes):
#     """
#     Initialize connection instance and delegates the client handling logic to it.

#     :param ip (str): IP address of the server.
#     :param port (int): Port number the server is listening on.
#     :param routes (dict): Dictionary of route handlers.
#     """
#     print("[Backend] Invoke handle_client_callback accepted connection from {}".format(addr))

#     daemon = HttpAdapter(ip, port, conn, addr, routes)

#     # Handle client
#     daemon.handle_client(conn, addr, routes)


# # Coroutine async/await for handling new client
# async def handle_client_coroutine(reader, writer, ip, port, routes):
#     """
#     Coroutine in async communication to initialize connection instance
#     then delegates the client handling logic to it.

#     :param reader (StreamReader): Stream reader wrapper.
#     :param write (Stream write): Stream write wrapper.
#     """
#     addr = writer.get_extra_info("peername")
#     print(
#         "[Backend] Invoke handle_client_coroutine accepted connection from {}".format(
#             addr
#         )
#     )

#     daemon = HttpAdapter(ip, port, None, addr, routes)
    
#     try:
#         await daemon.handle_client_coroutine(reader, writer)
#     except Exception as e:
#         print("[Backend] Error handling client {}: {}".format(addr, e))
#     finally:
#         print("[Backend] Closing connection to {}".format(addr))
#         writer.close()
#         await writer.wait_closed()
#         print("[Backend] Connection to {} closed".format(addr))


# async def async_server(ip="0.0.0.0", port=7000, routes=None):
#     """Run the asyncio server loop."""
#     print("[Backend] async_server **ASYNC** listening on port {}".format(port))
#     if routes:
#         print("[Backend] route settings")
#         for key, value in routes.items():
#             is_co_func = "**ASYNC**" if inspect.iscoroutinefunction(value) else ""
#             print(
#                 f"   + ('{key[0]}', '{key[1]}'): {is_co_func}{value.__name__}"
#             )

#     # Create Closure function to pass routes to the handler
#     async def client_connected_cb(reader, writer):
#         await handle_client_coroutine(reader, writer, ip, port, routes or {})
    
#     # Start event loop of Asyncio server
#     server = await asyncio.start_server(client_connected_cb, ip, port)
#     async with server:
#         await server.serve_forever()

# def run_backend(ip, port, routes):
#     """
#     Starts the backend server, binds to the specified IP and port, and listens for incoming
#     connections. Each connection is handled in a separate thread. The backend accepts incoming
#     connections and spawns a thread for each client.


#     :param ip (str): IP address to bind the server.
#     :param port (int): Port number to listen on.
#     :param routes (dict): Dictionary of route handlers.
#     """
#     # This global variable to configure the asynchrnous mode or not
#     global mode_async

#     print("[Backend] run_backend with routes={}".format(routes))
#     # Process async stream for registering the service and terminate
#     if mode_async == "coroutine":
#         asyncio.run(async_server(ip, port, routes))
#         return

#     # Process socket object
#     server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#     try:
#         server.bind((ip, port))
#         server.listen(50)

#         print("[Backend] Listening on port {}".format(port))
#         if routes:
#             print("[Backend] route settings")
#             for key, value in routes.items():
#                 is_co_func = ""
#                 if inspect.iscoroutinefunction(value):
#                     is_co_func = "**ASYNC** "
#                 print(
#                     "   + ('{}', '{}'): {}{}".format(
#                         key[0], key[1], is_co_func, str(value)
#                     )
#                 )

#         if mode_async == "callback":
#             sel.register(server, selectors.EVENT_READ, (handle_client_callback, ip, port, routes))

#         while True:
#             # Accept connection
#             conn, addr = server.accept()

#             #
#             #  TODO: implement the step of the client incomping connection
#             #        using non-blocking communication
#             #          + multi-thread
#             #          + callback
#             #          + coroutine
#             #        provided handle_client routine
#             #


#             # @bksysnet: We provide various mechanisms to handle client connection
#             #            student can merge and provide dynamic selection later
#             #            this provider simplify by using mode selection variable
#             #            change global variable mode_async to select the mechanism
#             if mode_async == "callback":
#                 # Callback implementation - Event driven architecture
#                 server.setblocking(False)

#                 events = sel.select(timeout=None)
#                 for key, mask in events:
#                     callback, ip, port, routes = key.data
#                     callback(key.fileobj, ip, port, conn, addr, routes)

#             else:
#                 # Baseline multi-thread implementation
#                 #client_thread = threading.Thread...
#                 client_thread = threading.Thread(
#                     target=handle_client,
#                     args=(ip, port, conn, addr, routes),
#                     daemon=True,
#                 )
#                 client_thread.start()


#     except socket.error as e:
#         print("Socket error: {}".format(e))

# def create_backend(ip, port, routes=None):
#     """Entry point for creating and running the backed server."""
#     run_backend(ip, port, routes or {})

#
# Copyright (C) 2026 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
#

import inspect
import selectors
import socket
import threading
import argparse

from .response import *
from .httpadapter import HttpAdapter

# --- IMPORT ĐỘNG CƠ EVENT LOOP NHÀ LÀM ---
from .eventloop import get_event_loop, async_accept, Task

sel = selectors.DefaultSelector()
mode_async = "coroutine"

def handle_client(ip, port, conn, addr, routes):
    print("[Backend] Invoke handle_client accepted connection from {}".format(addr))
    daemon = HttpAdapter(ip, port, conn, addr, routes)
    daemon.handle_client(conn, addr, routes)

def handle_client_callback(server, ip, port, conn, addr, routes):
    print("[Backend] Invoke handle_client_callback accepted connection from {}".format(addr))
    daemon = HttpAdapter(ip, port, conn, addr, routes)
    daemon.handle_client(conn, addr, routes)

# -------------------------------------------------------------
# CƠ CHẾ COROUTINE MỚI (TỰ THIẾT KẾ, KHÔNG DÙNG THƯ VIỆN ASYNCIO)
# -------------------------------------------------------------
async def handle_client_coroutine_wrapper(conn, addr, ip, port, routes):
    """Bọc kết nối vào một Coroutine Task"""
    print(f"[Backend] Invoke handle_client_coroutine accepted connection from {addr}")
    daemon = HttpAdapter(ip, port, conn, addr, routes)
    try:
        # Chuyển quyền xử lý cho tầng Adapter bằng Coroutine
        await daemon.handle_client_coroutine(conn)
    except Exception as e:
        print(f"[Backend] Error handling client {addr}: {e}")
    finally:
        print(f"[Backend] Closing connection to {addr}")
        conn.close()

async def async_server_manual(ip, port, routes):
    """Máy chủ non-blocking hoàn toàn tự chế"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((ip, port))
    server.listen(50)
    server.setblocking(False)

    print(f"[Backend] async_server_manual **ASYNC** listening on port {port}")
    if routes:
        print("[Backend] route settings")
        for key, value in routes.items():
            is_co_func = "**ASYNC**" if inspect.iscoroutinefunction(value) else ""
            print(f"   + ('{key[0]}', '{key[1]}'): {is_co_func}{value.__name__}")

    # Vòng lặp chờ khách kết nối không chặn (Non-blocking Accept)
    while True:
        # Gọi hàm async_accept từ eventloop.py để nhường CPU khi chưa có khách
        conn, addr = await async_accept(server)
        # Khi có khách, tạo một Task mới để phục vụ khách đó song song
        Task(handle_client_coroutine_wrapper(conn, addr, ip, port, routes))

def run_backend(ip, port, routes):
    global mode_async
    print(f"[Backend] run_backend with routes={routes}")

    if mode_async == "coroutine":
        # KHỞI ĐỘNG VÒNG LẶP SỰ KIỆN NHÀ LÀM!
        loop = get_event_loop()
        # Đưa máy chủ vào Task điều phối đầu tiên
        Task(async_server_manual(ip, port, routes or {}))
        # Bắt đầu vòng quay vô tận (The Tick)
        loop.run_forever()
        return

    # Process socket object
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((ip, port))
        server.listen(50)
        print("[Backend] Listening on port {}".format(port))

        if mode_async == "callback":
            sel.register(server, selectors.EVENT_READ, (handle_client_callback, ip, port, routes))

        while True:
            conn, addr = server.accept()
            if mode_async == "callback":
                server.setblocking(False)
                events = sel.select(timeout=None)
                for key, mask in events:
                    callback, ip, port, routes = key.data
                    callback(key.fileobj, ip, port, conn, addr, routes)
            else:
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(ip, port, conn, addr, routes),
                    daemon=True,
                )
                client_thread.start()
    except socket.error as e:
        print("Socket error: {}".format(e))

def create_backend(ip, port, routes=None):
    run_backend(ip, port, routes or {})