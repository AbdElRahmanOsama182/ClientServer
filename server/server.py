import math
import socket
import threading
import os
import sys
import time

SERVER = socket.gethostbyname(socket.gethostname())
HEADER = 4096
FORMAT = 'utf-8'
IDLE_TIMEOUT = 10  # Default timeout in seconds

def adjust_timeout():
    connections = threading.active_count() - 1
    factor = math.ceil(math.log((connections + 1), 100))
    return IDLE_TIMEOUT / factor


def handle_client(conn, addr):
    """Handles incoming client requests, supports persistent connections."""
    conn.settimeout(adjust_timeout())
    print(f"[NEW CONNECTION] {addr} connected.")
    print(f"[TIMEOUT] Connection timeout set to {conn.gettimeout()} seconds.")
    try:
        while True:
            try:
                # Receive and parse HTTP request
                request = conn.recv(HEADER).decode(FORMAT)
                if not request:
                    print(f"[CLOSED] Connection with {addr} closed.")
                    break

                headers = request.splitlines()
                method, path, _ = headers[0].split()
                print(f"[REQUEST] Method: {method}, Path: {path}")

                if method == "GET":
                    file_path = path.lstrip("/")
                    if os.path.isfile(file_path):
                        with open(file_path, "rb") as file:
                            response_data = file.read()
                        response = f"HTTP/1.1 200 OK\r\nConnection: keep-alive\r\n\r\n".encode(FORMAT) + response_data
                    else:
                        response = "HTTP/1.1 404 Not Found\r\nConnection: keep-alive\r\n\r\nFile Not Found".encode(FORMAT)
                    conn.sendall(response)
                    conn.settimeout(adjust_timeout())

                elif method == "POST":
                    file_name = path.lstrip("/")
                    content_length = 0
                    for header in headers:
                        if header.startswith("Content-Length:"):
                            content_length = int(header.split(":")[1].strip())
                            break

                    response = "HTTP/1.1 200 OK\r\nConnection: keep-alive\r\n\r\n".encode(FORMAT)
                    conn.sendall(response)
                    conn.settimeout(adjust_timeout())

                    # Receive file content
                    bytes_received = 0
                    with open(file_name, "wb") as file:
                        while bytes_received < content_length:
                            file_content = conn.recv(min(HEADER, content_length - bytes_received))
                            if not file_content:
                                break
                            file.write(file_content)
                            bytes_received += len(file_content)
                    print(f"[RECEIVED] File '{file_name}' received from client with {bytes_received} bytes.")

                else:
                    response = "HTTP/1.1 405 Method Not Allowed\r\nConnection: keep-alive\r\n\r\n".encode(FORMAT)
                    conn.sendall(response)
                    conn.settimeout(adjust_timeout())
            except socket.timeout:
                print(f"[TIMEOUT] Connection with {addr} timed out.")
                break
    finally:
        conn.close()
        print(f"[DISCONNECTED] {addr} disconnected.")

def start_server(port):
    """Starts the server to listen for connections."""
    print(f"[STARTING] Server starting on port {port}...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER, port))
    server.listen()
    print(f"[LISTENING] Server listening on {SERVER}:{port}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python my_server.py <PORT>")
        sys.exit(1)
    PORT = int(sys.argv[1])
    start_server(PORT)