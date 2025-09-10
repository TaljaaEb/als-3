# customer_webhook_app.py
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
WEBHOOK_URL = "https://your-webhook-endpoint.com/customer-event"
WEBHOOK_API_KEY = "Sup3rS3cur3ApiKey"
ALICE_PORT = 44444

# ===================== LOGGING =====================
logging.basicConfig(
    filename="customer_p2p.log",
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

print(f"[CUSTOMER] Detected Local IP: {IP}")
print(f"[CUSTOMER] Available Interfaces: {netifaces.interfaces()}")
choice = input("[CUSTOMER] Enter Choice Interface Number 0,1,2... : ")

from netifaces import AF_INET
for iface in netifaces.interfaces():
    if netifaces.ifaddresses(iface).get(AF_INET):
        if netifaces.ifaddresses(iface)[AF_INET][0]['addr'] == IP:
            INTE = str(netifaces.interfaces()[int(choice)])
            print(f"[CUSTOMER] Selected Interface: {INTE}")
            break

# ===================== AUTH =====================
IP_USER = str("customer_" + IP)
auth_token = digest.encode(IP_USER, "Sup3rS3cur3P4ssw0rd")
print(f"[CUSTOMER] Auth Token: {auth_token}")
log_event("auth_generated", {"user": IP_USER, "token": auth_token})

# ===================== P2P NODE =====================
alice = Net(passive_bind=IP, passive_port=ALICE_PORT, interface=INTE, node_type="passive", debug=1)
alice.start()
alice.bootstrap()
alice.advertise()

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
        print(f"[CUSTOMER WEBHOOK] Sent '{event_name}' -> {response.status_code}")
    except Exception as e:
        log_event("webhook_error", str(e))
        print(f"[CUSTOMER WEBHOOK ERROR] Failed: {e}")

def alice_loop():
    while True:
        for con in alice:
            for reply in con:
                print(f"[CUSTOMER] Hello")
                send_webhook("customer_event", {"from": con.addr[0], "message": reply})
        time.sleep(1)

threading.Thread(target=alice_loop, daemon=True).start()

# ===================== TKINTER UI =====================
#def on_click():
#    print("[CUSTOMER] Button clicked, sending webhook event")
#    send_webhook("customer_click", {"message": "hello"})

def on_click():
    try:
        r = requests.get("http://127.0.0.1:8001/customer-event", timeout=2)
        print("[CUSTOMER APP] Response:", r.text)
    except Exception as e:
        print("[CUSTOMER APP] Error:", e)

root = tk.Tk()
root.title("Customer Webhook Trigger")
root.geometry("300x150")

btn = tk.Button(root, text="Trigger Customer Webhook", command=on_click,
                bg="blue", fg="white", font=("Arial", 14), relief="raised")
btn.pack(expand=True, fill="both", padx=20, pady=20)

root.mainloop()

