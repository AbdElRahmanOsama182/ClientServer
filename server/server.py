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
    # Adjusts the connection timeout based on the number of active connections.
    connections = threading.active_count() - 1
    factor = math.ceil(math.log((connections + 1), 100))
    return IDLE_TIMEOUT / factor


def handle_client(conn, addr):
    # Handles incoming client requests, supports persistent connections.
    conn.settimeout(adjust_timeout())
    print(f"[NEW CONNECTION] {addr} connected.")
    print(f"[TIMEOUT] Connection timeout set to {conn.gettimeout()} seconds.")
    try:
        while True:
            try:
                # Receive and parse HTTP request
                request = conn.recv(HEADER).decode(FORMAT)

                # If no data is received, the connection is closed.
                if not request:
                    print(f"[CLOSED] Connection with {addr} closed.")
                    break

                headers = request.splitlines()
                method, path, _ = headers[0].split()
                print(f"[REQUEST] Method: {method}, Path: {path}")
                if method == "GET":

                    file_path = path.lstrip("/")
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        response_headers = (
                            f"HTTP/1.1 200 OK\r\n"
                            f"Content-Length: {file_size}\r\n"
                            f"Connection: keep-alive\r\n\r\n"
                        ).encode(FORMAT)
                        conn.sendall(response_headers)
                        with open(file_path, "rb") as file:
                            while chunk := file.read(HEADER):
                                conn.sendall(chunk)

                        print(f"[SENT] File '{file_path}' sent to {addr} with {file_size} bytes.")
                    else:
                        response = "HTTP/1.1 404 Not Found\r\nConnection: keep-alive\r\n\r\nFile Not Found".encode(FORMAT)
                        print(f"[ERROR] File '{file_path}' not found.")
                        conn.sendall(response)
                    # Adjust timeout based on the number of active connections
                    conn.settimeout(adjust_timeout())

                elif method == "POST":
                    file_name = path.lstrip("/")
                    # Extract content length from headers
                    content_length = 0
                    for header in headers:
                        if header.startswith("Content-Length:"):
                            content_length = int(header.split(":")[1].strip())
                            break
                    # Send 200 response
                    response = "HTTP/1.1 200 OK\r\nConnection: keep-alive\r\n\r\n".encode(FORMAT)
                    conn.sendall(response)
                    # Adjust timeout based on the number of active connections
                    conn.settimeout(adjust_timeout())

                    # Receive file content and check if the content length is reached
                    bytes_received = 0
                    file_name = os.path.basename(file_name)
                    with open(file_name, "wb") as file:
                        while bytes_received < content_length:
                            file_content = conn.recv(min(HEADER, content_length - bytes_received))
                            if not file_content:
                                break
                            file.write(file_content)
                            bytes_received += len(file_content)
                    print(f"[RECEIVED] File '{file_name}' received from client with {bytes_received} bytes.")

                # If method is not GET or POST, send 405 response
                else:
                    response = "HTTP/1.1 405 Method Not Allowed\r\nConnection: keep-alive\r\n\r\n".encode(FORMAT)
                    conn.sendall(response)
                    conn.settimeout(adjust_timeout())
            # Handle timeout exceptions and close the connection
            except socket.timeout:
                print(f"[TIMEOUT] Connection with {addr} timed out.")
                break
    finally:
        conn.close()
        print(f"[DISCONNECTED] {addr} disconnected.")

def start_server(port):
    # Starts the server to listen for connections.
    print(f"[STARTING] Server starting on port {port}...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER, port))
    server.listen()
    print(f"[LISTENING] Server listening on {SERVER}:{port}")
    while True:
        conn, addr = server.accept()
        # Start a new thread to handle the client connection
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        # Print the number of active connections
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
        

if __name__ == "__main__":
    # Check if the port number is provided as an argument
    if len(sys.argv) != 2:
        print("Usage: python my_server.py <PORT>")
        sys.exit(1)
    PORT = int(sys.argv[1])
    start_server(PORT)
    