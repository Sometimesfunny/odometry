import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import numpy as np
from .icp_core import icp

MAP = None

class Handler(BaseHTTPRequestHandler):
    def _set_headers(self, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

    def do_POST(self):
        start_time_all = time.time()
        if self.path != "/icp":
            self._set_headers(404)
            self.wfile.write(b'{"error":"not found"}')
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            body = self.rfile.read(length).decode('utf-8')
            req = json.loads(body)

            partial = np.array(req["partial"], dtype=np.float32)
            t_init = np.array(req.get("t_init", [0.0, 0.0]), dtype=np.float32)
            R_init = np.array(req.get("R_init", [[1.0, 0.0], [0.0, 1.0]]), dtype=np.float32)

            start_time_icp = time.time()
            R_total, t_total, errors = icp(partial, MAP, init_pose=(R_init, t_init))
            time_icp = time.time() - start_time_icp
            print(f"time icp: {time_icp}")
            # Возвращаем приращения выравнивания относительно init_pose
            resp = {
                "R": R_total.tolist(),
                "t": t_total.tolist(),
                "errors": [float(e) for e in errors]
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(resp).encode('utf-8'))
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        time_all = time.time() - start_time_all
        print(f"all time: {time_all}")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", default="map.npy")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8008)
    args = parser.parse_args()
    global MAP
    MAP = np.load(args.map)
    server = HTTPServer((args.host, args.port), Handler)
    print(f"REST ICP server on http://{args.host}:{args.port}  map_shape={MAP.shape}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
