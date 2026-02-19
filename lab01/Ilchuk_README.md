### Отчёт по лабораторной: Моделирование полёта тела в атмосфере


**Задание:**  
Реализовать приложение для моделирования полёта тела в атмосфере.  
Предусмотреть возможность ввода шага моделирования и вывода результатов.
Выполнить моделирование **без очистки предыдущих результатов** для различных шагов моделирования, сравнить траектории и заполнить таблицу.
Сделать выводы.


---

Код программы:
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ProjectileModel:

    def __init__(self, mass, area, drag_coeff=0.15, air_density=1.29, gravity=9.81):
        self.mass = mass
        self.area = area
        self.drag_coeff = drag_coeff
        self.air_density = air_density
        self.gravity = gravity

        
        self.drag_constant = 0.5 * drag_coeff * air_density * area / mass 

    def calculate_derivatives(self, state):
        x, y, velocity_x, velocity_y = state

        speed = np.sqrt(velocity_x**2+velocity_y**2)

        acceleration_x = -self.drag_constant * velocity_x * speed
        acceleration_y = -self.gravity - self.drag_constant * velocity_y * speed

        return np.array([
            velocity_x,
            velocity_y,
            acceleration_x,
            acceleration_y
        ])

    def runge_kutta_step(self, state, time_step):
        k1 = self.calculate_derivatives(state)
        k2 = self.calculate_derivatives(state + time_step * k1 / 2)
        k3 = self.calculate_derivatives(state + time_step * k2 / 2)
        k4 = self.calculate_derivatives(state + time_step * k3)

        return state + time_step * (k1 + 2*k2 + 2*k3 + k4) / 6

    def simulate_motion(self, initial_speed, launch_angle_deg, time_step):

        launch_angle_rad = np.deg2rad(launch_angle_deg)

        state = np.array([
            0.0,
            0.0,
            initial_speed * np.cos(launch_angle_rad),
            initial_speed * np.sin(launch_angle_rad)
        ])

        x_values = []
        y_values = []
        maximum_height = 0

        while state[1] >= 0:
            x_values.append(state[0])
            y_values.append(state[1])
            maximum_height = max(maximum_height, state[1])
            state = self.runge_kutta_step(state, time_step)

        final_speed = np.sqrt(state[2]**2+state[3]**2)

        return {
            "x": np.array(x_values),
            "y": np.array(y_values),
            "range": state[0],
            "max_height": maximum_height,
            "final_speed": final_speed
        }

