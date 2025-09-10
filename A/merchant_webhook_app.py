# merchant_webhook_app.py
import tkinter as tk
import threading
import time
import socket
import logging
import requests
import netifaces
from pyp2p.net import *
from special_beta import auth as digest
import requests

# ===================== CONFIG =====================
WEBHOOK_URL = "https://your-webhook-endpoint.com/merchant-event"
WEBHOOK_API_KEY = "Sup3rS3cur3ApiKey"
BOB_PORT = 44445

# ===================== LOGGING =====================
logging.basicConfig(
    filename="merchant_p2p.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

def log_event(event, data):
    logging.info(f"{event} | {data}")

# ===================== LOCAL IP & INTERFACE =====================
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
IP = s.getsockname()[0]
s.close()

print(f"[MERCHANT] Detected Local IP: {IP}")
print(f"[MERCHANT] Available Interfaces: {netifaces.interfaces()}")
choice = input("[MERCHANT] Enter Choice Interface Number 0,1,2... : ")

from netifaces import AF_INET
for iface in netifaces.interfaces():
    if netifaces.ifaddresses(iface).get(AF_INET):
        if netifaces.ifaddresses(iface)[AF_INET][0]['addr'] == IP:
            INTE = str(netifaces.interfaces()[int(choice)])
            print(f"[MERCHANT] Selected Interface: {INTE}")
            break

# ===================== AUTH =====================
IP_USER = str("merchant_" + IP)
auth_token = digest.encode(IP_USER, "Sup3rS3cur3P4ssw0rd")
print(f"[MERCHANT] Auth Token: {auth_token}")
log_event("auth_generated", {"user": IP_USER, "token": auth_token})

# ===================== P2P NODE =====================
bob = Net(passive_bind=IP, passive_port=BOB_PORT, interface=INTE, node_type="passive", debug=1)
bob.start()
bob.bootstrap()
bob.advertise()

def send_webhook(event_name, payload):
    try:
        headers = {"Authorization": f"Bearer {WEBHOOK_API_KEY}"}
        response = requests.post(
            WEBHOOK_URL,
            json={"event": event_name, "user": IP_USER, "data": payload},
            headers=headers,
            timeout=3
        )
        log_event(event_name, payload)
        print(f"[MERCHANT WEBHOOK] Sent '{event_name}' -> {response.status_code}")
    except Exception as e:
        log_event("webhook_error", str(e))
        print(f"[MERCHANT WEBHOOK ERROR] Failed: {e}")

def bob_loop():
    while True:
        for con in bob:
            # Simulate "merchant event"
            print("[MERCHANT] Hello")
            send_webhook("merchant_event", {"peer_ip": con.addr[0]},)
            con.send_line("MERCHANT HELLO")
        time.sleep(1)

threading.Thread(target=bob_loop, daemon=True).start()

# ===================== TKINTER UI =====================
#def on_click():
#    print("[MERCHANT] Button clicked, sending webhook event")
#    send_webhook("merchant_click", {"message": "hello"})

def on_click():
    try:
        r = requests.get("http://127.0.0.1:8000/merchant-event", timeout=2)
        print("[MERCHANT APP] Response:", r.text)
    except Exception as e:
        print("[MERCHANT APP] Error:", e)

root = tk.Tk()
root.title("Merchant Webhook Trigger")
root.geometry("300x150")

btn = tk.Button(root, text="Trigger Merchant Webhook", command=on_click,
                bg="green", fg="white", font=("Arial", 14), relief="raised")
btn.pack(expand=True, fill="both", padx=20, pady=20)

root.mainloop()
