import numpy as np
from scipy.spatial import cKDTree
import matplotlib.pyplot as plt


def best_fit_transform(A, B):
    centroid_A = np.mean(A, axis=0)
    centroid_B = np.mean(B, axis=0)
    
    AA = A - centroid_A
    BB = B - centroid_B

    H = AA.T @ BB
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T

    if np.linalg.det(R) < 0:
        Vt[1, :] *= -1
        R = Vt.T @ U.T

    t = centroid_B - R @ centroid_A
    return R, t

def icp(partial, full, init_pose=None, max_iterations=50, tolerance=1e-6):
    src = np.copy(partial)
    dst = np.copy(full)
    
    if init_pose is not None:
        R_init, t_init = init_pose
        src = (R_init @ src.T).T + t_init

    R_total = np.eye(2)
    t_total = np.zeros((2,))
    
    prev_error = float('inf')
    errors = []

    for i in range(max_iterations):
        tree = cKDTree(dst)
        distances, indices = tree.query(src)
        dst_corr = dst[indices]

        R, t = best_fit_transform(src, dst_corr)
        src = (R @ src.T).T + t

        R_total = R @ R_total
        t_total = R @ t_total + t

        mean_error = np.mean(distances)
        errors.append(mean_error)

        if abs(prev_error - mean_error) < tolerance:
            print(f'Сходимость достигнута на итерации {i+1}')
            break
        prev_error = mean_error

    return R_total, t_total, errors

def huber_loss(distances, delta=1.0):
    return np.mean(np.where(np.abs(distances) <= delta,
                            0.5 * distances**2,
                            delta * (np.abs(distances) - 0.5 * delta)))

def icp_with_visualization(partial, full, init_pose=None, max_iterations=100, tolerance=1e-6):
    src_original = np.copy(partial)
    dst = np.copy(full)

    R_total = np.eye(2)
    t_total = np.zeros((2,))

    if init_pose is not None:
        R_init, t_init = init_pose
        R_total = R_init @ R_total
        t_total = R_init @ t_total + t_init

    errors = []
    prev_error = float('inf')

    plt.figure(figsize=(8, 6))

    for i in range(max_iterations):
        src_transformed = (R_total @ src_original.T).T + t_total

        tree = cKDTree(dst)
        distances, indices = tree.query(src_transformed)
        dst_corr = dst[indices]

        R_delta, t_delta = best_fit_transform(src_transformed, dst_corr)

        R_total = R_delta @ R_total
        t_total = R_delta @ t_total + t_delta

        keep_ratio = 0.8
        trimmed_distances = np.sort(distances)[:int(len(distances) * keep_ratio)]
        mean_error = np.mean(trimmed_distances)
        # mean_error = huber_loss(distances, delta=1.0)
        errors.append(mean_error)

        # --- Визуализация ---
        src_vis = (R_total @ src_original.T).T + t_total
        plt.clf()
        plt.scatter(full[:, 0], full[:, 1], c='lightgray', s=10, label='Полная карта')
        plt.scatter(src_vis[:, 0], src_vis[:, 1], c='blue', s=10, label=f'Частичная карта (итерация {i+1})')
        plt.scatter(t_total[0], t_total[1], c='red', marker='x', s=100, label='Текущая позиция')
        plt.title(f'ICP: итерация {i + 1}, ошибка = {mean_error:.4f}')
        plt.axis('equal')
        plt.grid(True)
        plt.legend()
        # plt.pause(5)

        if abs(prev_error - mean_error) < tolerance:
            print(f'Сходимость достигнута на итерации {i+1}')
            break
        prev_error = mean_error

    plt.show()
    return R_total, t_total, errors

def run_multi_icp(partial, full, num_trials=10):
    best_error = float('inf')
    best_R = None
    best_t = None
    for _ in range(num_trials):
        angle = np.random.uniform(-np.pi, np.pi)
        trans = np.random.uniform(-10, 10, size=2)
        R = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
        t = trans
        R_try, t_try, errors = icp_with_visualization(partial, full, init_pose=(R, t))
        if errors[-1] < best_error:
            best_error = errors[-1]
            best_R = R_try
            best_t = t_try
    return best_R, best_t


# Пример использования:
if __name__ == "__main__":
    # Загрузка данных из файлов .npy
    full_map = np.load("map.npy")       # полный набор точек
    partial_map = np.load("lidar_frame_i100.npy")   # частичная карта
    
    theta = np.deg2rad(0)
    R_init = np.array([
        [np.cos(theta), -np.sin(theta)],
        [np.sin(theta),  np.cos(theta)]
    ])
    t_init = np.array([15.0, 50.0])
    # Запустим алгоритм ICP
    R_opt, t_opt, _ = icp_with_visualization(partial_map, full_map, init_pose=(R_init, t_init))
    
    print("Оптимальная матрица поворота R:")
    print(R_opt)
    print("\nОптимальный вектор переноса t:")
    print(t_opt)
    
    # Вектор t_opt и есть искомое смещение - позиция (x, y) места, откуда получена частичная карта.

    # Преобразуем частичную карту в глобальные координаты
    aligned_partial = (R_opt @ partial_map.T).T + t_opt

    # Визуализация результата
    plt.figure(figsize=(10, 8))
    plt.scatter(full_map[:, 0], full_map[:, 1], c='lightgray', label='Полная карта', s=10)
    plt.scatter(aligned_partial[:, 0], aligned_partial[:, 1], c='blue', label='Выравненная частичная карта', s=10)
    plt.scatter(t_opt[0], t_opt[1], c='red', marker='x', s=100, label='Оценка позиции сенсора')
    plt.title("Регистрация карты и оценка позиции")
    plt.legend()
    plt.axis('equal')
    plt.grid(True)
    plt.show()
