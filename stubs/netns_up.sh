#!/usr/bin/env bash
set -euo pipefail

# === Параметры ===
N=${1:-4}                     # сколько роботов
SUBNET=10.200.0.0/24
BR=br-bench
BR_IP=10.200.0.254/24        # mgmt IP моста (не обязателен, но удобно)
SRV_NS=srv
SRV_IP=10.200.0.1/24

# Профиль канала (для роботов; при желании — индивидуально настраивайте внутри цикла)
RATE="10mbit"
DELAY="10ms"
LOSS="0.1%"

# === Подготовка: мост ===
sudo ip link add name $BR type bridge || true
sudo ip addr add $BR_IP dev $BR 2>/dev/null || true
sudo ip link set $BR up

# === Серверный namespace + veth ===
sudo ip netns add $SRV_NS 2>/dev/null || true
sudo ip link add veth-s type veth peer name vpeer-s
sudo ip link set veth-s netns $SRV_NS
sudo ip link set vpeer-s master $BR
sudo ip link set vpeer-s up
sudo ip netns exec $SRV_NS ip addr add $SRV_IP dev veth-s
sudo ip netns exec $SRV_NS ip link set veth-s up
sudo ip netns exec $SRV_NS ip link set lo up

# === Роботы ===
for i in $(seq 1 $N); do
  NS="robot$i"
  IP="10.200.0.$((10+i))/24"
  sudo ip netns add $NS 2>/dev/null || true
  # veth пара
  sudo ip link add veth-r$i type veth peer name vpeer-r$i
  sudo ip link set veth-r$i netns $NS
  sudo ip link set vpeer-r$i master $BR
  sudo ip link set vpeer-r$i up
  sudo ip netns exec $NS ip addr add $IP dev veth-r$i
  sudo ip netns exec $NS ip link set veth-r$i up
  sudo ip netns exec $NS ip link set lo up
  # маршрут (в пределах подсети default не обязателен, но пусть будет)
  sudo ip netns exec $NS ip route add default dev veth-r$i || true

  # Шейпинг в robot-ns на его veth (симметрично воздействует на трафик из ns наружу)
  sudo ip netns exec $NS bash -lc "
    modprobe sch_htb 2>/dev/null || true
    modprobe sch_netem 2>/dev/null || true
    tc qdisc del dev veth-r$i root 2>/dev/null || true
    tc qdisc add dev veth-r$i root handle 1: htb default 10
    tc class add dev veth-r$i parent 1: classid 1:10 htb rate $RATE ceil $RATE
    tc qdisc add dev veth-r$i parent 1:10 handle 10: netem delay $DELAY loss $LOSS
  "
done

echo "netns up: server=$SRV_NS@$SRV_IP, robots=1..$N on $BR ($SUBNET)"
