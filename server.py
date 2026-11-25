import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PAGE = Path(__file__).with_name("index.html")
SERVICES = {"Sadrokartón", "Obklady a dlažby", "Rekonštrukcia", "Iné"}
AREAS = {"Ružinov", "Nové Mesto", "Petržalka", "Staré Mesto", "Iná lokalita"}

def validate(data):
    if not isinstance(data, dict):
        return False
    description = data.get("description")
    return (isinstance(data.get("service"), str)
            and data["service"] in SERVICES
            and isinstance(data.get("area"), str)
            and data["area"] in AREAS
            and isinstance(description, str)
            and 0 < len(description.strip()) <= 1500)

class Handler(BaseHTTPRequestHandler):
    def send(self, status, body, content_type="application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self.send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/health":
            self.send(200, b'{"status":"ok","lead_storage":false}')
        else:
            self.send(404, b'{"error":"not_found"}')

    def do_POST(self):
        if self.path != "/api/validate":
            self.send(404, b'{"error":"not_found"}')
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 12000:
                raise ValueError()
            data = json.loads(self.rfile.read(size))
            if not validate(data):
                raise ValueError()
        except (ValueError, UnicodeError):
            self.send(400, b'{"error":"invalid_request"}')
            return
        self.send(200, b'{"valid":true,"stored":false}')

if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8000"))), Handler).serve_forever()
