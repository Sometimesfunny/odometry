#!/usr/bin/env python3
# client_stub.py
import argparse, requests, time, json, os, csv, uuid
from datetime import datetime


def make_payload(size_bytes):
    return {"data": "x" * max(0, size_bytes)}  # simple JSON payload

def run_client(args):
    os.makedirs(os.path.dirname(args.log_csv) or ".", exist_ok=True)
    client_id = args.client_id or str(uuid.uuid4())[:8]
    with open(args.log_csv, "a", newline="") as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(["timestamp","client_id","iter","payload_bytes","net_time_s","elapsed_s","status"])
        for it in range(args.iters):
            payload = make_payload(args.payload_bytes)
            # simulate local compute time before sending
            time.sleep(args.local_compute)
            t0 = time.time()
            try:
                # measure actual net+server time by doing HTTP post
                resp = requests.post(args.server_url, json={"payload": payload, "server_compute": args.server_compute}, timeout=60)
                t1 = time.time()
                net_time = t1 - t0
                status = resp.status_code
            except Exception as e:
                t1 = time.time()
                net_time = t1 - t0
                status = f"err:{e}"
            # simulate post-compute
            time.sleep(args.post_compute)
            elapsed = time.time() - t0
            writer.writerow([datetime.utcnow().isoformat(), client_id, it, args.payload_bytes, f"{net_time:.6f}", f"{elapsed:.6f}", status])
            f.flush()
            # optional interval between iterations
            time.sleep(args.interval)

if __name__=="__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--server_url", default="http://server:8008/process")
    p.add_argument("--payload_bytes", type=int, default=2*1024*1024)  # 2 MB
    p.add_argument("--local_compute", type=float, default=0.01)
    p.add_argument("--post_compute", type=float, default=0.0)
    p.add_argument("--server_compute", type=float, default=0.01)
    p.add_argument("--iters", type=int, default=5)
    p.add_argument("--interval", type=float, default=0.1)
    p.add_argument("--log_csv", default="/tmp/stub_logs.csv")
    p.add_argument("--client_id", default=None)
    args = p.parse_args()
    run_client(args)
