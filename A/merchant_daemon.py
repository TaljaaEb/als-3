# merchant_daemon.py
import json
import threading
import signal
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import stripe
import socket

# --- DYNAMIC DATA (will be updated on payment success)
itemlines = []

# -------------------------
# Legacy HTTPServer Handler (serves live itemlines)
# -------------------------
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/itemlines":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            if not itemlines:
                self.wfile.write(b"<custom>No items yet</custom>\n")
            else:
                for t in itemlines:
                    self.wfile.write(f"<custom>{t}</custom>\n".encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

def run_http_server(host="0.0.0.0", port=5051):
    server_address = (host, port)
    httpd = HTTPServer(server_address, Handler)
    print(f"[A] Legacy server at http://{host}:{port}/itemlines")
    httpd.serve_forever()

# -------------------------
# Stripe Webhook Handler
# -------------------------
WEBHOOK_SECRET = "whsec_123456..."  # Replace with your Stripe webhook secret

class StripeWebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global itemlines
        content_length = int(self.headers['Content-Length'])
        payload = self.rfile.read(content_length)
        sig_header = self.headers.get('Stripe-Signature')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError:
            self.send_response(400)
            self.end_headers()
            return

        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            print(f"[MERCHANT] Payment succeeded: {payment_intent['id']}")
            
            # ✅ REPLACE STATIC ITEMLINES WITH DYNAMIC ONES
            itemlines = generate_itemlines(payment_intent)

            # Notify customer daemon AFTER updating itemlines
            notify_customer_daemon(payment_intent)

        self.send_response(200)
        self.end_headers()

def generate_itemlines(payment_intent):
    """
    Create dynamic itemlines based on payment data.
    In real system this might pull from DB, or create
    order summary lines.
    """
    new_items = [
        f"{payment_intent['id']} Item A x1 {payment_intent['amount']/100:.2f}",
        f"{payment_intent['id']} Item B x2 {(payment_intent['amount']/100)*2:.2f}",
    ]
    print(f"[MERCHANT] Updated itemlines: {new_items}")
    return new_items

def notify_customer_daemon(payment_intent):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect(("127.0.0.1", 6000))
            s.sendall(json.dumps(payment_intent).encode("utf-8"))
        except ConnectionRefusedError:
            print("[MERCHANT] Customer daemon not running, skipping.")

def run_webhook_server():
    server = HTTPServer(('0.0.0.0', 5000), StripeWebhookHandler)
    print("[MERCHANT] Listening on port 5000 for Stripe events...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping merchant daemon...")
        server.server_close()
        sys.exit(0)

if __name__ == "__main__":
    # Start legacy HTTP server in background thread
    t = threading.Thread(target=run_http_server, daemon=True)
    t.start()

    # Start webhook listener (main loop)
    run_webhook_server()
