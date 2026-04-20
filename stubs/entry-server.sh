#!/usr/bin/env bash
set -euo pipefail

# Профиль канала (можно менять через переменные окружения)
RATE="${RATE:-10mbit}"
DELAY="${DELAY:-10ms}"
LOSS="${LOSS:-0%}"
IFACE="${IFACE:-eth0}"

# Настроить qdisc
# tc qdisc del dev "$IFACE" root 2>/dev/null || true
# tc qdisc add dev "$IFACE" root handle 1: htb default 10
# tc class add dev "$IFACE" parent 1: classid 1:10 htb rate "$RATE" ceil "$RATE"
# tc qdisc add dev "$IFACE" parent 1:10 handle 10: netem delay "$DELAY" loss "$LOSS"

# echo "[server] tc applied on $IFACE: rate=$RATE delay=$DELAY loss=$LOSS"

# Запуск сервера
exec python /app/stubs/server_stub.py --host 0.0.0.0 --port 8008
