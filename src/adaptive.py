
from dataclasses import dataclass

@dataclass
class Profile:
    name: str
    bandwidth_mbps: float
    latency_ms: float

def estimate_times(scan_bytes: int, t_local: float, t_remote_compute: float, profile: "Profile"):
    """
    Returns dict with 'local', 'remote', 'hybrid' time estimates.
    Hybrid: assume 50% points prefiltered locally costing 0.5 * t_local preproc,
            upload 50%, then server compute at 0.5 * t_remote_compute.
    """
    from .simulate_network import tx_time_seconds
    local = t_local
    remote = tx_time_seconds(scan_bytes, profile.bandwidth_mbps, profile.latency_ms) + t_remote_compute
    half_bytes = int(0.5 * scan_bytes)
    preproc = 0.5 * t_local
    net = tx_time_seconds(half_bytes, profile.bandwidth_mbps, profile.latency_ms)
    hybrid = preproc + net + 0.5 * t_remote_compute
    return {"local": local, "remote": remote, "hybrid": hybrid}

def choose_best_mode(estimates: dict):
    return min(estimates.items(), key=lambda kv: kv[1])[0]
