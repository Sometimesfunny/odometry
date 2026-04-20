import matplotlib.pyplot as plt
import numpy as np


class InteractiveMapDrawer:
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, 100)
        self.ax.set_xscale("linear")
        self.ax.set_yscale("linear")

        self.current_color = "blue"
        map = np.load("map.npy")
        trajectory = np.load("trajectory.npy")
        self.points_by_color = {
            "blue": {"xs": list(map[:, 0]), "ys": list(map[:, 1])},
            "green": {"xs": list(trajectory[:, 0]), "ys": list(trajectory[:, 1])}
        }

        self.lines = {
            "blue": self.ax.plot(map[:, 0], map[:, 1], marker='o', linestyle='-', markersize=2, color='blue')[0],
            "green": self.ax.plot(trajectory[:, 0], trajectory[:, 1], marker='o', linestyle='-', markersize=2, color='green')[0],
        }

        self.drawing = False
        self.draw_enabled = False
        self.min_distance = 0.05

        self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)

        self.update_status()
        plt.show()

    def on_press(self, event):
        if self.draw_enabled and event.inaxes is not None:
            self.drawing = True
            self.add_point(event.xdata, event.ydata)

    def on_motion(self, event):
        if self.draw_enabled and self.drawing and event.inaxes is not None:
            self.add_point(event.xdata, event.ydata)

    def on_release(self, event):
        self.drawing = False

    def on_key_press(self, event):
        key = event.key.lower()
        if key == 'l':
            self.save_current_points()
        elif key == 'd':
            self.draw_enabled = not self.draw_enabled
            print(f"[i] Режим рисования: {'включен' if self.draw_enabled else 'выключен'}")
            self.update_status()
        elif key == '+':
            self.min_distance *= 1.2
            print(f"[i] min_distance увеличено до {self.min_distance:.4f}")
            self.update_status()
        elif key == '-':
            self.min_distance = max(self.min_distance / 1.2, 0.001)
            print(f"[i] min_distance уменьшено до {self.min_distance:.4f}")
            self.update_status()
        elif key == 'j':
            self.toggle_color()

    def toggle_color(self):
        self.current_color = 'green' if self.current_color == 'blue' else 'blue'
        print(f"[i] Переключение цвета: теперь рисуем {self.current_color}")
        self.update_status()

    def save_current_points(self):
        xs = self.points_by_color[self.current_color]["xs"]
        ys = self.points_by_color[self.current_color]["ys"]
        if xs and ys:
            points = np.column_stack((xs, ys))
            filename = f"points_{self.current_color}.npy"
            np.save(filename, points)
            print(f"[+] Сохранено {len(points)} точек в '{filename}'")
        else:
            print(f"[!] Нет точек для сохранения в цвете {self.current_color}")

    def add_point(self, x, y):
        color_data = self.points_by_color[self.current_color]
        xs, ys = color_data["xs"], color_data["ys"]

        if not xs:
            xs.append(x)
            ys.append(y)
            self.update_line()
        else:
            dx = x - xs[-1]
            dy = y - ys[-1]
            dist = (dx**2 + dy**2)**0.5
            if dist >= self.min_distance:
                xs.append(x)
                ys.append(y)
                self.update_line()

    def update_line(self):
        for color in self.points_by_color:
            xs = self.points_by_color[color]["xs"]
            ys = self.points_by_color[color]["ys"]
            self.lines[color].set_data(xs, ys)
        self.fig.canvas.draw_idle()

    def update_status(self):
        self.ax.set_title(
            f"Цвет: {self.current_color.upper()} | Рисование: {'ON' if self.draw_enabled else 'OFF'} "
            f"| min_dist: {self.min_distance:.3f} | D - рисовать, J - цвет, L - сохранить, +/- - шаг"
        )
        self.fig.canvas.draw_idle()

if __name__ == '__main__':
    drawer = InteractiveMapDrawer()
