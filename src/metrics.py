
import numpy as np

def rms_trajectory_error(estimated: np.ndarray, truth: np.ndarray) -> float:
    """
    Root-mean-square error between two 2D trajectories with the same length.
    """
    assert estimated.shape == truth.shape
    diffs = estimated - truth
    d2 = np.sum(diffs**2, axis=1)
    return float(np.sqrt(np.mean(d2)))

def final_drift(estimated: np.ndarray, truth: np.ndarray) -> float:
    """
    Euclidean distance between the final points.
    """
    return float(np.linalg.norm(estimated[-1] - truth[-1]))
