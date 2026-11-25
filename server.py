import json
import uuid
import psycopg
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

def store_test(data):
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("Database unavailable")
    with psycopg.connect(url, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS test_leads (id uuid PRIMARY KEY, created_at timestamptz DEFAULT now(), service text NOT NULL, area text NOT NULL)")
            cur.execute("DELETE FROM test_leads WHERE created_at < now() - interval '7 days'")
            ident = uuid.uuid4()
            cur.execute("INSERT INTO test_leads (id, service, area) VALUES (%s, %s, %s)", (ident, data["service"], data["area"]))
    return str(ident)

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
        if self.path == "/api/test-lead":
            if data.get("description") != "TEST":
                self.send(400, b'{"error":"test_only"}')
                return
            try:
                ident = store_test(data)
            except (psycopg.Error, RuntimeError):
                self.send(503, b'{"error":"database_unavailable"}')
                return
            self.send(201, json.dumps({"test": True, "id": ident}).encode())
            return
        self.send(200, b'{"valid":true,"stored":false}')

if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8000"))), Handler).serve_forever()
