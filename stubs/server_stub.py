#!/usr/bin/env python3
# server_stub.py
import argparse, json, time
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/process":
            self.send_response(404); self.end_headers(); return
        length = int(self.headers.get("Content-Length","0"))
        body = self.rfile.read(length)
        # simulate server compute time (very small) if requested via header
        try:
            req = json.loads(body.decode("utf-8"))
            server_compute = float(req.get("server_compute", 0.01))
        except Exception:
            server_compute = 0.01
        time.sleep(server_compute)
        resp = {"status":"ok", "recv_bytes": len(body)}
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode("utf-8"))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8008)
    args = p.parse_args()
    server = HTTPServer((args.host, args.port), Handler)
    print(f"server on {args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__=="__main__":
    main()
