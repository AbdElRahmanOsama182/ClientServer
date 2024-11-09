import socket
import sys
import os
import time

HEADER = 4096
FORMAT = 'utf-8'
DEFAULT_PORT = 80

def client_get(file_path, host, port):
    # Sends a GET request to the server to retrieve a file.
    request = f"GET /{file_path} HTTP/1.1\r\nHost: {host}\r\nConnection: keep-alive\r\n\r\n".encode(FORMAT)
    client.sendall(request)
    # Receive response from server
    response = client.recv(HEADER)
    # Check if file was found on server
    if b"200 OK" in response:
        with open(file_path.split("/")[-1], "wb") as file:
            file.write(response.split(b"\r\n\r\n", 1)[1])
        print(f"[RECEIVED] File '{file_path}' received from server.")
    # If file was not found, print an error message
    else:
        print("[ERROR] File not found on server.")

def client_post(file_path, host, port):
    # Sends a POST request to the server to upload a file.
    # Read file data and calculate content length
    with open(file_path, "rb") as file:
        file_data = file.read()
    content_length = len(file_data)
    # Send POST request with file data
    request = f"POST /{file_path} HTTP/1.1\r\nHost: {host}\r\nContent-Length: {content_length}\r\nConnection: keep-alive\r\n\r\n".encode(FORMAT)
    client.sendall(request)
    time.sleep(0.1)  # Short delay to ensure headers are sent before file data
    client.sendall(file_data)
    # Receive response from server
    response = client.recv(HEADER).decode(FORMAT)
    # Check if file was uploaded successfully
    if "200 OK" in response:
        print(f"[SENT] File '{file_path}' uploaded successfully.")
    # If file upload failed, print an error message
    else:
        print(f"[ERROR] Failed to upload '{file_path}'.")


def run_client(commands_file, server_ip, server_port=DEFAULT_PORT):
    # Parses commands from file and sends requests to the server.
    # Establish connection with server
    global client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))
    print(f"[CONNECTED] Connected to server at {server_ip}:{server_port}")

    # Read commands from file
    with open(commands_file, "r") as file:
        commands = file.readlines()
    # Process each command in one connection (Persistent connection (Pipeline))
    for command in commands:
        parts = command.strip().split()
        if not parts or len(parts) < 3:
            continue  # Skip invalid commands

        operation = parts[0]
        file_path = parts[1]
        host = parts[2]
        # Use default port if not specified in command
        port = int(parts[3]) if len(parts) > 3 else server_port

        if operation == "client_get":
            client_get(file_path, host, port)
        elif operation == "client_post":
            client_post(file_path, host, port)
        else:
            print(f"[ERROR] Unknown command: {operation}")

    client.close()
    print("[DISCONNECTED] Client connection closed.")

if __name__ == "__main__":
    # Check if the required arguments are provided
    if len(sys.argv) < 3:
        print("Usage: python my_client.py <commands.txt> <server_ip> [port]")
        sys.exit(1)

    commands_file = sys.argv[1]
    server_ip = sys.argv[2]
    # Use default port if not specified
    server_port = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_PORT
    run_client(commands_file, server_ip, server_port)