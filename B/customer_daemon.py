# customer_daemon.py
import socket
import json
import requests
import time

def extract_strings_recursive(test_str, tag):
    start_idx = test_str.find("<" + tag + ">")
    if start_idx == -1:
        return []
    end_idx = test_str.find("</" + tag + ">", start_idx)
    res = [test_str[start_idx+len(tag)+2:end_idx]]
    res += extract_strings_recursive(test_str[end_idx+len(tag)+3:], tag)
    return res

def send_to_c(items):
    print(f"[C] Received parsed items: {items}")

def handle_transaction_pull():
    try:
        r = requests.get("http://127.0.0.1:5051/itemlines", timeout=3)
        items = extract_strings_recursive(r.text, "custom")
        print(f"[B] Parsed items: {items}")
        send_to_c(items)
    except Exception as e:
        print(f"[B] Error fetching from merchant: {e}")

def run_customer_daemon():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 6000))
        s.listen(1)
        print("[CUSTOMER] Waiting for payment success events...")
        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(4096)
                if data:
                    payment_data = json.loads(data.decode("utf-8"))
                    print(f"[CUSTOMER] Payment success for: {payment_data['id']}")
                    # Give merchant time to refresh itemlines
                    time.sleep(1)
                    handle_transaction_pull()

if __name__ == "__main__":
    run_customer_daemon()
