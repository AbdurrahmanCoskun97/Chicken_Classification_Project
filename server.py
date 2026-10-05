import socket
import time
from pathlib import Path
from typing import Optional


def start_server(port: int) -> socket.socket:
    """Initializes and returns a TCP server socket."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", port))
    server_socket.listen(1)
    server_socket.settimeout(1.0)
    print(f"[Server] 🟢 Listening on port: {port}")
    return server_socket


def receive_image(server_socket: socket.socket, save_folder: Path) -> Optional[Path]:
    """Receives image binary stream from client and saves it to disk."""
    try:
        client_socket, addr = server_socket.accept()
    except socket.timeout:
        return None
    except Exception as e:
        print(f"[Server] ❌ Connection error: {e}")
        return None

    try:
        timestamp = int(time.time())
        file_path = save_folder / f"image_{timestamp}.jpg"

        with open(file_path, "wb") as f:
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                f.write(data)

        client_socket.close()
        print(f"[Server] 📷 Image received from {addr[0]}: {file_path.name}")
        return file_path
    except Exception as e:
        print(f"[Server] ❌ Error saving image: {e}")
        return None


def send_result_to_raspberry(ip: str, port: int, result: str) -> bool:
    """Sends inference result back to the client device."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2.0)
            sock.connect((ip, port))
            sock.sendall(result.encode())
        print(f"[Server] ✅ Result sent to {ip}:{port}: {result}")
        return True
    except Exception as e:
        print(f"[Server] ❌ Failed to send result to {ip}: {e}")
        return False