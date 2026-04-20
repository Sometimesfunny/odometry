
import numpy as np
from scipy.spatial import KDTree

def rotate(v, angle_rad):
    rot = np.array([[np.cos(angle_rad), -np.sin(angle_rad)],
                    [np.sin(angle_rad),  np.cos(angle_rad)]])
    return rot @ v

def simulate_lidar_frame(map_points: np.ndarray, trajectory: np.ndarray, i: int,
                         fov_deg: float = 120.0, max_range: float = 70.0,
                         n_rays: int = 1000, tolerance: float = 0.2):
    pos = trajectory[i]
    j = min(i+10, len(trajectory)-1)
    direction = trajectory[j] - pos
    n = np.linalg.norm(direction)
    if n == 0:
        direction = np.array([0.0, 1.0])
    else:
        direction = direction / n
    kdtree = KDTree(map_points)

    angles = np.linspace(-fov_deg/2, fov_deg/2, n_rays)
    angles_rad = np.radians(angles)

    visible = []
    for a in angles_rad:
        ray_dir = rotate(direction, a)
        steps = max(int(max_range/0.1), 1)
        ray = np.linspace(pos, pos + ray_dir*max_range, steps)
        for p in ray:
            idxs = kdtree.query_ball_point(p, r=tolerance)
            if idxs:
                closest_idx = idxs[np.argmin(np.linalg.norm(map_points[idxs] - pos, axis=1))]
                visible.append(map_points[closest_idx])
                break
    visible = np.array(visible, dtype=np.float32).reshape(-1, 2)

    # Convert to robot frame: center at pos, Y forward
    centered = visible - pos
    angle_to_y = np.arctan2(direction[0], direction[1])
    rotM = np.array([[np.cos(angle_to_y), -np.sin(angle_to_y)],
                     [np.sin(angle_to_y),  np.cos(angle_to_y)]], dtype=np.float32)
    rotated = (rotM @ centered.T).T
    return rotated

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--i", type=int, default=100)
    parser.add_argument("--map", default="map.npy")
    parser.add_argument("--traj", default="trajectory.npy")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    mp = np.load(args.map)
    tr = np.load(args.traj)
    frame = simulate_lidar_frame(mp, tr, args.i)
    out = args.out or f"lidar_frame_i{args.i}.npy"
    np.save(out, frame)
    print(f"Saved {out} with shape {frame.shape}")
