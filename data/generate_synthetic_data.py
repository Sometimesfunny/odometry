
import numpy as np

def generate_map_and_trajectory(
    map_size=(100, 100),
    n_walls=5,
    wall_points=2000,
    trajectory_len=1000,
    seed=42,
):
    rng = np.random.default_rng(seed)
    W, H = map_size
    points = []
    for _ in range(n_walls):
        if rng.random() < 0.5:
            x = rng.uniform(10, W-10)
            ys = np.linspace(10, H-10, wall_points//n_walls)
            xs = np.full_like(ys, x)
        else:
            y = rng.uniform(10, H-10)
            xs = np.linspace(10, W-10, wall_points//n_walls)
            ys = np.full_like(xs, y)
        pts = np.stack([xs, ys], axis=1)
        points.append(pts)
    xs = np.linspace(0, W, wall_points//n_walls)
    border = np.vstack([
        np.stack([xs, np.zeros_like(xs)], axis=1),
        np.stack([xs, np.full_like(xs, H)], axis=1),
        np.stack([np.zeros_like(xs), xs], axis=1),
        np.stack([np.full_like(xs, W), xs], axis=1),
    ])
    points.append(border)
    map_points = np.vstack(points)

    t = np.linspace(0, 2*np.pi, trajectory_len)
    cx, cy = W/2, H/2
    rx, ry = W*0.35, H*0.35
    traj = np.stack([cx + rx*np.cos(1.0*t), cy + ry*np.sin(1.5*t + 0.5)], axis=1)

    return map_points.astype(np.float32), traj.astype(np.float32)

if __name__ == "__main__":
    mp, tr = generate_map_and_trajectory()
    np.save("map.npy", mp)
    np.save("trajectory.npy", tr)
    print(f"Saved map.npy ({mp.shape}) and trajectory.npy ({tr.shape})")
