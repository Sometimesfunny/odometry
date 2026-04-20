#!/usr/bin/env bash
set -euo pipefail
N=${1:-4}
BR=br-bench
SRV_NS=srv

# убить процессы (по желанию)
sudo ip netns exec $SRV_NS pkill -f server_stub.py 2>/dev/null || true
for i in $(seq 1 $N); do
  sudo ip netns exec robot$i pkill -f client_stub.py 2>/dev/null || true
done

# удалить veth/неймспейсы
for i in $(seq 1 $N); do
  sudo ip -n robot$i link del veth-r$i 2>/dev/null || true
  sudo ip netns del robot$i 2>/dev/null || true
done
sudo ip -n srv link del veth-s 2>/dev/null || true
sudo ip netns del $SRV_NS 2>/dev/null || true

# удалить мост
sudo ip link set $BR down 2>/dev/null || true
sudo ip link del $BR 2>/dev/null || true

echo "netns down."
