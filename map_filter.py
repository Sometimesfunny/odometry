import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import KDTree

# Загрузка
map_points = np.load('map.npy')      # (n, 2)
trajectory = np.load('trajectory.npy')      # (m, 2)

i = 500
fov_deg = 90
max_range = 70.0
n_rays = 1000  # количество лучей
tolerance = 0.2

# Позиция и направление
pos = trajectory[i]
if i < len(trajectory) - 10:
    next_pos = trajectory[i + 10]
else:
    next_pos = trajectory[i]
direction = next_pos - pos
direction /= np.linalg.norm(direction)

kdtree = KDTree(map_points)

# Углы лучей
angles = np.linspace(-fov_deg / 2, fov_deg / 2, n_rays)
angles_rad = np.radians(angles)

def rotate(v, angle_rad):
    rot = np.array([
        [np.cos(angle_rad), -np.sin(angle_rad)],
        [np.sin(angle_rad),  np.cos(angle_rad)]
    ])
    return rot @ v

# Проход по лучам
visible_points = []
for angle in angles_rad:
    ray_dir = rotate(direction, angle)
    ray = np.linspace(pos, pos + ray_dir * max_range, int(max_range / 0.1))

    for p in ray:
        idxs = kdtree.query_ball_point(p, r=tolerance)
        if idxs:
            # находим ближайшую точку на луче, фиксируем как "попавшую в lidar"
            closest_idx = idxs[np.argmin(np.linalg.norm(map_points[idxs] - pos, axis=1))]
            visible_points.append(map_points[closest_idx])
            break  # прекращаем сканирование по лучу (первое попадание)
            
visible_points = np.array(visible_points).reshape(-1, 2)

# --- Визуализация ---
fig, axs = plt.subplots(1, 2, figsize=(14, 6))

axs[0].set_xlim(0, 100)
axs[0].set_ylim(0, 100)

axs[1].set_xlim(-50, 50)
axs[1].set_ylim(0, 100)

# --- График 1: карта + траектория + лучи ---
axs[0].scatter(map_points[:, 0], map_points[:, 1], s=1, label='Карта')
axs[0].plot(trajectory[:, 0], trajectory[:, 1], 'g-', label='Траектория')
axs[0].plot(pos[0], pos[1], 'ro', label=f'Робот (i={i})')

# Рисуем все лучи
for angle in angles_rad:
    ray_dir = rotate(direction, angle)
    end = pos + ray_dir * max_range
    axs[0].plot([pos[0], end[0]], [pos[1], end[1]], 'r-', alpha=0.1)

axs[0].legend()
axs[0].set_title("Карта, траектория и лучи лидара")

# Приводим точки к формату "от лица робота"
centered_points = visible_points - pos
angle_to_y = np.arctan2(direction[0], direction[1])  # угол между direction и [0, 1]
rotation_matrix = np.array([
    [np.cos(angle_to_y), -np.sin(angle_to_y)],
    [np.sin(angle_to_y),  np.cos(angle_to_y)]
])

# Поворачиваем все точки, видимые лидаром
rotated_points = (rotation_matrix @ centered_points.T).T
np.save(f'lidar_frame_i{i}.npy', rotated_points)
print(f"Сохранено {rotated_points.shape[0]} точек в 'lidar_frame_i{i}.npy'")

# --- График 2: только видимые точки ---
if rotated_points.size > 0:
    axs[1].scatter(rotated_points[:, 0], rotated_points[:, 1], c='orange', s=5)
else:
    axs[1].text(0.5, 0.5, 'Нет пересечений с картой', ha='center', va='center', transform=axs[1].transAxes)
axs[1].set_title("Точки, задетектированные lidar-ом")

plt.tight_layout()
plt.show()
