import numpy as np
import matplotlib.pyplot as plt

class LivePlotter:
    def __init__(self, map_points: np.ndarray, trajectory: np.ndarray, figsize=(7,7)):
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.ax.scatter(map_points[:,0], map_points[:,1], s=1)
        self.ax.plot(trajectory[:,0], trajectory[:,1])
        self.est_line, = self.ax.plot([], [])
        self.truth_pt, = self.ax.plot([], [], marker='o', linestyle='None')
        self.est_pt, = self.ax.plot([], [], marker='o', linestyle='None')
        self.partial_scatter = None

        x_min, y_min = np.min(map_points, axis=0) - 5
        x_max, y_max = np.max(map_points, axis=0) + 5
        self.ax.set_xlim(x_min, x_max)
        self.ax.set_ylim(y_min, y_max)
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.set_title("Hybrid ICP Odometry (live)")

        self.est_history = []
        plt.ion(); self.fig.canvas.draw(); self.fig.canvas.flush_events(); plt.show()

    def update(self, truth_xy, est_xy, partial_world=None):
        self.est_history.append(est_xy)
        hist = np.array(self.est_history)
        self.est_line.set_data(hist[:,0], hist[:,1])
        self.truth_pt.set_data([truth_xy[0]],[truth_xy[1]])
        self.est_pt.set_data([est_xy[0]],[est_xy[1]])

        if partial_world is not None and len(partial_world) > 0:
            if self.partial_scatter is None:
                self.partial_scatter = self.ax.scatter(partial_world[:,0], partial_world[:,1], s=5, alpha=0.5)
            else:
                self.partial_scatter.set_offsets(partial_world)

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def close(self):
        plt.ioff()
        plt.close(self.fig)
