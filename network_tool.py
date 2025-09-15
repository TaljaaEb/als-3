# network_tool.py
import socket
import requests
import math
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

# -------------------
# A. Get Local IP
# -------------------
def get_ip():
    """Return the local machine's outbound IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        IP = s.getsockname()[0]
    finally:
        s.close()
    return IP

# -------------------
# B. Get Locality
# -------------------
def get_locality(ip=None):
    """
    Get the locality (city, country) of the given IP.
    If no IP is provided, use the machine's IP.
    Uses ipapi.co (free).
    """
    ip = ip or get_ip()
    try:
        response = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
        data = response.json()
        return {
            "ip": ip,
            "city": data.get("city", "Unknown"),
            "region": data.get("region", "Unknown"),
            "country": data.get("country_name", "Unknown"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude")
        }
    except Exception as e:
        return {"error": str(e)}

# -------------------
# Helper: Haversine Distance
# -------------------
def haversine(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance between two points in km."""
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# -------------------
# C. Calculate Nearest IP
# -------------------
def calculate_nearest_ip(valid_ip_list):
    """
    Given a list of IPs, return the nearest one based on geo distance.
    """
    origin = get_locality()
    if "error" in origin:
        return {"error": origin["error"]}

    nearest_ip = None
    nearest_distance = float("inf")

    for ip in valid_ip_list:
        loc = get_locality(ip)
        if loc.get("latitude") is None or loc.get("longitude") is None:
            continue  # skip invalid IPs
        dist = haversine(
            origin["latitude"], origin["longitude"],
            loc["latitude"], loc["longitude"]
        )
        if dist < nearest_distance:
            nearest_distance = dist
            nearest_ip = {"ip": ip, "distance_km": dist, "location": loc}

    return {"origin": origin, "nearest": nearest_ip}

# -------------------
# HTTP Handler for Make.com
# -------------------
class MakeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/get_ip"):
            result = {"ip": get_ip()}
        elif self.path.startswith("/get_locality"):
            result = get_locality()
        elif self.path.startswith("/nearest_ip"):
            # Example: /nearest_ip?ips=8.8.8.8,1.1.1.1
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            ip_list = query.get("ips", [""])[0].split(",")
            result = calculate_nearest_ip(ip_list)
        else:
            result = {"error": "Invalid endpoint"}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode("utf-8"))

# -------------------
# Entry Point
# -------------------
if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), MakeHandler)
    print("Make.com tool listening on port 8080")
    server.serve_forever()
