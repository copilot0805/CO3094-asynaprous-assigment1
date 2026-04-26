#
# Copyright (C) 2026 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# AsynapRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#


"""
app.sampleapp
~~~~~~~~~~~~~~~~~

"""

import sys
import os
import importlib.util
import json

from   daemon.asynaprous import AsynapRous

app = AsynapRous()

# Dictionary to keep track of active peers 
# Structure: { "username": {"ip": "127.0.0.1", "port": 5001} }
ACTIVE_PEERS = {}

@app.route('/login', methods=['POST'])
def login(request, *args, **kwargs):    
    """
    Handle user login via POST request.

    This route simulates a login process and prints the provided headers and body
    to the console.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or login payload.
    """
    actual_body = request.body
    print(f"[SampleApp] Logging in with request body: {actual_body}")
    data = {"message": "Welcome to the RESTful TCP WebApp", "received": actual_body}

    # Convert to JSON string
    json_str = json.dumps(data)
    return (json_str.encode("utf-8"))

@app.route("/echo", methods=["POST"])
def echo(request, *args, **kwargs):
    actual_body = request.body
    print(f"[SampleApp] received body {actual_body}")

    try:
        if actual_body:
            message = json.loads(actual_body)
        else:
            message = "No body received"
        data = {"received": message }
        json_str = json.dumps(data)
        return (json_str.encode("utf-8"))
    except json.JSONDecodeError:
        data = {"error": "Invalid JSON format"}
        json_str = json.dumps(data)
        return (json_str.encode("utf-8"))


@app.route('/hello', methods=['PUT'])
async def hello(request, *args, **kwargs):
    """
    Handle greeting via PUT request.

    This route prints a greeting message to the console using the provided headers
    and body.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or message payload.
    """
    actual_body = request.body
    print(f"[SampleApp] ['PUT'] **ASYNC** Hello received: {actual_body}")
    data =  {"id": 1, "name": "Alice", "email": "alice@example.com"}

    # Convert to JSON string
    json_str = json.dumps(data)
    return (json_str.encode("utf-8"))

# Tracker server
@app.route('/submit-info', methods=['POST'])
def submit_info(request, *args, **kwargs):
    """
    Peer Registration: Nhận IP và Port từ ứng dụng chat và lưu vào danh bạ.
    """
    # Vì HttpAdapter truyền đối tượng Request vào, ta lấy body trực tiếp từ nó!
    actual_body = request.body
    print(f"[Tracker] Received submit-info request with body: {actual_body}")
    
    try:
        data = json.loads(actual_body)
        username = data.get('username')
        if username:
            ACTIVE_PEERS[username] = {
                "ip": data.get('ip'),
                "port": data.get('port')
            }
            print(f"[Tracker] Registered peer: {username} at {ACTIVE_PEERS[username]}")
            response_data = {"message": f"Peer {username} registered successfully", "status": "success"}
        else:
            response_data = {"error": "Missing username in JSON payload"}
    except json.JSONDecodeError:
        response_data = {"error": "Invalid JSON format"}
    except Exception as e:
        response_data = {"error": str(e)}

    return response_data

@app.route('/get-list', methods=['GET'])
def get_list(request, *args, **kwargs):
    """
    Peer Discovery: Return the list of active peers to the chat application.
    """
    print(f"[Tracker] Received get-list request. Now ACTIVE_PEERS: {len(ACTIVE_PEERS)}")
    # CHỈ CẦN TRẢ VỀ DICT:
    return ACTIVE_PEERS

def create_sampleapp(ip, port):
    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()

