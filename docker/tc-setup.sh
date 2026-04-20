#!/bin/bash
# usage: tc_setup.sh <iface> <rate> <delay_ms>
set -e
iface=${1:-eth0}
rate=${2:-10mbit}
delay=${3:-10ms}

tc qdisc del dev "$iface" root 2>/dev/null || true
tc qdisc add dev "$iface" root handle 1: htb default 10
tc class add dev "$iface" parent 1: classid 1:10 htb rate "$rate" ceil "$rate"
tc qdisc add dev "$iface" parent 1:10 handle 10: netem delay "$delay" loss 0%
echo "tc applied on $iface: rate=$rate delay=$delay"

exec "$@"
