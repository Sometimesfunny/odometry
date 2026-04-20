#!/usr/bin/env bash
set -euo pipefail

RATE="${RATE:-10mbit}"
DELAY="${DELAY:-10ms}"
LOSS="${LOSS:-0%}"
IFACE="${IFACE:-eth0}"

# tc qdisc del dev "$IFACE" root 2>/dev/null || true
# tc qdisc add dev "$IFACE" root handle 1: htb default 10
# tc class add dev "$IFACE" parent 1: classid 1:10 htb rate "$RATE" ceil "$RATE"
# tc qdisc add dev "$IFACE" parent 1:10 handle 10: netem delay "$DELAY" loss "$LOSS"

# echo "[client] tc applied on $IFACE: rate=$RATE delay=$DELAY loss=$LOSS"

# Имя контейнера доступно в переменной HOSTNAME — используем его для имени файла
: "${HOSTNAME:=client}"

exec python /app/stubs/client_stub.py \
  --server_url "http://server:8008/process" \
  --payload_bytes "${PAYLOAD_BYTES:-2097152}" \
  --iters "${ITERS:-10}" \
  --log_csv "/logs/${HOSTNAME}.csv" \
  --client_id "${HOSTNAME}"
