import socket

try:
    with open('update.sh', 'rb') as f:
        data = f.read()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("termbin.com", 9999))
    s.sendall(data)
    s.shutdown(socket.SHUT_WR) # Tell server we are done sending
    response = b""
    while True:
        chunk = s.recv(1024)
        if not chunk:
            break
        response += chunk
    print("URL:" + response.decode().strip())
    s.close()
except Exception as e:
    print(f"Error: {e}")
