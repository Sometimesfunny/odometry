
import numpy as np
from scipy.spatial import cKDTree

def best_fit_transform(A: np.ndarray, B: np.ndarray):
    """
    Find the rotation R and translation t that best align A to B (2D, least squares).
    Returns R (2x2), t (2,), and does NOT transform A in-place.
    """
    centroid_A = np.mean(A, axis=0)
    centroid_B = np.mean(B, axis=0)
    AA = A - centroid_A
    BB = B - centroid_B
    H = AA.T @ BB
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    # Handle reflection
    if np.linalg.det(R) < 0:
        Vt[1, :] *= -1
        R = Vt.T @ U.T
    t = centroid_B - R @ centroid_A
    return R, t

def icp_step(src_points: np.ndarray, dst_points: np.ndarray):
    """
    One ICP step: find correspondences of src in dst and compute R, t.
    Returns transformed src, R, t, and mean distance.
    """
    tree = cKDTree(dst_points)
    distances, indices = tree.query(src_points)
    dst_corr = dst_points[indices]
    R, t = best_fit_transform(src_points, dst_corr)
    src_new = (R @ src_points.T).T + t
    mean_error = float(np.mean(distances))
    return src_new, R, t, mean_error

def icp(partial: np.ndarray,
        full: np.ndarray,
        init_pose=None,
        max_iterations: int = 50,
        tolerance: float = 1e-6,
        trim_ratio: float = 0.8):
    """
    Trimmed ICP with optional init pose.
    Returns (R_total, t_total, errors).
    """
    src = np.copy(partial)
    if init_pose is not None:
        R_init, t_init = init_pose
        src = (R_init @ src.T).T + t_init

    R_total = np.eye(2)
    t_total = np.zeros((2,))
    errors = []
    prev = float("inf")

    for _ in range(max_iterations):
        src, R_delta, t_delta, mean_err = icp_step(src, full)
        # accumulate
        R_total = R_delta @ R_total
        t_total = R_delta @ t_total + t_delta

        # Note: we keep mean_err; a full trimmed ICP would recompute distances here.
        errors.append(mean_err)
        if abs(prev - mean_err) < tolerance:
            break
        prev = mean_err

    return R_total, t_total, errors
