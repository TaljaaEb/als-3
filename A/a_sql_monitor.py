# a_sql_monitor.py
import socket
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- CONFIG ---
C_HOST = "127.0.0.1"
C_PORT = 5000
HTTP_PORT = 8000

# --- DATA ---
itemlines = [
    "101 18V Cordless Drill 2 89.99",
    "102 6-inch Wood Clamp 4 12.50",
    "103 Carpenter's Hammer 1 19.99"
]

# -------------------------
# Legacy HTTPServer Handler
# -------------------------
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/itemlines":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            for ln in itemlines:
                self.wfile.write(f"<custom>{ln}</custom>\n".encode())
        elif self.path == "/merchant-event":
            # Webhook endpoint for Merchant
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            print("[A] Merchant webhook event received!")
            self.wfile.write(b"Merchant Event Received")
            # Optional: forward to C if needed
            send_to_c()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

def send_to_c():
    """Send itemlines to C"""
    payload = {"source": "A", "itemlines": itemlines}
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((C_HOST, C_PORT))
            s.sendall(json.dumps(payload).encode())
            resp = s.recv(1024)
            print("[A] C responded:", resp.decode())
    except Exception as e:
        print("[A] Error sending to C:", e)

if __name__ == "__main__":
    print(f"[A] HTTP server running on port {HTTP_PORT}...")
    server = HTTPServer(("0.0.0.0", HTTP_PORT), Handler)
    server.serve_forever()
