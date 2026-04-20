import os
import time
import argparse
import json
from urllib import request
import numpy as np
from typing import List
from .icp_core import icp
from .simulate_network import sleep_for_transfer
from .adaptive import Profile, estimate_times, choose_best_mode
from .lidar_sim import simulate_lidar_frame
from .viz import LivePlotter
from tqdm import tqdm

def call_server_icp(url: str, partial: np.ndarray, R_init: np.ndarray, t_init: np.ndarray):
    payload = json.dumps({
        "partial": partial.tolist(),
        "R_init": R_init.tolist(),
        "t_init": t_init.tolist()
    }).encode('utf-8')
    req = request.Request(url, data=payload, method="POST", headers={"Content-Type": "application/json"})
    with request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    R_delta = np.array(data["R"], dtype=np.float32)
    t_delta = np.array(data["t"], dtype=np.float32)
    return R_delta, t_delta

def path_len(traj: np.ndarray, i0: int, i1: int) -> float:
    """Сумма длин отрезков traj[i] -> traj[i+1] на [i0..i1] (двунаправленно)."""
    if i0 == i1:
        return 0.0
    step = 1 if i1 > i0 else -1
    total = 0.0
    for i in range(i0, i1, step):
        d = traj[i + step] - traj[i]
        total += float(np.linalg.norm(d))
    return total


