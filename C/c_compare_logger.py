# c_compare_logger.py
import socket
import threading
import json
from datetime import datetime
from collections import defaultdict

HOST = "0.0.0.0"
PORT = 5000

# Histories keyed by source (A/B) then by item_code
history = {
    "A": defaultdict(list),
    "B": defaultdict(list)
}

lock = threading.Lock()

def log_difference():
    """Compare the two latest lists from A and B."""
    latest_A = {code: hist[-1] for code, hist in history["A"].items()}
    latest_B = {code: hist[-1] for code, hist in history["B"].items()}

    only_in_A = [f"{code} {latest_A[code]}" for code in latest_A if code not in latest_B]
    only_in_B = [f"{code} {latest_B[code]}" for code in latest_B if code not in latest_A]

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("compare_log.txt", "a") as f:
        f.write(f"\n--- {now} ---\n")
        f.write(f"Only in A: {only_in_A}\n")
        f.write(f"Only in B: {only_in_B}\n")

def add_to_history(source, transactions):
    """Append new transactions with timestamps to history."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for t in transactions:
        parts = t.split(" ", 1)
        if len(parts) < 2:
            continue
        code, rest = parts[0], parts[1]
        # Only append if different from last entry
        if not history[source][code] or history[source][code][-1][1] != rest:
            history[source][code].append((now, rest))

    # Save full history log
    with open(f"history_{source}.txt", "a") as f:
        for code, records in history[source].items():
            for ts, desc in records:
                f.write(f"{ts} | {code} {desc}\n")

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    data = conn.recv(8192).decode("utf-8").strip()
    try:
        payload = json.loads(data)
        source = payload.get("source")
        items = payload.get("transactions", [])

        if source not in ("A", "B"):
            raise ValueError("Invalid source")

        with lock:
            add_to_history(source, items)
            log_difference()

        conn.sendall(b"SUCCESS")
    except Exception as e:
        print(f"Error: {e}")
        conn.sendall(b"FAIL")
    finally:
        conn.close()

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"C (compare_logger) listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_server()
