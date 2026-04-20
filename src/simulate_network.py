
import time

def tx_time_seconds(bytes_count: int, bandwidth_mbps: float, latency_ms: float):
    """
    Compute wall time for one request-response:
      - one-way latency added twice (simple RTT model)
      - payload upload time at given bandwidth
    Returns seconds.
    """
    if bandwidth_mbps <= 0:
        return float("inf")
    bits = 8 * bytes_count
    seconds_payload = bits / (bandwidth_mbps * 1e6)
    rtt = 2 * (latency_ms / 1000.0)
    return seconds_payload + rtt

def sleep_for_transfer(bytes_count: int, bandwidth_mbps: float, latency_ms: float):
    t = tx_time_seconds(bytes_count, bandwidth_mbps, latency_ms)
    time.sleep(t)
    return t
