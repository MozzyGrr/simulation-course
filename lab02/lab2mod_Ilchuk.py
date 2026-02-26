import numpy as np
import tkinter as tk
from tkinter import ttk
from numba import njit
import time

@njit
def heat_solver(left_temp, right_temp, length, dx, total_time, dt):
    #Железо
    density = 7800.0
    heat_capacity = 460.0
    conductivity = 46.0

    nodes = int(length / dx)
    steps = int(total_time / dt)

    temperature = np.zeros(nodes + 1)
    temperature[0] = left_temp
    temperature[-1] = right_temp

    a_coef = conductivity / dx**2
    b_coef = 2 * conductivity / dx**2 + density * heat_capacity / dt
    c_coef = conductivity / dx**2

    forward_alpha = np.zeros(nodes + 1)
    forward_beta = np.zeros(nodes + 1)

    for i in range(steps):

        forward_alpha[0] = 0.0
        forward_beta[0] = left_temp

       
        for k in range(1, nodes):
            rhs = -(density * heat_capacity / dt) * temperature[k]

            denom = b_coef - c_coef * forward_alpha[k - 1]

            forward_alpha[k] = a_coef / denom
            forward_beta[k] = (c_coef * forward_beta[k - 1] - rhs) / denom

        new_temperature = np.zeros(nodes + 1)
        new_temperature[-1] = right_temp

        
        for k in range(nodes - 1, 0, -1):
            new_temperature[k] = (
                forward_alpha[k] * new_temperature[k + 1]
                + forward_beta[k]
            )

        temperature = new_temperature

    midpoint = nodes // 2
    return temperature[midpoint]

class HeatGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Неявная схема теплопроводности")

        self.dt_list = [0.1, 0.01, 0.001, 0.0001]
        self.dx_list = [0.1, 0.01, 0.001, 0.0001]

        self.L = 0.4
        self.Tl = 0.0
        self.Tr = 200.0
        self.model_time = 600.0

        self.build_interface()

    def build_interface(self):

        run_button = tk.Button(
            self.root,
            text="Запустить моделирование",
            command=self.run_calculations
        )
        run_button.pack(pady=10)

        columns = ["dt \\ dx"] + [str(dx) for dx in self.dx_list]

        self.table_temp = ttk.Treeview(
            self.root,
            columns=columns,
            show="headings",
            height=6
        )

        for col in columns:
            self.table_temp.heading(col, text=col)
            self.table_temp.column(col, width=100, anchor="center")

        tk.Label(self.root, text="Температура в центре через 600 с").pack()
        self.table_temp.pack(pady=5)

        self.table_time = ttk.Treeview(
            self.root,
            columns=columns,
            show="headings",
            height=6
        )

        for col in columns:
            self.table_time.heading(col, text=col)
            self.table_time.column(col, width=100, anchor="center")

        tk.Label(self.root, text="Время вычисления (с)").pack()
        self.table_time.pack(pady=5)

    def run_calculations(self):

        for row in self.table_temp.get_children():
            self.table_temp.delete(row)

        for row in self.table_time.get_children():
            self.table_time.delete(row)

        for dt in self.dt_list:

            row_temp = [str(dt)]
            row_time = [str(dt)]

            for dx in self.dx_list:

                start = time.time()

                center_temp = heat_solver(
                    self.Tl,
                    self.Tr,
                    self.L,
                    dx,
                    self.model_time,
                    dt
                )

                elapsed = time.time() - start

                row_temp.append(f"{center_temp:.2f}")
                row_time.append(f"{elapsed:.4f}")

            self.table_temp.insert("", "end", values=row_temp)
            self.table_time.insert("", "end", values=row_time)
            
if __name__ == "__main__":
    root = tk.Tk()
    app = HeatGUI(root)
    root.mainloop()
