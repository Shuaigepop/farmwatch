import socket
import sys

try:
    with open('update.sh', 'rb') as f:
        data = f.read()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("termbin.com", 9999))
    s.sendall(data)
    response = s.recv(1024)
    print("URL:" + response.decode().strip())
    s.close()
except Exception as e:
    print(f"Error: {e}")
