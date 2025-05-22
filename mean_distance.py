import numpy as np
from scipy.spatial import KDTree

# Загрузка карты
map_points = np.load('points_blue.npy')  # форма (n, 2)

# Строим KD-дерево
kdtree = KDTree(map_points)

# Ищем ближайшего соседа для каждой точки (k=2, потому что первая — сама точка)
dists, _ = kdtree.query(map_points, k=2)

# Берем вторую колонку — это расстояния до ближайших СТОРОННИХ точек
nearest_neighbor_dists = dists[:, 1]

# Средняя дистанция
avg_distance = np.mean(nearest_neighbor_dists)
print(f"Средняя дистанция между ближайшими точками на карте: {avg_distance:.3f}")
