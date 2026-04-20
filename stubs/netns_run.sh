#!/usr/bin/env bash
set -euo pipefail

N=${1:-4}                             # роботов
SRV_NS=${SRV_NS:-srv}
SRV_URL="http://10.200.0.1:8008/process"
LOG_DIR=${LOG_DIR:-./logs}
PAYLOAD=${PAYLOAD:-$((2*1024*1024))}  # 2MB
ITERS=${ITERS:-10}

mkdir -p "$LOG_DIR"

# 1) сервер
echo "[run] server in ns=$SRV_NS"
sudo ip netns exec "$SRV_NS" bash -lc "
  pkill -f server_stub.py 2>/dev/null || true
  nohup python /app/stubs/server_stub.py --host 0.0.0.0 --port 8008 >/tmp/server.log 2>&1 &
"

# 2) клиенты
for i in $(seq 1 $N); do
  NS="robot$i"
  LOG="$LOG_DIR/robot$i.csv"
  echo "[run] client robot$i -> $SRV_URL, log=$LOG, payload=${PAYLOAD}B, iters=$ITERS"
  sudo ip netns exec "$NS" bash -lc "
    pkill -f client_stub.py 2>/dev/null || true
    nohup python /app/stubs/client_stub.py \
      --server_url '$SRV_URL' \
      --payload_bytes $PAYLOAD \
      --iters $ITERS \
      --log_csv '$LOG' \
      --client_id robot$i \
      >/tmp/client_robot$i.log 2>&1 &
  "
done

echo "launched. tail server log:  sudo ip netns exec $SRV_NS tail -f /tmp/server.log"