def run_mode(mode: str,
             map_points: np.ndarray,
             trajectory: np.ndarray,
             indices: List[int],
             profile: Profile,
             server_speedup: float = 5.0,
             scan_bytes_per_point: int = 16,
             verbose: bool = False,
             server_url: str = "http://127.0.0.1:8008/icp",
             viz: LivePlotter | None = None,
             viz_delay: float = 0.05,
             lidar_cache_dir: str = ".lidar_cache"
):
    est_positions = []
    timings = []
    c_per_point = 1e-5
    os.makedirs(lidar_cache_dir, exist_ok=True)

    # Инициализация позы: как было
    R_prev = np.eye(2, dtype=np.float32)
    t_prev = trajectory[indices[0]].astype(np.float32)

    prev_idx = indices[0]
    for idx in tqdm(indices):
        cache_file = os.path.join(lidar_cache_dir, f"frame_{idx}.npy")
        if os.path.exists(cache_file):
            partial = np.load(cache_file)
        else:
            partial = simulate_lidar_frame(map_points, trajectory, idx)
            np.save(cache_file, partial)
        N = len(partial)
        scan_bytes = int(N * scan_bytes_per_point)

        # --- перемещение между итерациями: направление prev->curr и длина пути по промежуточным узлам ---
        dp = trajectory[idx] - trajectory[prev_idx]
        norm = float(np.linalg.norm(dp))
        if norm > 1e-9:
            dir_world = dp / norm
        else:
            dir_world = np.array([0.0, 0.0], dtype=np.float32)
        dist = path_len(trajectory, prev_idx, idx)
        t_pred = t_prev + dir_world.astype(np.float32) * dist

        t0 = time.time()
        if N == 0:
            # без точек — только одометрический сдвиг
            R_new, t_new = R_prev, t_pred
            elapsed = time.time() - t0
        else:
            # ICP с начальной позой: R_prev (как просил), t_pred (с учётом перемещения)
            if mode == "local":
                R_delta, t_delta, _ = icp(partial, map_points, init_pose=(R_prev, t_pred))
                elapsed = time.time() - t0
            elif mode == "remote":
                net = sleep_for_transfer(scan_bytes, profile.bandwidth_mbps, profile.latency_ms)
                R_delta, t_delta = call_server_icp(server_url, partial, R_prev, t_pred)
                elapsed = time.time() - t0 + net
            elif mode == "hybrid":
                pre = 0.5 * c_per_point * N
                time.sleep(pre)
                half_bytes = scan_bytes // 2
                net = sleep_for_transfer(half_bytes, profile.bandwidth_mbps, profile.latency_ms)
                R_delta, t_delta = call_server_icp(server_url, partial, R_prev, t_pred)
                elapsed = time.time() - t0 + pre + net
            elif mode == "adaptive":
                approx_local = c_per_point * N
                approx_server = approx_local / server_speedup
                ests = estimate_times(scan_bytes, approx_local, approx_server, profile)
                picked = choose_best_mode(ests)
                if verbose:
                    print(f"[adaptive] idx={idx} N={N} choose={picked} est={ests}")
                if picked == "local":
                    R_delta, t_delta, _ = icp(partial, map_points, init_pose=(R_prev, t_pred))
                    elapsed = time.time() - t0
                elif picked == "remote":
                    net = sleep_for_transfer(scan_bytes, profile.bandwidth_mbps, profile.latency_ms)
                    R_delta, t_delta = call_server_icp(server_url, partial, R_prev, t_pred)
                    elapsed = time.time() - t0 + net
                else:
                    pre = 0.5 * approx_local
                    time.sleep(pre)
                    half_bytes = scan_bytes // 2
                    net = sleep_for_transfer(half_bytes, profile.bandwidth_mbps, profile.latency_ms)
                    R_delta, t_delta = call_server_icp(server_url, partial, R_prev, t_pred)
                    elapsed = time.time() - t0 + pre + net
            else:
                raise ValueError("Unknown mode")

            # аккумулируем глобальную позу (как было)
            R_new = R_delta @ R_prev
            t_new = R_delta @ t_pred + t_delta

        # визуализация + накопление
        est_positions.append(t_new)
        timings.append(elapsed)
        if viz is not None:
            partial_world = (R_new @ partial.T).T + t_new if N > 0 else None
            truth_xy = trajectory[idx]
            viz.update(truth_xy, t_new, partial_world=partial_world)
            if viz_delay > 0:
                time.sleep(viz_delay)

        R_prev, t_prev = R_new, t_new
        prev_idx = idx

    return np.array(est_positions), np.array(timings)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", default="map.npy")
    parser.add_argument("--traj", default="trajectory.npy")
    parser.add_argument("--mode", choices=["local", "remote", "hybrid", "adaptive"], default="adaptive")
    parser.add_argument("--profile", choices=["optics", "wifi", "4g", "radio"], default="wifi")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=300)
    parser.add_argument("--step", type=int, default=10)
    parser.add_argument("--server_speedup", type=float, default=5.0)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--server_url", default="http://127.0.0.1:8008/icp")
    parser.add_argument("--viz", action="store_true")
    parser.add_argument("--viz_delay", type=float, default=0.05)
    args = parser.parse_args()

    mp = np.load(args.map)
    tr = np.load(args.traj)

    profiles = {
        "optics": Profile("Optics", bandwidth_mbps=1000.0, latency_ms=1.0),
        "wifi":   Profile("Wi-Fi",  bandwidth_mbps=10.0,   latency_ms=10.0),
        "4g":     Profile("4G",     bandwidth_mbps=1.0,    latency_ms=100.0),
        "radio":  Profile("Radio",  bandwidth_mbps=0.1,    latency_ms=300.0),
    }
    prof = profiles[args.profile]

    indices = list(range(args.start, min(args.end, len(tr)), args.step))

    plotter = LivePlotter(mp, tr) if args.viz else None
    try:
        est, times = run_mode(args.mode, mp, tr, indices, prof,
                              server_speedup=args.server_speedup,
                              verbose=args.verbose,
                              server_url=args.server_url,
                              viz=plotter,
                              viz_delay=args.viz_delay)
    finally:
        if plotter is not None:
            plotter.close()

    truth = tr[indices]
    from .metrics import rms_trajectory_error, final_drift
    rms = rms_trajectory_error(est, truth)
    drift = final_drift(est, truth)
    print(f"Mode={args.mode} Profile={prof.name}: RMS={rms:.3f} Drift={drift:.3f} AvgTime={float(np.mean(times)):.3f}s")

if __name__ == "__main__":
    main()