class FlightGUI:

    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Моделирование движения в атмосфере")
        self.root.geometry("1150x750")
        self.create_interface()

    def create_interface(self):

        left_panel = ttk.Frame(self.root, padding=10)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(left_panel, text="Начальная скорость (м/с)").pack()
        self.speed_input = ttk.Entry(left_panel)
        self.speed_input.insert(0, "20")
        self.speed_input.pack()

        ttk.Label(left_panel, text="Угол запуска (градусы)").pack()
        self.angle_input = ttk.Entry(left_panel)
        self.angle_input.insert(0, "50")
        self.angle_input.pack()

        ttk.Label(left_panel, text="Шаг времени dt").pack()
        self.time_step_input = ttk.Entry(left_panel)
        self.time_step_input.insert(0, "0.01")
        self.time_step_input.pack()

        ttk.Label(left_panel, text="Масса (кг)").pack()
        self.mass_input = ttk.Entry(left_panel)
        self.mass_input.insert(0, "1")
        self.mass_input.pack()

        ttk.Label(left_panel, text="Площадь (м²)").pack()
        self.area_input = ttk.Entry(left_panel)
        self.area_input.insert(0, "0.01")
        self.area_input.pack()

        ttk.Button(left_panel, text="Смоделировать",
                   command=self.run_single_simulation).pack(pady=8)

        ttk.Button(left_panel, text="Авто-запуск (разные dt)",
                   command=self.run_multiple_simulations).pack()

        ttk.Button(left_panel, text="Очистить",
                   command=self.clear_graph).pack(pady=5)

        self.results_table = ttk.Treeview(
            left_panel,
            columns=("dt", "range", "height", "velocity"),
            show="headings",
            height=8
        )

        self.results_table.heading("dt", text="dt")
        self.results_table.heading("range", text="Дальность")
        self.results_table.heading("height", text="Макс. высота")
        self.results_table.heading("velocity", text="Скорость при падении")

        self.results_table.pack(pady=10)

        self.figure, self.axis = plt.subplots(figsize=(7, 6))
        self.axis.set_xlabel("Дальность (м)")
        self.axis.set_ylabel("Высота (м)")
        self.axis.set_title("Траектории движения")
        self.axis.grid(True)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def read_input_parameters(self):
        initial_speed = float(self.speed_input.get())
        launch_angle = float(self.angle_input.get())
        time_step = float(self.time_step_input.get())
        mass = float(self.mass_input.get())
        area = float(self.area_input.get())

        return initial_speed, launch_angle, time_step, mass, area

    def run_single_simulation(self):
        try:
            initial_speed, launch_angle, time_step, mass, area = self.read_input_parameters()

            model = ProjectileModel(mass, area)
            result = model.simulate_motion(initial_speed, launch_angle, time_step)

            self.axis.plot(result["x"], result["y"], linewidth=2)
            self.canvas.draw()

            self.results_table.insert("", tk.END, values=(
                time_step,
                round(result["range"], 2),
                round(result["max_height"], 2),
                round(result["final_speed"], 2)
            ))

        except:
            messagebox.showerror("Ошибка", "Проверьте корректность введённых данных")

    def run_multiple_simulations(self):
        try:
            initial_speed, launch_angle, _, mass, area = self.read_input_parameters()

            time_steps = [1, 0.1, 0.01, 0.001, 0.0001]
            colors = plt.cm.viridis(np.linspace(0, 1, len(time_steps)))

            for i, time_step in enumerate(time_steps):
                model = ProjectileModel(mass, area)
                result = model.simulate_motion(initial_speed, launch_angle, time_step)

                self.axis.plot(result["x"], result["y"],
                               color=colors[i], linewidth=2)

                self.results_table.insert("", tk.END, values=(
                    time_step,
                    round(result["range"], 2),
                    round(result["max_height"], 2),
                    round(result["final_speed"], 2)
                ))

            self.axis.legend([f"dt = {step}" for step in time_steps])
            self.canvas.draw()

        except:
            messagebox.showerror("Ошибка", "Проверьте корректность введённых данных")

    def clear_graph(self):
        self.axis.clear()
        self.axis.set_xlabel("Дальность (м)")
        self.axis.set_ylabel("Высота (м)")
        self.axis.set_title("Траектории движения")
        self.axis.grid(True)
        self.canvas.draw()

        for row in self.results_table.get_children():
            self.results_table.delete(row)
if __name__ == "__main__":
    root = tk.Tk()
    app = FlightGUI(root)
    root.mainloop()


---
Пример с траекториями
<img width="1150" height="780" alt="image" src="https://github.com/user-attachments/assets/2e4344c1-fa56-4266-8cd9-1a9b29233b54" />

---
|Шаг моделирования, с|1|0.1|0.01|0.001|0.0001|
|-|-|-|-|-|-|
| Дальность полёта, м | 49.91 | 38.95 | 38.95 | 38.92 | 38.91 |
| Максимальная высота, м | 10.73 | 11.75 | 11.76 | 11.76 | 11.76 |
| Скорость в конечной точке, м/с | 26.43 | 19.46 | 19.46 | 19.44 | 19.44 |


---

Вывод:

В ходе лабораторной работы проведено моделирование движения тела в атмосфере с учётом сопротивления воздуха и гравитации. Можно заметить большую разницу в дальности между первым и вторым шагом, можем сделать вывод о том, что слишком большой шаг дает заметные численные ошибки.
С уменьшением шага, результаты становятся точнее, однако разница между последующими шагами незначительна. Резюмируя, шаг моделирования однозначно влияет на точность вычислений.
