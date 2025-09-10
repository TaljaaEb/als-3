# b_collector_monitor.py
import socket
import json
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

C_HOST = "127.0.0.1"
C_PORT = 5000
HTTP_PORT = 8001  # use a different port than A

def extract_strings_recursive(test_str, tag):
    start_idx = test_str.find("<" + tag + ">")
    if start_idx == -1:
        return []
    end_idx = test_str.find("</" + tag + ">", start_idx)
    res = [test_str[start_idx+len(tag)+2:end_idx]]
    res += extract_strings_recursive(test_str[end_idx+len(tag)+3:], tag)
    return res

# -------------------------
# Legacy HTTPServer Handler
# -------------------------
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/customer-event":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            print("[B] Customer webhook event received!")
            self.wfile.write(b"Customer Event Received")
            # Optional: trigger data pull
            handle_transaction_pull()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

def handle_transaction_pull():
    """Pull data from A and send to C."""
    try:
        r = requests.get("http://127.0.0.1:8000/itemlines")
        items = extract_strings_recursive(r.text, "custom")
        print(f"[B] Parsed items: {items}")
        send_to_c(items)
    except Exception as e:
        print(f"[B] Error fetching from A: {e}")

def send_to_c(itemlines):
    """Send transaction list to C."""
    payload = {"source": "B", "itemlines": itemlines}
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((C_HOST, C_PORT))
            s.sendall(json.dumps(payload).encode())
            resp = s.recv(1024)
            print(f"[B] C responded: {resp.decode()}")
    except Exception as e:
        print(f"[B] Error sending to C: {e}")

if __name__ == "__main__":
    print(f"[B] HTTP server running on port {HTTP_PORT}...")
    server = HTTPServer(("0.0.0.0", HTTP_PORT), Handler)
    server.serve_forever()
